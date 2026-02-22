"""
Tests for turret subsystem.
"""

from subsystems.turret import Turret
from constants import CON_TURRET


def test_turret_voltage_clamping():
    """Verify voltage is clamped to max."""
    turret = Turret()

    turret._set_voltage(100)
    assert turret.motor.get_last_voltage() == CON_TURRET["max_voltage"]

    turret._set_voltage(-100)
    assert turret.motor.get_last_voltage() == -CON_TURRET["max_voltage"]


def test_turret_soft_limit_blocks_at_max():
    """Verify positive voltage is blocked when at max position."""
    turret = Turret()

    turret.motor.simulate_position(CON_TURRET["max_position"])
    turret._set_voltage(2.0)
    assert turret.motor.get_last_voltage() == 0

    # Allow return (negative voltage when at max)
    turret._set_voltage(-2.0)
    assert turret.motor.get_last_voltage() == -2.0


def test_turret_soft_limit_blocks_at_min():
    """Verify negative voltage is blocked when at min position."""
    turret = Turret()

    turret.motor.simulate_position(CON_TURRET["min_position"])
    turret._set_voltage(-2.0)
    assert turret.motor.get_last_voltage() == 0

    # Allow return (positive voltage when at min)
    turret._set_voltage(2.0)
    assert turret.motor.get_last_voltage() == 2.0


def test_turret_is_at_position():
    """Verify is_at_position with tolerance."""
    turret = Turret()

    turret.motor.simulate_position(0.1)
    assert turret.is_at_position(0.1) is True

    # Clearly within tolerance
    tol = CON_TURRET["position_tolerance"]
    turret.motor.simulate_position(0.1 + tol * 0.5)
    assert turret.is_at_position(0.1) is True

    # Clearly outside tolerance
    turret.motor.simulate_position(0.1 + tol + 0.01)
    assert turret.is_at_position(0.1) is False


def test_turret_manual_command_scales_input():
    """Verify manual command scales joystick to voltage."""
    turret = Turret()

    cmd = turret.manual(lambda: 0.5)
    cmd.initialize()
    cmd.execute()

    expected_voltage = 0.5 * CON_TURRET["max_voltage"]
    assert turret.motor.get_last_voltage() == expected_voltage


def test_turret_manual_command_stops_on_end():
    """Verify manual command stops motor when ended."""
    turret = Turret()

    cmd = turret.manual(lambda: 1.0)
    cmd.initialize()
    cmd.execute()
    assert turret.motor.get_last_voltage() != 0

    cmd.end(False)
    assert turret.motor.get_last_voltage() == 0


def test_turret_is_within_limits():
    """Verify is_within_limits check."""
    turret = Turret()

    turret.motor.simulate_position(0.0)
    assert turret.is_within_limits() is True

    turret.motor.simulate_position(CON_TURRET["max_position"])
    assert turret.is_within_limits() is True

    turret.motor.simulate_position(CON_TURRET["max_position"] + 0.1)
    assert turret.is_within_limits() is False
