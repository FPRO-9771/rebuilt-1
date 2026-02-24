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
from tests.conftest import TEST_CON_MANUAL, TEST_CON_HOOD


# --- Launcher speed adjustment ---

def test_adjust_launcher_rps_increases():
    """Verify bumper increases launcher speed."""
    step = TEST_CON_MANUAL["launcher_speed_step"]
    start = TEST_CON_MANUAL["launcher_default_rps"]
    state = {"launcher_rps": start}

    adjust_launcher_rps(state, step)
    assert state["launcher_rps"] == start + step


def test_adjust_launcher_rps_decreases():
    """Verify trigger decreases launcher speed."""
    step = TEST_CON_MANUAL["launcher_speed_step"]
    start = TEST_CON_MANUAL["launcher_default_rps"]
    state = {"launcher_rps": start}

    adjust_launcher_rps(state, -step)
    assert state["launcher_rps"] == start - step


def test_adjust_launcher_rps_clamps_at_max():
    """Verify speed can't exceed max."""
    step = TEST_CON_MANUAL["launcher_speed_step"]
    state = {"launcher_rps": TEST_CON_MANUAL["launcher_max_rps"]}

    adjust_launcher_rps(state, step)
    assert state["launcher_rps"] == TEST_CON_MANUAL["launcher_max_rps"]


def test_adjust_launcher_rps_clamps_at_zero():
    """Verify speed can't go below zero."""
    step = TEST_CON_MANUAL["launcher_speed_step"]
    # Start below one step so decrementing would go negative
    state = {"launcher_rps": step * 0.5}

    adjust_launcher_rps(state, -step)
    assert state["launcher_rps"] == 0


# --- Launcher toggle command ---

def test_launcher_toggle_reads_dynamic_rps():
    """Verify toggle command reads current RPS each cycle."""
    launcher = Launcher()
    start = TEST_CON_MANUAL["launcher_default_rps"]
    step = TEST_CON_MANUAL["launcher_speed_step"]
    state = {"launcher_rps": start}

    cmd = _LauncherToggleCommand(launcher, lambda: state["launcher_rps"])
    cmd.initialize()
    cmd.execute()
    assert launcher.motor._velocity == start

    # Change speed mid-run — next execute picks it up
    state["launcher_rps"] = start + step
    cmd.execute()
    assert launcher.motor._velocity == start + step


def test_launcher_toggle_never_finishes():
    """Verify toggle command never auto-finishes."""
    launcher = Launcher()
    rps = TEST_CON_MANUAL["launcher_default_rps"]
    cmd = _LauncherToggleCommand(launcher, lambda: rps)
    cmd.initialize()

    for _ in range(50):
        cmd.execute()
        assert cmd.isFinished() is False


def test_launcher_toggle_stops_on_end():
    """Verify toggle command stops launcher when ended."""
    launcher = Launcher()
    rps = TEST_CON_MANUAL["launcher_default_rps"]
    cmd = _LauncherToggleCommand(launcher, lambda: rps)
    cmd.initialize()
    cmd.execute()

    cmd.end(False)
    assert launcher.motor.get_last_voltage() == 0


# --- Hood nudge ---

def test_nudge_hood_increases_position():
    """Verify bumper nudges hood position up."""
    hood = Hood()
    step = TEST_CON_MANUAL["hood_position_step"]
    start = TEST_CON_MANUAL["hood_default_position"]
    state = {"hood_position": start}

    nudge_hood(state, step, hood)

    assert state["hood_position"] == start + step
    assert hood.motor._position == start + step


def test_nudge_hood_decreases_position():
    """Verify trigger nudges hood position down."""
    hood = Hood()
    step = TEST_CON_MANUAL["hood_position_step"]
    start = TEST_CON_MANUAL["hood_default_position"]
    state = {"hood_position": start}

    nudge_hood(state, -step, hood)

    assert state["hood_position"] == start - step
    assert hood.motor._position == start - step


def test_nudge_hood_clamps_at_max():
    """Verify hood can't be nudged past max."""
    hood = Hood()
    max_pos = TEST_CON_HOOD["max_position"]
    state = {"hood_position": max_pos}

    nudge_hood(state, 1.0, hood)

    assert state["hood_position"] == max_pos
    assert hood.motor._position == max_pos


def test_nudge_hood_clamps_at_min():
    """Verify hood can't be nudged below min."""
    hood = Hood()
    min_pos = TEST_CON_HOOD["min_position"]
    state = {"hood_position": min_pos}

    nudge_hood(state, -1.0, hood)

    assert state["hood_position"] == min_pos
    assert hood.motor._position == min_pos
