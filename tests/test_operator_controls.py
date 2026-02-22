"""
Tests for operator manual controls.
"""

from subsystems.launcher import Launcher
from subsystems.hood import Hood
from controls.operator_controls import (
    adjust_launcher_rps,
    nudge_hood,
    _LauncherToggleCommand,
)
from constants import CON_MANUAL, CON_HOOD


# --- Launcher speed adjustment ---

def test_adjust_launcher_rps_increases():
    """Verify bumper increases launcher speed."""
    state = {"launcher_rps": 40.0}
    adjust_launcher_rps(state, CON_MANUAL["launcher_speed_step"])
    assert state["launcher_rps"] == 40.0 + CON_MANUAL["launcher_speed_step"]


def test_adjust_launcher_rps_decreases():
    """Verify trigger decreases launcher speed."""
    state = {"launcher_rps": 40.0}
    adjust_launcher_rps(state, -CON_MANUAL["launcher_speed_step"])
    assert state["launcher_rps"] == 40.0 - CON_MANUAL["launcher_speed_step"]


def test_adjust_launcher_rps_clamps_at_max():
    """Verify speed can't exceed max."""
    state = {"launcher_rps": CON_MANUAL["launcher_max_rps"]}
    adjust_launcher_rps(state, CON_MANUAL["launcher_speed_step"])
    assert state["launcher_rps"] == CON_MANUAL["launcher_max_rps"]


def test_adjust_launcher_rps_clamps_at_zero():
    """Verify speed can't go below zero."""
    state = {"launcher_rps": 2.0}
    adjust_launcher_rps(state, -CON_MANUAL["launcher_speed_step"])
    assert state["launcher_rps"] == 0


# --- Launcher toggle command ---

def test_launcher_toggle_reads_dynamic_rps():
    """Verify toggle command reads current RPS each cycle."""
    launcher = Launcher()
    state = {"launcher_rps": 40.0}

    cmd = _LauncherToggleCommand(launcher, lambda: state["launcher_rps"])
    cmd.initialize()
    cmd.execute()
    assert launcher.motor._velocity == 40.0

    # Change speed mid-run — next execute picks it up
    state["launcher_rps"] = 60.0
    cmd.execute()
    assert launcher.motor._velocity == 60.0


def test_launcher_toggle_never_finishes():
    """Verify toggle command never auto-finishes."""
    launcher = Launcher()
    cmd = _LauncherToggleCommand(launcher, lambda: 50.0)
    cmd.initialize()

    for _ in range(50):
        cmd.execute()
        assert cmd.isFinished() is False


def test_launcher_toggle_stops_on_end():
    """Verify toggle command stops launcher when ended."""
    launcher = Launcher()
    cmd = _LauncherToggleCommand(launcher, lambda: 50.0)
    cmd.initialize()
    cmd.execute()

    cmd.end(False)
    assert launcher.motor.get_last_voltage() == 0


# --- Hood nudge ---

def test_nudge_hood_increases_position():
    """Verify bumper nudges hood position up."""
    hood = Hood()
    state = {"hood_position": 0.125}
    step = CON_MANUAL["hood_position_step"]

    nudge_hood(state, step, hood)

    assert state["hood_position"] == 0.125 + step
    assert hood.motor._position == 0.125 + step


def test_nudge_hood_decreases_position():
    """Verify trigger nudges hood position down."""
    hood = Hood()
    state = {"hood_position": 0.125}
    step = CON_MANUAL["hood_position_step"]

    nudge_hood(state, -step, hood)

    assert state["hood_position"] == 0.125 - step
    assert hood.motor._position == 0.125 - step


def test_nudge_hood_clamps_at_max():
    """Verify hood can't be nudged past max."""
    hood = Hood()
    state = {"hood_position": CON_HOOD["max_position"]}

    nudge_hood(state, 1.0, hood)

    assert state["hood_position"] == CON_HOOD["max_position"]
    assert hood.motor._position == CON_HOOD["max_position"]


def test_nudge_hood_clamps_at_min():
    """Verify hood can't be nudged below min."""
    hood = Hood()
    state = {"hood_position": CON_HOOD["min_position"]}

    nudge_hood(state, -1.0, hood)

    assert state["hood_position"] == CON_HOOD["min_position"]
    assert hood.motor._position == CON_HOOD["min_position"]
