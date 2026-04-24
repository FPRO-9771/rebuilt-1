"""
Tests for ResyncTurret command.

Verifies the in-match turret recalibration: after running ResyncTurret,
a CoordinateAim cycle with the same pose and motor position should see
error_deg ~= 0 -- regardless of how wrong the initial offset was.
"""

from unittest.mock import patch

from wpimath.geometry import Pose2d, Rotation2d

from subsystems.turret_minion import TurretMinion as Turret
from commands.coordinate_aim import CoordinateAim
from commands.resync_turret import ResyncTurret
from calculations.target_state import ShootContext
from tests.conftest import TEST_CON_TURRET_MINION, TEST_CON_POSE


_MID_POS = (TEST_CON_TURRET_MINION["min_position"] + TEST_CON_TURRET_MINION["max_position"]) / 2

# Alliance dict shape used by match_setup.get_alliance
_ALLIANCE = {"target_x": 5.0, "target_y": 0.0}


def _pose_supplier(x=0.0, y=0.0, heading_deg=0.0):
    pose = Pose2d(x, y, Rotation2d.fromDegrees(heading_deg))
    return lambda: pose


def test_resync_zeros_error_for_current_motor_position():
    """After resync, compute_target_state for the current motor position
    should return error_deg ~= 0."""
    turret = Turret()
    # Put the turret at an arbitrary position within limits.
    turret.motor.simulate_position(_MID_POS + 1.0)

    cmd = ResyncTurret(
        turret,
        pose_supplier=_pose_supplier(heading_deg=0.0),
        alliance_supplier=lambda: _ALLIANCE,
    )
    cmd.initialize()

    # Re-run the same aim math that CoordinateAim uses.
    from calculations.target_state import compute_target_state
    state = compute_target_state(
        0.0,                              # heading_deg
        (0.0, 0.0),                       # shooter_xy (zero offsets in tests)
        (_ALLIANCE["target_x"], _ALLIANCE["target_y"]),
        (0.0, 0.0),                       # velocity
        turret.get_position(),
        turret.get_effective_center_position(),
        TEST_CON_POSE["degrees_per_rotation"],
    )
    assert abs(state.error_deg) < 1e-6


def test_resync_changes_offset():
    """Resync writes a nonzero offset when the turret is not already
    aligned with the Hub."""
    turret = Turret()
    turret.motor.simulate_position(_MID_POS + 1.0)
    assert turret.get_center_position_offset() == 0.0

    cmd = ResyncTurret(
        turret,
        pose_supplier=_pose_supplier(),
        alliance_supplier=lambda: _ALLIANCE,
    )
    cmd.initialize()

    assert turret.get_center_position_offset() != 0.0


def test_second_resync_is_idempotent_without_motion():
    """Pressing B twice without the turret moving should leave the
    offset unchanged (the second press measures ~0 error)."""
    turret = Turret()
    turret.motor.simulate_position(_MID_POS + 1.5)

    supplier = _pose_supplier(heading_deg=30.0)
    alliance_supplier = lambda: _ALLIANCE

    ResyncTurret(turret, supplier, alliance_supplier).initialize()
    offset_after_first = turret.get_center_position_offset()

    ResyncTurret(turret, supplier, alliance_supplier).initialize()
    offset_after_second = turret.get_center_position_offset()

    assert abs(offset_after_second - offset_after_first) < 1e-9


def test_second_resync_absorbs_additional_drift():
    """After a resync, rotating the motor (simulated drift) and resyncing
    again should fold the new drift into the offset."""
    turret = Turret()
    turret.motor.simulate_position(_MID_POS)

    supplier = _pose_supplier()
    alliance_supplier = lambda: _ALLIANCE

    ResyncTurret(turret, supplier, alliance_supplier).initialize()
    offset_1 = turret.get_center_position_offset()

    # Simulate the motor encoder slipping: physical turret still on Hub,
    # but motor reports a new position. The resync must re-anchor.
    drift_rot = 0.3
    turret.motor.simulate_position(_MID_POS + drift_rot)

    ResyncTurret(turret, supplier, alliance_supplier).initialize()
    offset_2 = turret.get_center_position_offset()

    # The second offset shifts by exactly the drift (in rotations), since
    # after the first resync error_deg was 0, and we moved the motor by
    # drift_rot, which produces an error of drift_rot * deg_per_rotation.
    expected_delta = drift_rot
    assert abs((offset_2 - offset_1) - expected_delta) < 1e-6


@patch("commands.coordinate_aim.SmartDashboard")
def test_resync_resets_coord_aim_accumulators(mock_sd):
    """When given a CoordinateAim, resync zeros its filtered_error and I term."""
    turret = Turret()
    turret.motor.simulate_position(_MID_POS + 1.0)

    ctx = ShootContext(
        corrected_distance=0.0,
        raw_distance=0.0,
        closing_speed_mps=0.0,
        pose_x=0.0,
        pose_y=0.0,
        heading_deg=0.0,
        shooter_x=0.0,
        shooter_y=0.0,
        target_x=_ALLIANCE["target_x"],
        target_y=_ALLIANCE["target_y"],
        vx=0.0,
        vy=0.0,
    )
    coord_aim = CoordinateAim(
        turret,
        context_supplier=lambda: ctx,
        turret_config=TEST_CON_TURRET_MINION,
    )
    coord_aim.initialize()
    coord_aim.execute()
    # After a cycle with off-target geometry, these should be nonzero.
    assert coord_aim._filtered_error != 0 or coord_aim._i_accumulator != 0

    cmd = ResyncTurret(
        turret,
        pose_supplier=_pose_supplier(),
        alliance_supplier=lambda: _ALLIANCE,
        coord_aim=coord_aim,
    )
    cmd.initialize()

    assert coord_aim._filtered_error == 0.0
    assert coord_aim._i_accumulator == 0.0


def test_turret_offset_defaults_to_zero():
    """Fresh turret has no calibration offset."""
    turret = Turret()
    assert turret.get_center_position_offset() == 0.0
    assert (turret.get_effective_center_position()
            == TEST_CON_POSE["center_position"])


def test_turret_offset_reset():
    """reset_center_position_offset clears a previously-set offset."""
    turret = Turret()
    turret.set_center_position_offset(0.25)
    assert turret.get_center_position_offset() == 0.25

    turret.reset_center_position_offset()
    assert turret.get_center_position_offset() == 0.0
