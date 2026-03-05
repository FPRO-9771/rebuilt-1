"""
Tests for shoot command.
"""

from unittest.mock import patch, MagicMock

from subsystems.launcher import Launcher
from subsystems.hood import Hood
from subsystems.shooter_lookup import get_shooter_settings
from commands.shoot_command import ShootCommand
from tests.conftest import TEST_CON_SHOOTER


def _make_shoot_command(locked=False, distance=2.0):
    """Helper to create ShootCommand with a mock tracker."""
    tracker = MagicMock()
    tracker.is_locked.return_value = locked
    tracker.get_distance.return_value = distance
    launcher = Launcher()
    hood = Hood()
    cmd = ShootCommand(tracker, launcher, hood)
    return cmd, tracker, launcher, hood


def test_pre_spins_launcher_when_not_locked():
    """Launcher spins up even when not locked."""
    cmd, tracker, launcher, hood = _make_shoot_command(locked=False, distance=2.0)

    cmd.initialize()
    cmd.execute()

    expected_rps, _ = get_shooter_settings(2.0)
    assert launcher.motor._velocity == expected_rps


def test_sets_hood_when_not_locked():
    """Hood position is set even when not locked."""
    cmd, tracker, launcher, hood = _make_shoot_command(locked=False, distance=3.0)

    cmd.initialize()
    cmd.execute()

    _, expected_hood = get_shooter_settings(3.0)
    assert hood.motor._position == expected_hood


def test_uses_tracker_distance():
    """Settings come from tracker's reported distance."""
    cmd, tracker, launcher, hood = _make_shoot_command(locked=True, distance=3.0)

    cmd.initialize()
    cmd.execute()

    expected_rps, expected_hood = get_shooter_settings(3.0)
    assert launcher.motor._velocity == expected_rps
    assert hood.motor._position == expected_hood


def test_stops_all_on_end():
    """Launcher and hood stop when command ends."""
    cmd, tracker, launcher, hood = _make_shoot_command(locked=True, distance=2.0)

    cmd.initialize()
    cmd.execute()
    cmd.end(False)

    assert launcher.motor.get_last_voltage() == 0
    assert hood.motor.get_last_voltage() == 0


def test_never_auto_finishes():
    """ShootCommand never auto-finishes."""
    cmd, tracker, launcher, hood = _make_shoot_command()

    cmd.initialize()
    assert cmd.isFinished() is False
