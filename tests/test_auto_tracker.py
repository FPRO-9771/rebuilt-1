"""
Tests for auto-tracker command.
"""

from unittest.mock import patch

from subsystems.turret import Turret
from commands.auto_tracker import AutoTracker
from handlers.mock_vision import MockVisionProvider
from handlers.vision import VisionTarget
from subsystems.shooter_lookup import get_shooter_settings
from tests.conftest import (
    TEST_CON_TURRET, TEST_CON_SHOOTER,
    TEST_TAG_PRIORITY, TEST_TAG_OFFSETS, TEST_TARGET_LOCK_LOST_CYCLES,
)

_MID_POS = (TEST_CON_TURRET["min_position"] + TEST_CON_TURRET["max_position"]) / 2


def _make_tracker(tag_priority=None, tag_offsets=None):
    turret = Turret()
    turret.motor.simulate_position(_MID_POS)
    vision = MockVisionProvider()
    priority = tag_priority if tag_priority is not None else TEST_TAG_PRIORITY
    offsets = tag_offsets if tag_offsets is not None else TEST_TAG_OFFSETS
    cmd = AutoTracker(
        turret, vision,
        tag_priority_supplier=lambda: priority,
        tag_offsets_supplier=lambda: offsets,
    )
    return cmd, turret, vision


@patch("commands.auto_tracker.DriverStation")
def test_aims_turret_at_target(mock_ds):
    """Target to the right produces positive turret voltage."""
    mock_ds.isTeleopEnabled.return_value = True
    cmd, turret, vision = _make_tracker()
    vision.simulate_target_right(tag_id=4, offset_degrees=10, distance=2.0)

    cmd.initialize()
    cmd.execute()

    assert turret.motor.get_last_voltage() > 0


@patch("commands.auto_tracker.DriverStation")
def test_locked_when_centered_and_in_range(mock_ds):
    """Lock is True when target is centered and distance is in table range."""
    mock_ds.isTeleopEnabled.return_value = True
    cmd, turret, vision = _make_tracker()
    table = TEST_CON_SHOOTER["distance_table"]
    mid_dist = (table[0][0] + table[-1][0]) / 2
    vision.simulate_target_centered(tag_id=4, distance=mid_dist)

    cmd.initialize()
    cmd.execute()

    assert cmd.is_locked() is True


@patch("commands.auto_tracker.DriverStation")
def test_not_locked_when_misaligned(mock_ds):
    """Lock is False when turret is far from aligned."""
    mock_ds.isTeleopEnabled.return_value = True
    cmd, turret, vision = _make_tracker()
    # Offset well beyond alignment tolerance
    offset = TEST_CON_SHOOTER["turret_alignment_tolerance"] + 10
    vision.simulate_target_right(tag_id=4, offset_degrees=offset, distance=2.0)

    cmd.initialize()
    cmd.execute()

    assert cmd.is_locked() is False


@patch("commands.auto_tracker.DriverStation")
def test_not_locked_when_out_of_range(mock_ds):
    """Lock is False when distance is outside the table range."""
    mock_ds.isTeleopEnabled.return_value = True
    cmd, turret, vision = _make_tracker()
    table = TEST_CON_SHOOTER["distance_table"]
    too_far = table[-1][0] + 10.0
    vision.simulate_target_centered(tag_id=4, distance=too_far)

    cmd.initialize()
    cmd.execute()

    assert cmd.is_locked() is False


@patch("commands.auto_tracker.DriverStation")
def test_not_locked_when_no_target(mock_ds):
    """Lock is False when no target is visible."""
    mock_ds.isTeleopEnabled.return_value = True
    cmd, turret, vision = _make_tracker()
    vision.simulate_no_target()

    cmd.initialize()
    cmd.execute()

    assert cmd.is_locked() is False


@patch("commands.auto_tracker.DriverStation")
@patch("commands.auto_tracker.SmartDashboard")
def test_teleop_guard_skips_aiming(mock_sd, mock_ds):
    """When not in teleop, tracker clears state and does not aim."""
    mock_ds.isTeleopEnabled.return_value = False
    cmd, turret, vision = _make_tracker()
    vision.simulate_target_right(tag_id=4, offset_degrees=10, distance=2.0)

    cmd.initialize()
    cmd.execute()

    # Turret should not have been commanded (voltage stays at 0)
    assert turret.motor.get_last_voltage() == 0
    assert cmd.is_locked() is False


@patch("commands.auto_tracker.DriverStation")
def test_get_distance_returns_tracked_value(mock_ds):
    """get_distance returns the distance from vision."""
    mock_ds.isTeleopEnabled.return_value = True
    cmd, turret, vision = _make_tracker()
    vision.simulate_target_centered(tag_id=4, distance=3.5)

    cmd.initialize()
    cmd.execute()

    assert cmd.get_distance() == 3.5


@patch("commands.auto_tracker.DriverStation")
def test_never_auto_finishes(mock_ds):
    """Tracker never auto-finishes."""
    mock_ds.isTeleopEnabled.return_value = True
    cmd, turret, vision = _make_tracker()

    cmd.initialize()
    assert cmd.isFinished() is False


