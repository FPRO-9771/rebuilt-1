"""
Tests for turret subsystem.
"""

from subsystems.turret import Turret
from tests.conftest import TEST_CON_TURRET

# Midpoint of soft limits — always safe regardless of constant tuning
_MID_POS = (TEST_CON_TURRET["min_position"] + TEST_CON_TURRET["max_position"]) / 2


def test_turret_voltage_clamping():
    """Verify voltage is clamped to max."""
    turret = Turret()
    turret.motor.simulate_position(_MID_POS)

    turret._set_voltage(100)
    assert turret.motor.get_last_voltage() == TEST_CON_TURRET["max_voltage"]

    turret._set_voltage(-100)
    assert turret.motor.get_last_voltage() == -TEST_CON_TURRET["max_voltage"]


def test_turret_soft_limit_blocks_at_max():
    """Verify positive voltage is blocked when at max position."""
    turret = Turret()
    max_v = TEST_CON_TURRET["max_voltage"]
    half_v = max_v * 0.5

    turret.motor.simulate_position(TEST_CON_TURRET["max_position"])
    turret._set_voltage(half_v)
    assert turret.motor.get_last_voltage() == 0

    # Allow return (negative voltage when at max)
    turret._set_voltage(-half_v)
    assert turret.motor.get_last_voltage() == -half_v


def test_turret_soft_limit_blocks_at_min():
    """Verify negative voltage is blocked when at min position."""
    turret = Turret()
    max_v = TEST_CON_TURRET["max_voltage"]
    half_v = max_v * 0.5

    turret.motor.simulate_position(TEST_CON_TURRET["min_position"])
    turret._set_voltage(-half_v)
    assert turret.motor.get_last_voltage() == 0

    # Allow return (positive voltage when at min)
    turret._set_voltage(half_v)
    assert turret.motor.get_last_voltage() == half_v


def test_turret_is_at_position():
    """Verify is_at_position with tolerance."""
    turret = Turret()
    tol = TEST_CON_TURRET["position_tolerance"]

    turret.motor.simulate_position(_MID_POS)
    assert turret.is_at_position(_MID_POS) is True

    # Clearly within tolerance
    turret.motor.simulate_position(_MID_POS + tol * 0.5)
    assert turret.is_at_position(_MID_POS) is True

    # Clearly outside tolerance
    turret.motor.simulate_position(_MID_POS + tol * 2)
    assert turret.is_at_position(_MID_POS) is False


def test_turret_manual_command_scales_input():
    """Verify manual command scales joystick to voltage."""
    turret = Turret()
    turret.motor.simulate_position(_MID_POS)

    cmd = turret.manual(lambda: 0.5)
    cmd.initialize()
    cmd.execute()

    expected_voltage = (
        0.5 * TEST_CON_TURRET["max_voltage"] * TEST_CON_TURRET["manual_speed_factor"]
    )
    assert turret.motor.get_last_voltage() == expected_voltage


def test_turret_manual_command_stops_on_end():
    """Verify manual command stops motor when ended."""
    turret = Turret()
    turret.motor.simulate_position(_MID_POS)

    cmd = turret.manual(lambda: 1.0)
    cmd.initialize()
    cmd.execute()
    assert turret.motor.get_last_voltage() != 0

    cmd.end(False)
    assert turret.motor.get_last_voltage() == 0


def test_turret_is_within_limits():
    """Verify is_within_limits check."""
    turret = Turret()

    turret.motor.simulate_position(_MID_POS)
    assert turret.is_within_limits() is True

    turret.motor.simulate_position(TEST_CON_TURRET["max_position"])
    assert turret.is_within_limits() is True

    turret.motor.simulate_position(TEST_CON_TURRET["max_position"] + 1.0)
    assert turret.is_within_limits() is False
