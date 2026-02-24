"""
Tests for launcher subsystem.
"""

from subsystems.launcher import Launcher
from tests.conftest import TEST_CON_LAUNCHER


def test_launcher_spin_up_commands_velocity():
    """Verify spin_up sends velocity command."""
    launcher = Launcher()

    cmd = launcher.spin_up(50.0)
    cmd.initialize()
    cmd.execute()

    assert launcher.motor._velocity == 50.0
    assert launcher.motor.command_history[-1]["type"] == "velocity"
    assert launcher.motor.command_history[-1]["value"] == 50.0


def test_launcher_is_at_speed_within_tolerance():
    """Verify is_at_speed with tolerance."""
    launcher = Launcher()
    tol = TEST_CON_LAUNCHER["velocity_tolerance"]

    launcher.motor.simulate_velocity(50.0)
    assert launcher.is_at_speed(50.0) is True

    # Just within tolerance
    launcher.motor.simulate_velocity(50.0 + tol)
    assert launcher.is_at_speed(50.0) is True

    # Clearly outside tolerance
    launcher.motor.simulate_velocity(50.0 + tol * 2)
    assert launcher.is_at_speed(50.0) is False


def test_launcher_spin_up_never_finishes():
    """Verify spin_up command never auto-finishes."""
    launcher = Launcher()

    cmd = launcher.spin_up(50.0)
    cmd.initialize()

    for _ in range(100):
        cmd.execute()
        assert cmd.isFinished() is False


def test_launcher_spin_up_stops_on_end():
    """Verify spin_up stops motor when ended."""
    launcher = Launcher()

    cmd = launcher.spin_up(50.0)
    cmd.initialize()
    cmd.execute()

    cmd.end(False)
    assert launcher.motor.get_last_voltage() == 0


def test_launcher_voltage_clamping():
    """Verify voltage is clamped to max."""
    launcher = Launcher()

    launcher._set_voltage(100)
    assert launcher.motor.get_last_voltage() == TEST_CON_LAUNCHER["max_voltage"]

    launcher._set_voltage(-100)
    assert launcher.motor.get_last_voltage() == -TEST_CON_LAUNCHER["max_voltage"]
