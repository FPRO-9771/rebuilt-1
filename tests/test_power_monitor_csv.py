"""
Tests for the PowerMonitor CSV writer (telemetry/power_csv.py).

Uses tmp_path so files are written to a pytest-managed directory and
cleaned up automatically.
"""

import csv
import pytest

from hardware.mock_motor_controller import MockMotorController
from telemetry.power_monitor import PowerMonitor
from telemetry.power_csv import make_csv_writer


@pytest.fixture(autouse=True)
def _enable_power_monitor(monkeypatch):
    from constants.debug import DEBUG
    monkeypatch.setitem(DEBUG, "power_monitor", True)


def _make_monitor(tmp_path, motors, battery_v=12.5):
    groups = {
        "drivetrain":     [("drive", lambda: motors["drive"].get_supply_current())],
        "intake_arms":    [("arm", lambda: motors["arm"].get_supply_current())],
        "intake_spinner": [("spinner", lambda: motors["spinner"].get_supply_current())],
        "shooting":       [("shooter", lambda: motors["shooter"].get_supply_current())],
    }
    battery = [battery_v]
    writer = make_csv_writer(tmp_path)
    monitor = PowerMonitor(
        groups,
        battery_voltage_supplier=lambda: battery[0],
        csv_writer=writer,
    )
    return monitor, battery


@pytest.fixture
def motors():
    return {
        "drive": MockMotorController(can_id=1),
        "arm": MockMotorController(can_id=2),
        "spinner": MockMotorController(can_id=3),
        "shooter": MockMotorController(can_id=4),
    }


def test_summary_written_with_header_on_first_dump(tmp_path, motors):
    monitor, _ = _make_monitor(tmp_path, motors)
    motors["drive"].simulate_supply_current(100.0)
    monitor.sample("teleop")
    monitor.dump()

    summary = tmp_path / "summary.csv"
    assert summary.exists()
    rows = list(csv.reader(summary.open()))
    assert len(rows) == 2  # header + 1 match
    assert rows[0][0] == "started_at"
    # Columns include per-group per-phase entries.
    assert "drivetrain_teleop_peak_a" in rows[0]
    assert "shooting_auto_peak_a" in rows[0]


def test_summary_appends_without_duplicating_header(tmp_path, motors):
    monitor, _ = _make_monitor(tmp_path, motors)

    motors["drive"].simulate_supply_current(50.0)
    monitor.sample("teleop")
    monitor.dump()

    motors["drive"].simulate_supply_current(80.0)
    monitor.sample("teleop")
    monitor.dump()

    rows = list(csv.reader((tmp_path / "summary.csv").open()))
    assert len(rows) == 3  # header + 2 match rows
    assert rows[0][0] == "started_at"
    assert rows[1][0] != "started_at"
    assert rows[2][0] != "started_at"


def test_time_series_file_has_one_row_per_sample(tmp_path, motors):
    monitor, _ = _make_monitor(tmp_path, motors)

    motors["drive"].simulate_supply_current(60.0)
    motors["shooter"].simulate_supply_current(25.0)
    for _ in range(5):
        monitor.sample("auto")
    for _ in range(7):
        monitor.sample("teleop")

    monitor.dump()

    match_files = list(tmp_path.glob("match_*.csv"))
    assert len(match_files) == 1
    rows = list(csv.reader(match_files[0].open()))
    # 1 header + 5 auto + 7 teleop = 13
    assert len(rows) == 13
    header = rows[0]
    assert header[0] == "t_s"
    assert header[1] == "phase"
    assert header[2] == "battery_v"
    assert "drivetrain_a" in header
    assert "shooting_a" in header

    phase_col = header.index("phase")
    phases = [r[phase_col] for r in rows[1:]]
    assert phases.count("auto") == 5
    assert phases.count("teleop") == 7


def test_peak_current_and_motor_appear_in_summary(tmp_path, motors):
    monitor, _ = _make_monitor(tmp_path, motors, battery_v=12.0)

    # Ramp up drive, spike once, then back down.
    for amps in (50.0, 220.0, 100.0):
        motors["drive"].simulate_supply_current(amps)
        monitor.sample("teleop")
    monitor.dump()

    rows = list(csv.reader((tmp_path / "summary.csv").open()))
    header, data = rows[0], rows[1]
    idx_peak = header.index("drivetrain_teleop_peak_a")
    idx_motor = header.index("drivetrain_teleop_peak_motor")
    assert float(data[idx_peak]) == pytest.approx(220.0, abs=0.1)
    assert data[idx_motor] == "drive"


def test_missing_dir_recovers_without_crashing(tmp_path, motors, monkeypatch):
    """If mkdir fails, dump() should still not raise."""
    bad_dir = tmp_path / "nope"

    # Make mkdir blow up.
    original = bad_dir.__class__.mkdir
    def failing_mkdir(self, *args, **kwargs):
        raise OSError("simulated permission denied")
    monkeypatch.setattr(bad_dir.__class__, "mkdir", failing_mkdir)

    writer = make_csv_writer(bad_dir)
    groups = {
        "drivetrain": [("drive", lambda: motors["drive"].get_supply_current())],
    }
    monitor = PowerMonitor(
        groups,
        battery_voltage_supplier=lambda: 12.0,
        csv_writer=writer,
    )
    motors["drive"].simulate_supply_current(50.0)
    monitor.sample("teleop")
    monitor.dump()  # must not raise

    # Restore for other tests that may use Path.mkdir.
    monkeypatch.setattr(bad_dir.__class__, "mkdir", original)
