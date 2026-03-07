"""
Tests for manual launcher command.
"""

from subsystems.launcher import Launcher
from commands.manual_launcher import ManualLauncher
from tests.conftest import TEST_CON_MANUAL


def _make_manual_launcher(stick_value=0.0):
    launcher = Launcher()
    cmd = ManualLauncher(launcher, lambda: stick_value)
    return cmd, launcher


def test_stick_center_gives_midpoint_rps():
    """Stick at center (0) produces midpoint of min/max RPS."""
    cmd, launcher = _make_manual_launcher(stick_value=0.0)

    cmd.initialize()
    cmd.execute()

    min_rps = TEST_CON_MANUAL["launcher_min_rps"]
    max_rps = TEST_CON_MANUAL["launcher_max_rps"]
    expected = (min_rps + max_rps) / 2.0
    assert launcher.motor._velocity == expected


def test_stick_full_forward_gives_max_rps():
    """Stick full forward (1.0) produces max RPS."""
    cmd, launcher = _make_manual_launcher(stick_value=1.0)

    cmd.initialize()
    cmd.execute()

    assert launcher.motor._velocity == TEST_CON_MANUAL["launcher_max_rps"]


def test_stick_full_back_gives_min_rps():
    """Stick full back (-1.0) produces min RPS."""
    cmd, launcher = _make_manual_launcher(stick_value=-1.0)

    cmd.initialize()
    cmd.execute()

    assert launcher.motor._velocity == TEST_CON_MANUAL["launcher_min_rps"]


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
