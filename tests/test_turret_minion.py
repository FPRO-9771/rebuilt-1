"""
Tests for turret Minion subsystem.
Mirrors test_turret.py but exercises the TalonFXS / Minion variant.
"""

from subsystems.turret_minion import TurretMinion
from tests.conftest import TEST_CON_TURRET_MINION

# Midpoint of soft limits -- always safe regardless of constant tuning
_MID_POS = (TEST_CON_TURRET_MINION["min_position"] + TEST_CON_TURRET_MINION["max_position"]) / 2


def test_turret_minion_voltage_clamping():
    """Verify voltage is clamped to max."""
    turret = TurretMinion()
    turret.motor.simulate_position(_MID_POS)

    turret._set_voltage(100)
    assert turret.motor.get_last_voltage() == TEST_CON_TURRET_MINION["max_voltage"]

    turret._set_voltage(-100)
    assert turret.motor.get_last_voltage() == -TEST_CON_TURRET_MINION["max_voltage"]


def test_turret_minion_soft_limit_blocks_at_max():
    """Verify positive voltage is blocked when at max position."""
    turret = TurretMinion()
    max_v = TEST_CON_TURRET_MINION["max_voltage"]
    half_v = max_v * 0.5

    turret.motor.simulate_position(TEST_CON_TURRET_MINION["max_position"])
    turret._set_voltage(half_v)
    assert turret.motor.get_last_voltage() == 0

    # Allow return (negative voltage when at max)
    turret._set_voltage(-half_v)
    assert turret.motor.get_last_voltage() == -half_v


def test_turret_minion_soft_limit_blocks_at_min():
    """Verify negative voltage is blocked when at min position."""
    turret = TurretMinion()
    max_v = TEST_CON_TURRET_MINION["max_voltage"]
    half_v = max_v * 0.5

    turret.motor.simulate_position(TEST_CON_TURRET_MINION["min_position"])
    turret._set_voltage(-half_v)
    assert turret.motor.get_last_voltage() == 0

    # Allow return (positive voltage when at min)
    turret._set_voltage(half_v)
    assert turret.motor.get_last_voltage() == half_v


def test_turret_minion_is_at_position():
    """Verify is_at_position with tolerance."""
    turret = TurretMinion()
    tol = TEST_CON_TURRET_MINION["position_tolerance"]

    turret.motor.simulate_position(_MID_POS)
    assert turret.is_at_position(_MID_POS) is True

    # Clearly within tolerance
    turret.motor.simulate_position(_MID_POS + tol * 0.5)
    assert turret.is_at_position(_MID_POS) is True

    # Clearly outside tolerance
    turret.motor.simulate_position(_MID_POS + tol * 2)
    assert turret.is_at_position(_MID_POS) is False


def test_turret_minion_manual_command_scales_input():
    """Verify manual command scales joystick to voltage."""
    turret = TurretMinion()
    turret.motor.simulate_position(_MID_POS)

    cmd = turret.manual(lambda: 0.5)
    cmd.initialize()
    cmd.execute()

    exp = TEST_CON_TURRET_MINION["manual_exponent"]
    expected_voltage = (
        abs(0.5) ** exp * TEST_CON_TURRET_MINION["max_voltage"] * TEST_CON_TURRET_MINION["manual_speed_factor"]
    )
    assert turret.motor.get_last_voltage() == expected_voltage


def test_turret_minion_manual_command_stops_on_end():
    """Verify manual command stops motor when ended."""
    turret = TurretMinion()
    turret.motor.simulate_position(_MID_POS)

    cmd = turret.manual(lambda: 1.0)
    cmd.initialize()
    cmd.execute()
    assert turret.motor.get_last_voltage() != 0

    cmd.end(False)
    assert turret.motor.get_last_voltage() == 0


def test_turret_minion_is_within_limits():
    """Verify is_within_limits check."""
    turret = TurretMinion()

    turret.motor.simulate_position(_MID_POS)
    assert turret.is_within_limits() is True

    turret.motor.simulate_position(TEST_CON_TURRET_MINION["max_position"])
    assert turret.is_within_limits() is True

    turret.motor.simulate_position(TEST_CON_TURRET_MINION["max_position"] + 1.0)
    assert turret.is_within_limits() is False


def test_turret_minion_soft_limit_ramps_voltage():
    """Verify voltage ramps down near soft limits instead of hard-cutting."""
    turret = TurretMinion()
    max_v = TEST_CON_TURRET_MINION["max_voltage"]
    max_pos = TEST_CON_TURRET_MINION["max_position"]
    min_pos = TEST_CON_TURRET_MINION["min_position"]
    ramp = TEST_CON_TURRET_MINION["soft_limit_ramp"]

    # Halfway into the ramp zone near max -- voltage should be ~50% of requested
    pos_in_ramp = max_pos - ramp * 0.5
    turret.motor.simulate_position(pos_in_ramp)
    turret._set_voltage(max_v)
    ramped = turret.motor.get_last_voltage()
    assert 0 < ramped < max_v

    # Halfway into the ramp zone near min -- negative voltage should ramp
    pos_in_ramp_min = min_pos + ramp * 0.5
    turret.motor.simulate_position(pos_in_ramp_min)
    turret._set_voltage(-max_v)
    ramped_min = turret.motor.get_last_voltage()
    assert -max_v < ramped_min < 0

    # At midpoint -- no ramping, full voltage passes through
    turret.motor.simulate_position(_MID_POS)
    turret._set_voltage(max_v)
    assert turret.motor.get_last_voltage() == max_v
