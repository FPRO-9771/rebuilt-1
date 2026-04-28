"""
Tests for the PowerMonitor (telemetry/power_monitor.py).

Uses MockMotorController + a fake battery voltage supplier so we can drive
the accumulators deterministically without hardware.
"""

import pytest

from hardware.mock_motor_controller import MockMotorController
from telemetry.power_monitor import PowerMonitor
from telemetry.power_stats import BROWNOUT_THRESHOLD_V


@pytest.fixture(autouse=True)
def _enable_power_monitor(monkeypatch):
    """Default ON for these tests -- individual tests can flip it off."""
    from constants.debug import DEBUG
    monkeypatch.setitem(DEBUG, "power_monitor", True)


@pytest.fixture
def motors():
    """Four mock motors across four groups, one per group."""
    return {
        "drive": MockMotorController(can_id=1),
        "arm": MockMotorController(can_id=2),
        "spinner": MockMotorController(can_id=3),
        "shooter": MockMotorController(can_id=4),
    }


def _make_monitor(motors, battery_v=12.5):
    """Build a PowerMonitor with one motor per group and a constant battery."""
    groups = {
        "drivetrain":     [("drive", lambda: motors["drive"].get_supply_current())],
        "intake_arms":    [("arm", lambda: motors["arm"].get_supply_current())],
        "intake_spinner": [("spinner", lambda: motors["spinner"].get_supply_current())],
        "shooting":       [("shooter", lambda: motors["shooter"].get_supply_current())],
    }
    battery = [battery_v]
    monitor = PowerMonitor(groups, battery_voltage_supplier=lambda: battery[0])
    return monitor, battery


# ---------- toggle ----------

def test_sample_is_noop_when_toggle_off(monkeypatch, motors):
    from constants.debug import DEBUG
    monkeypatch.setitem(DEBUG, "power_monitor", False)
    monitor, _ = _make_monitor(motors)
    motors["drive"].simulate_supply_current(200.0)

    monitor.sample("teleop")

    # No accumulation should have happened.
    stats = monitor._stats["drivetrain"]["teleop"]
    assert stats.samples == 0
    assert stats.peak_amps == 0.0


def test_dump_is_noop_when_no_samples(motors, caplog):
    monitor, _ = _make_monitor(motors)
    monitor.dump()
    # No log lines emitted.
    assert not any("POWER MONITOR" in rec.message for rec in caplog.records)


# ---------- accumulation ----------

def test_peak_and_avg_track_across_samples(motors):
    monitor, _ = _make_monitor(motors, battery_v=12.0)

    motors["drive"].simulate_supply_current(50.0)
    monitor.sample("teleop")

    motors["drive"].simulate_supply_current(250.0)  # peak
    monitor.sample("teleop")

    motors["drive"].simulate_supply_current(100.0)
    monitor.sample("teleop")

    stats = monitor._stats["drivetrain"]["teleop"]
    assert stats.samples == 3
    assert stats.peak_amps == pytest.approx(250.0)
    assert stats.peak_motor == "drive"
    # avg = (50 + 250 + 100) / 3 = 133.33
    assert stats.avg_amps == pytest.approx(400.0 / 3)


def test_wh_integrates_volts_amps_over_time(motors):
    # 10 samples at 100A and 12V == 100 * 12 * 10 * 0.050 s = 600 W*s = 600/3600 Wh
    monitor, _ = _make_monitor(motors, battery_v=12.0)
    motors["drive"].simulate_supply_current(100.0)

    for _ in range(10):
        monitor.sample("teleop")

    stats = monitor._stats["drivetrain"]["teleop"]
    expected_wh = (100.0 * 12.0 * 10 * 0.050) / 3600.0
    assert stats.wh == pytest.approx(expected_wh)


def test_phases_accumulate_independently(motors):
    monitor, _ = _make_monitor(motors)

    motors["drive"].simulate_supply_current(30.0)
    monitor.sample("auto")
    monitor.sample("auto")

    motors["drive"].simulate_supply_current(80.0)
    monitor.sample("teleop")

    auto_stats = monitor._stats["drivetrain"]["auto"]
    tele_stats = monitor._stats["drivetrain"]["teleop"]

    assert auto_stats.samples == 2
    assert auto_stats.peak_amps == pytest.approx(30.0)

    assert tele_stats.samples == 1
    assert tele_stats.peak_amps == pytest.approx(80.0)