@patch("commands.auto_tracker.DriverStation")
def test_stops_turret_on_end(mock_ds):
    """Turret stops when tracker ends."""
    mock_ds.isTeleopEnabled.return_value = True
    cmd, turret, vision = _make_tracker()
    vision.simulate_target_right(tag_id=4, offset_degrees=10, distance=2.0)

    cmd.initialize()
    cmd.execute()
    assert turret.motor.get_last_voltage() != 0

    cmd.end(False)
    assert turret.motor.get_last_voltage() == 0


# =========================================================================
# Priority-based targeting tests
# =========================================================================


@patch("commands.auto_tracker.DriverStation")
def test_locks_onto_highest_priority_tag(mock_ds):
    """When multiple tags visible, locks onto highest priority."""
    mock_ds.isTeleopEnabled.return_value = True
    cmd, turret, vision = _make_tracker()
    # Tag 4 is first in priority, tag 5 is second
    vision.set_target(VisionTarget(tag_id=5, tx=5.0, ty=0, distance=1.5, yaw=0))
    vision.set_target(VisionTarget(tag_id=4, tx=10.0, ty=0, distance=3.0, yaw=0))

    cmd.initialize()
    cmd.execute()

    # Should lock onto tag 4 (higher priority) even though 5 is closer
    assert cmd._locked_tag_id == 4


@patch("commands.auto_tracker.DriverStation")
def test_ignores_tags_not_in_priority(mock_ds):
    """Tags not in the priority list are ignored."""
    mock_ds.isTeleopEnabled.return_value = True
    cmd, turret, vision = _make_tracker()
    # Tag 99 is not in TEST_TAG_PRIORITY
    vision.simulate_target_centered(tag_id=99, distance=2.0)

    cmd.initialize()
    cmd.execute()

    assert cmd._locked_tag_id is None
    assert cmd.is_locked() is False


@patch("commands.auto_tracker.DriverStation")
def test_stickiness_holds_lock_during_brief_loss(mock_ds):
    """Locked tag stays locked for a few cycles after disappearing."""
    mock_ds.isTeleopEnabled.return_value = True
    cmd, turret, vision = _make_tracker()
    vision.simulate_target_centered(tag_id=4, distance=2.0)

    cmd.initialize()
    cmd.execute()
    assert cmd._locked_tag_id == 4

    # Target disappears for fewer cycles than the threshold
    vision.simulate_no_target()
    for _ in range(TEST_TARGET_LOCK_LOST_CYCLES - 1):
        cmd.execute()

    # Lock should still be held
    assert cmd._locked_tag_id == 4


@patch("commands.auto_tracker.DriverStation")
def test_stickiness_unlocks_after_threshold(mock_ds):
    """Lock releases after enough consecutive lost cycles."""
    mock_ds.isTeleopEnabled.return_value = True
    cmd, turret, vision = _make_tracker()
    vision.simulate_target_centered(tag_id=4, distance=2.0)

    cmd.initialize()
    cmd.execute()
    assert cmd._locked_tag_id == 4

    # Target disappears for exactly the threshold number of cycles
    vision.simulate_no_target()
    for _ in range(TEST_TARGET_LOCK_LOST_CYCLES):
        cmd.execute()

    # Lock should have released
    assert cmd._locked_tag_id is None


@patch("commands.auto_tracker.DriverStation")
def test_stickiness_does_not_switch_to_other_tag(mock_ds):
    """While locked on tag 4, seeing tag 5 does not cause a switch."""
    mock_ds.isTeleopEnabled.return_value = True
    cmd, turret, vision = _make_tracker()
    vision.simulate_target_centered(tag_id=4, distance=2.0)

    cmd.initialize()
    cmd.execute()
    assert cmd._locked_tag_id == 4

    # Now tag 4 disappears and tag 5 appears (closer)
    vision.simulate_no_target()
    vision.set_target(VisionTarget(tag_id=5, tx=0, ty=0, distance=1.0, yaw=0))

    # Run a few cycles (under threshold) -- should still be locked on 4
    for _ in range(TEST_TARGET_LOCK_LOST_CYCLES - 1):
        cmd.execute()
    assert cmd._locked_tag_id == 4


@patch("commands.auto_tracker.DriverStation")
def test_falls_through_to_lower_priority_tag(mock_ds):
    """After lock expires, picks next visible tag from priority list."""
    mock_ds.isTeleopEnabled.return_value = True
    cmd, turret, vision = _make_tracker()
    vision.simulate_target_centered(tag_id=4, distance=2.0)

    cmd.initialize()
    cmd.execute()
    assert cmd._locked_tag_id == 4

    # Tag 4 disappears, tag 5 appears
    vision.simulate_no_target()
    vision.set_target(VisionTarget(tag_id=5, tx=3.0, ty=0, distance=1.5, yaw=0))

    # Run past the lock threshold
    for _ in range(TEST_TARGET_LOCK_LOST_CYCLES):
        cmd.execute()

    # Now should lock onto tag 5
    cmd.execute()
    assert cmd._locked_tag_id == 5
