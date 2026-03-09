"""
Tests for auto-aim command.
"""

from unittest.mock import patch

from subsystems.turret import Turret
from commands.auto_aim import AutoAim
from handlers.mock_vision import MockVisionProvider
from handlers.vision import VisionTarget
from tests.conftest import (
    TEST_CON_TURRET, TEST_CON_SHOOTER,
    TEST_TAG_PRIORITY, TEST_TAG_OFFSETS, TEST_TARGET_LOCK_LOST_CYCLES,
)

_MID_POS = (TEST_CON_TURRET["min_position"] + TEST_CON_TURRET["max_position"]) / 2


def _make_auto_aim(tag_priority=None, tag_offsets=None,
                   robot_velocity_supplier=None):
    turret = Turret()
    turret.motor.simulate_position(_MID_POS)
    vision = MockVisionProvider()
    priority = tag_priority if tag_priority is not None else TEST_TAG_PRIORITY
    offsets = tag_offsets if tag_offsets is not None else TEST_TAG_OFFSETS
    cmd = AutoAim(
        turret, vision,
        tag_priority_supplier=lambda: priority,
        tag_offsets_supplier=lambda: offsets,
        robot_velocity_supplier=robot_velocity_supplier,
    )
    return cmd, turret, vision


@patch("commands.auto_aim.SmartDashboard")
def test_aims_turret_at_target(mock_sd):
    """Target to the right produces positive turret voltage."""
    cmd, turret, vision = _make_auto_aim()
    vision.simulate_target_right(tag_id=4, offset_degrees=10, distance=2.0)

    cmd.initialize()
    cmd.execute()

    assert turret.motor.get_last_voltage() > 0


@patch("commands.auto_aim.SmartDashboard")
def test_no_voltage_when_no_target(mock_sd):
    """No target means no turret movement."""
    cmd, turret, vision = _make_auto_aim()
    vision.simulate_no_target()

    cmd.initialize()
    cmd.execute()

    assert turret.motor.get_last_voltage() == 0


@patch("commands.auto_aim.SmartDashboard")
def test_publishes_auto_aim_on_initialize(mock_sd):
    """SmartDashboard shows AutoAim = True on init."""
    cmd, turret, vision = _make_auto_aim()
    cmd.initialize()
    mock_sd.putBoolean.assert_any_call("Shooter/AutoAim", True)


@patch("commands.auto_aim.SmartDashboard")
def test_publishes_auto_aim_off_on_end(mock_sd):
    """SmartDashboard shows AutoAim = False on end."""
    cmd, turret, vision = _make_auto_aim()
    cmd.initialize()
    cmd.end(False)
    mock_sd.putBoolean.assert_any_call("Shooter/AutoAim", False)


@patch("commands.auto_aim.SmartDashboard")
def test_stops_turret_on_end(mock_sd):
    """Turret stops when auto-aim ends."""
    cmd, turret, vision = _make_auto_aim()
    vision.simulate_target_right(tag_id=4, offset_degrees=10, distance=2.0)

    cmd.initialize()
    cmd.execute()
    assert turret.motor.get_last_voltage() != 0

    cmd.end(False)
    assert turret.motor.get_last_voltage() == 0


@patch("commands.auto_aim.SmartDashboard")
def test_never_auto_finishes(mock_sd):
    """AutoAim never auto-finishes."""
    cmd, turret, vision = _make_auto_aim()
    cmd.initialize()
    assert cmd.isFinished() is False


@patch("commands.auto_aim.SmartDashboard")
def test_priority_locks_highest(mock_sd):
    """Locks onto highest-priority visible tag."""
    cmd, turret, vision = _make_auto_aim()
    vision.set_target(VisionTarget(tag_id=5, tx=5.0, ty=0, distance=1.5, yaw=0))
    vision.set_target(VisionTarget(tag_id=4, tx=10.0, ty=0, distance=3.0, yaw=0))

    cmd.initialize()
    cmd.execute()

    assert cmd._locked_tag_id == 4


@patch("commands.auto_aim.SmartDashboard")
def test_stickiness_holds_lock(mock_sd):
    """Locked tag stays locked during brief loss."""
    cmd, turret, vision = _make_auto_aim()
    vision.simulate_target_centered(tag_id=4, distance=2.0)

    cmd.initialize()
    cmd.execute()
    assert cmd._locked_tag_id == 4

    vision.simulate_no_target()
    for _ in range(TEST_TARGET_LOCK_LOST_CYCLES - 1):
        cmd.execute()

    assert cmd._locked_tag_id == 4


@patch("commands.auto_aim.SmartDashboard")
def test_stickiness_unlocks_after_threshold(mock_sd):
    """Lock releases after enough consecutive lost cycles."""
    cmd, turret, vision = _make_auto_aim()
    vision.simulate_target_centered(tag_id=4, distance=2.0)

    cmd.initialize()
    cmd.execute()
    assert cmd._locked_tag_id == 4

    vision.simulate_no_target()
    for _ in range(TEST_TARGET_LOCK_LOST_CYCLES):
        cmd.execute()

    assert cmd._locked_tag_id is None


@patch("commands.auto_aim.SmartDashboard")
def test_velocity_compensation_shifts_aim(mock_sd):
    """Strafing right shifts aim further right (positive lead)."""
    # No velocity -- baseline
    cmd_still, turret_still, vision_still = _make_auto_aim(
        robot_velocity_supplier=lambda: (0.0, 0.0),
    )
    vision_still.simulate_target_centered(tag_id=4, distance=3.0)
    cmd_still.initialize()
    cmd_still.execute()
    v_still = turret_still.motor.get_last_voltage()

    # Strafing right at 2 m/s
    cmd_moving, turret_moving, vision_moving = _make_auto_aim(
        robot_velocity_supplier=lambda: (0.0, 2.0),
    )
    vision_moving.simulate_target_centered(tag_id=4, distance=3.0)
    cmd_moving.initialize()
    cmd_moving.execute()
    v_moving = turret_moving.motor.get_last_voltage()

    # Moving right should produce more positive voltage than standing still
    assert v_moving > v_still


@patch("commands.auto_aim.SmartDashboard")
def test_no_velocity_supplier_works(mock_sd):
    """AutoAim still works when no velocity supplier is provided."""
    cmd, turret, vision = _make_auto_aim(robot_velocity_supplier=None)
    vision.simulate_target_right(tag_id=4, offset_degrees=10, distance=2.0)
    cmd.initialize()
    cmd.execute()
    assert turret.motor.get_last_voltage() > 0
