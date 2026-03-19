"""
Tests for manual launcher command.
Stick maps to virtual distance via the distance table, which provides RPS.
"""

from subsystems.launcher import Launcher
from commands.manual_launcher import ManualLauncher
from subsystems.shooter_lookup import get_shooter_settings
from tests.conftest import TEST_CON_SHOOTER


def _make_manual_launcher(stick_value=0.0):
    launcher = Launcher()
    cmd = ManualLauncher(launcher, lambda: stick_value)
    return cmd, launcher


def test_stick_center_gives_center_distance_rps():
    """Stick at center (0) produces RPS for center distance."""
    cmd, launcher = _make_manual_launcher(stick_value=0.0)

    cmd.initialize()
    cmd.execute()

    center_d = TEST_CON_SHOOTER["manual_center_distance"]
    expected_rps, _ = get_shooter_settings(center_d)
    assert launcher.motor._velocity == expected_rps


def test_stick_full_forward_gives_max_distance_rps():
    """Stick full forward (1.0) produces RPS for max distance."""
    cmd, launcher = _make_manual_launcher(stick_value=1.0)

    cmd.initialize()
    cmd.execute()

    max_d = TEST_CON_SHOOTER["manual_max_distance"]
    expected_rps, _ = get_shooter_settings(max_d)
    assert launcher.motor._velocity == expected_rps


def test_stick_full_back_gives_min_distance_rps():
    """Stick full back (-1.0) produces RPS for min distance."""
    cmd, launcher = _make_manual_launcher(stick_value=-1.0)

    cmd.initialize()
    cmd.execute()

    min_d = TEST_CON_SHOOTER["manual_min_distance"]
    expected_rps, _ = get_shooter_settings(min_d)
    assert launcher.motor._velocity == expected_rps


def test_stops_on_end():
    """Launcher stops when command ends."""
    cmd, launcher = _make_manual_launcher(stick_value=0.5)

    cmd.initialize()
    cmd.execute()
    cmd.end(False)

    assert launcher.motor.get_last_voltage() == 0


def test_never_auto_finishes():
    """ManualLauncher never auto-finishes."""
    cmd, launcher = _make_manual_launcher()
    cmd.initialize()
    assert cmd.isFinished() is False
