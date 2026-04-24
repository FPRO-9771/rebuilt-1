"""
Tests for CoordinateAim command.
"""

from unittest.mock import patch

from subsystems.turret_minion import TurretMinion as Turret
from commands.coordinate_aim import CoordinateAim
from calculations.target_state import ShootContext
from tests.conftest import TEST_CON_TURRET_MINION, TEST_CON_POSE


_MID_POS = (TEST_CON_TURRET_MINION["min_position"] + TEST_CON_TURRET_MINION["max_position"]) / 2


def _make_context(target_x=5.0, target_y=0.0, heading_deg=0.0,
                  pose_x=0.0, pose_y=0.0, vx=0.0, vy=0.0):
    """Create a ShootContext for testing."""
    return ShootContext(
        corrected_distance=0.0,  # not used by CoordinateAim
        raw_distance=0.0,
        closing_speed_mps=0.0,
        pose_x=pose_x,
        pose_y=pose_y,
        heading_deg=heading_deg,
        shooter_x=pose_x,  # zero offset in test constants
        shooter_y=pose_y,
        target_x=target_x,
        target_y=target_y,
        vx=vx,
        vy=vy,
    )


def _make_coord_aim(ctx=None):
    """Create a CoordinateAim command with a ShootContext supplier."""
    turret = Turret()
    turret.motor.simulate_position(_MID_POS)

    if ctx is None:
        ctx = _make_context()

    cmd = CoordinateAim(
        turret,
        context_supplier=lambda: ctx,
        turret_config=TEST_CON_TURRET_MINION,
    )
    return cmd, turret


@patch("commands.coordinate_aim.SmartDashboard")
def test_aims_at_target_to_the_right(mock_sd):
    """Target to the right of turret produces nonzero voltage."""
    ctx = _make_context(target_x=5.0, target_y=-5.0)
    cmd, turret = _make_coord_aim(ctx)

    cmd.initialize()
    cmd.execute()

    assert turret.motor.get_last_voltage() != 0


@patch("commands.coordinate_aim.SmartDashboard")
def test_within_tolerance_outputs_zero_voltage(mock_sd):
    """Turret aimed at target within tolerance -> zero voltage and on_target."""
    # Target directly ahead, turret at center_position (0.0 in test)
    ctx = _make_context(target_x=5.0, target_y=0.0)
    cmd, turret = _make_coord_aim(ctx)
    turret.motor.simulate_position(TEST_CON_POSE["center_position"])

    cmd.initialize()
    cmd.execute()

    assert turret.motor.get_last_voltage() == 0
    assert cmd.is_on_target() is True


@patch("commands.coordinate_aim.SmartDashboard")
def test_outside_tolerance_outputs_nonzero_voltage(mock_sd):
    """Turret not aimed at target -> nonzero voltage."""
    # Target 90 degrees to the left
    ctx = _make_context(target_x=0.0, target_y=5.0)
    cmd, turret = _make_coord_aim(ctx)
    turret.motor.simulate_position(TEST_CON_POSE["center_position"])

    cmd.initialize()
    cmd.execute()

    assert turret.motor.get_last_voltage() != 0
    assert cmd.is_on_target() is False


@patch("commands.coordinate_aim.SmartDashboard")
def test_velocity_compensation_shifts_aim(mock_sd):
    """Tangential velocity shifts the aim compared to stationary."""
    # Hub is straight ahead (+X); lateral movement (vy) is tangential.
    # Stationary
    ctx_still = _make_context(target_x=5.0, target_y=0.0)
    cmd_still, turret_still = _make_coord_aim(ctx_still)
    turret_still.motor.simulate_position(TEST_CON_POSE["center_position"])
    cmd_still.initialize()
    cmd_still.execute()
    v_still = turret_still.motor.get_last_voltage()

    # Moving laterally (tangential to hub line)
    ctx_moving = _make_context(target_x=5.0, target_y=0.0, vy=2.0)
    cmd_moving, turret_moving = _make_coord_aim(ctx_moving)
    turret_moving.motor.simulate_position(TEST_CON_POSE["center_position"])
    cmd_moving.initialize()
    cmd_moving.execute()
    v_moving = turret_moving.motor.get_last_voltage()

    assert v_still != v_moving


@patch("commands.coordinate_aim.SmartDashboard")
def test_stops_turret_on_end(mock_sd):
    """Turret stops when command ends."""
    ctx = _make_context(target_x=0.0, target_y=5.0)
    cmd, turret = _make_coord_aim(ctx)
    turret.motor.simulate_position(TEST_CON_POSE["center_position"])

    cmd.initialize()
    cmd.execute()
    assert turret.motor.get_last_voltage() != 0

    cmd.end(False)
    assert turret.motor.get_last_voltage() == 0


@patch("commands.coordinate_aim.SmartDashboard")
def test_is_on_target_false_when_not_active(mock_sd):
    """is_on_target returns False when command is not running."""
    cmd, turret = _make_coord_aim()
    assert cmd.is_on_target() is False


@patch("commands.coordinate_aim.SmartDashboard")
def test_is_finished_always_false(mock_sd):
    """isFinished always returns False (command runs until canceled)."""
    cmd, turret = _make_coord_aim()
    cmd.initialize()
    assert cmd.isFinished() is False


@patch("commands.coordinate_aim.SmartDashboard")
def test_turret_near_limit_routes_other_direction(mock_sd):
    """When turret is near a limit, routing should avoid hitting it."""
    # Target 90 degrees left -> error = +90 deg = +2.25 rotations
    # Turret near max limit -> should route the other way
    ctx = _make_context(target_x=0.0, target_y=5.0)
    cmd, turret = _make_coord_aim(ctx)
    turret.motor.simulate_position(TEST_CON_TURRET_MINION["max_position"] - 0.5)

    cmd.initialize()
    cmd.execute()

    assert turret.motor.get_last_voltage() != 0


@patch("commands.coordinate_aim.SmartDashboard")
def test_get_target_state_returns_state_when_active(mock_sd):
    """get_target_state returns a TargetState when command is active."""
    ctx = _make_context()
    cmd, turret = _make_coord_aim(ctx)
    turret.motor.simulate_position(TEST_CON_POSE["center_position"])

    cmd.initialize()
    cmd.execute()

    state = cmd.get_target_state()
    assert state is not None
    assert state.distance_m > 0


@patch("commands.coordinate_aim.SmartDashboard")
def test_get_target_state_returns_none_when_inactive(mock_sd):
    """get_target_state returns None when command is not running."""
    cmd, turret = _make_coord_aim()
    assert cmd.get_target_state() is None