def test_unknown_phase_is_ignored(motors):
    monitor, _ = _make_monitor(motors)
    monitor.sample("disabled")  # not in _PHASES
    # No phase state should have accumulated.
    assert all(monitor._battery[p].samples == 0
               for p in monitor._battery)


# ---------- battery tracking ----------

def test_battery_min_and_avg(motors):
    monitor, battery = _make_monitor(motors, battery_v=12.0)
    voltages = [12.5, 12.0, 9.0, 11.0]
    for v in voltages:
        battery[0] = v
        monitor.sample("teleop")

    b = monitor._battery["teleop"]
    assert b.samples == 4
    assert b.min_v == pytest.approx(9.0)
    assert b.avg_v == pytest.approx(sum(voltages) / len(voltages))


def test_brownout_event_counted_and_ended(motors):
    monitor, battery = _make_monitor(motors, battery_v=12.0)

    # Healthy, dip into brownout for 2 samples, recover, dip again.
    series = [12.0, 6.5, 6.0, 12.0, 5.0, 12.0]
    for v in series:
        battery[0] = v
        monitor.sample("teleop")

    b = monitor._battery["teleop"]
    # Two distinct brownout periods: [6.5, 6.0] and [5.0].
    assert b.brownout_events == 2
    # Time below threshold: 3 samples * 0.050s
    assert b.time_below_brownout_s == pytest.approx(3 * 0.050)
    assert b.min_v < BROWNOUT_THRESHOLD_V


# ---------- dump + reset ----------

def test_dump_logs_summary_and_resets(motors, caplog):
    import logging
    caplog.set_level(logging.WARNING, logger="frc.power_monitor")

    monitor, _ = _make_monitor(motors, battery_v=12.0)
    motors["drive"].simulate_supply_current(150.0)
    monitor.sample("teleop")
    monitor.sample("teleop")

    monitor.dump()

    # Header line appears.
    assert any("POWER MONITOR MATCH SUMMARY" in rec.message
               for rec in caplog.records)
    # Drivetrain peak shows up somewhere.
    assert any("drivetrain" in rec.message for rec in caplog.records)

    # Reset: stats zeroed for next match.
    assert monitor._stats["drivetrain"]["teleop"].samples == 0
    assert monitor._battery["teleop"].samples == 0


def test_peak_motor_label_comes_from_hottest_in_group(motors):
    # Override the shooting group with multiple motors so we can verify
    # that peak_motor records the label of the hottest one.
    shooter_a = MockMotorController(can_id=10)
    shooter_b = MockMotorController(can_id=11)
    groups = {
        "shooting": [
            ("launcher", lambda: shooter_a.get_supply_current()),
            ("turret",   lambda: shooter_b.get_supply_current()),
        ],
    }
    monitor = PowerMonitor(groups, battery_voltage_supplier=lambda: 12.0)

    shooter_a.simulate_supply_current(40.0)
    shooter_b.simulate_supply_current(90.0)  # hotter
    monitor.sample("teleop")

    stats = monitor._stats["shooting"]["teleop"]
    assert stats.peak_motor == "turret"
    assert stats.peak_amps == pytest.approx(90.0)
    # Group total sums both motors.
    assert stats.avg_amps == pytest.approx(130.0)


def test_reader_exceptions_do_not_crash_sample(motors):
    """A misbehaving reader should be skipped, not kill the loop."""
    def boom():
        raise RuntimeError("simulated CAN glitch")

    groups = {
        "shooting": [
            ("bad", boom),
            ("good", lambda: 42.0),
        ],
    }
    monitor = PowerMonitor(groups, battery_voltage_supplier=lambda: 12.0)
    monitor.sample("teleop")  # must not raise

    stats = monitor._stats["shooting"]["teleop"]
    # The good motor still contributed.
    assert stats.samples == 1
    assert stats.peak_motor == "good"
    assert stats.peak_amps == pytest.approx(42.0)
