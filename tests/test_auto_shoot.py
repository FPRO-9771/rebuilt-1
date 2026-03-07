"""
Tests for auto-shoot command.
"""

from subsystems.launcher import Launcher
from subsystems.hood import Hood
from handlers.mock_vision import MockVisionProvider
from commands.auto_shoot import AutoShoot
from subsystems.shooter_lookup import get_shooter_settings
from tests.conftest import TEST_CON_SHOOTER, TEST_TAG_PRIORITY


def _make_auto_shoot(tag_priority=None):
    launcher = Launcher()
    hood = Hood()
    vision = MockVisionProvider()
    priority = tag_priority if tag_priority is not None else TEST_TAG_PRIORITY
    cmd = AutoShoot(
        launcher, hood, vision,
        tag_priority_supplier=lambda: priority,
    )
    return cmd, launcher, hood, vision


def test_sets_launcher_from_distance():
    """Launcher RPS matches distance table lookup."""
    cmd, launcher, hood, vision = _make_auto_shoot()
    vision.simulate_target_centered(tag_id=4, distance=2.0)

    cmd.initialize()
    cmd.execute()

    expected_rps, _ = get_shooter_settings(2.0)
    assert launcher.motor._velocity == expected_rps


def test_sets_hood_from_distance():
    """Hood position matches distance table lookup."""
    cmd, launcher, hood, vision = _make_auto_shoot()
    vision.simulate_target_centered(tag_id=4, distance=3.0)

    cmd.initialize()
    cmd.execute()

    _, expected_hood = get_shooter_settings(3.0)
    assert hood.motor._position == expected_hood


def test_uses_priority_tag_distance():
    """Uses distance from highest-priority visible tag."""
    cmd, launcher, hood, vision = _make_auto_shoot()
    # Tag 4 is higher priority than tag 5
    from handlers.vision import VisionTarget
    vision.set_target(VisionTarget(tag_id=5, tx=0, ty=0, distance=1.0, yaw=0))
    vision.set_target(VisionTarget(tag_id=4, tx=0, ty=0, distance=3.0, yaw=0))

    cmd.initialize()
    cmd.execute()

    expected_rps, _ = get_shooter_settings(3.0)
    assert launcher.motor._velocity == expected_rps


def test_holds_last_distance_when_target_lost():
    """Uses last known distance when no target visible."""
    cmd, launcher, hood, vision = _make_auto_shoot()
    vision.simulate_target_centered(tag_id=4, distance=3.0)

    cmd.initialize()
    cmd.execute()

    # Target disappears
    vision.simulate_no_target()
    cmd.execute()

    # Should still use distance=3.0
    expected_rps, _ = get_shooter_settings(3.0)
    assert launcher.motor._velocity == expected_rps


def test_stops_all_on_end():
    """Launcher and hood stop when command ends."""
    cmd, launcher, hood, vision = _make_auto_shoot()
    vision.simulate_target_centered(tag_id=4, distance=2.0)

    cmd.initialize()
    cmd.execute()
    cmd.end(False)

    assert launcher.motor.get_last_voltage() == 0
    assert hood.motor.get_last_voltage() == 0


def test_never_auto_finishes():
    """AutoShoot never auto-finishes."""
    cmd, launcher, hood, vision = _make_auto_shoot()
    cmd.initialize()
    assert cmd.isFinished() is False
