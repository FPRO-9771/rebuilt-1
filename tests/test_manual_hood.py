"""
Tests for manual hood command.
"""

from subsystems.hood import Hood
from commands.manual_hood import ManualHood
from tests.conftest import TEST_CON_MANUAL, TEST_CON_HOOD


def test_nudge_up_increases_position():
    """Stick up (positive) nudges hood position up by one step."""
    hood = Hood()
    cmd = ManualHood(hood, lambda: 0.5, deadband=0.1)

    cmd.initialize()
    cmd.execute()  # First cycle with stick active -> nudge

    expected = TEST_CON_MANUAL["hood_default_position"] + TEST_CON_MANUAL["hood_position_step"]
    assert hood.motor._position == expected


def test_nudge_down_decreases_position():
    """Stick down (negative) nudges hood position down by one step."""
    hood = Hood()
    cmd = ManualHood(hood, lambda: -0.5, deadband=0.1)

    cmd.initialize()
    cmd.execute()

    expected = TEST_CON_MANUAL["hood_default_position"] - TEST_CON_MANUAL["hood_position_step"]
    assert hood.motor._position == expected


def test_holding_stick_does_not_repeat_nudge():
    """Holding stick past deadband should only nudge once (edge-triggered)."""
    hood = Hood()
    cmd = ManualHood(hood, lambda: 0.5, deadband=0.1)

    cmd.initialize()
    cmd.execute()  # Nudge happens here
    cmd.execute()  # Still held -- no second nudge

    expected = TEST_CON_MANUAL["hood_default_position"] + TEST_CON_MANUAL["hood_position_step"]
    assert hood.motor._position == expected


def test_release_and_retap_nudges_again():
    """Releasing and re-deflecting the stick triggers a second nudge."""
    hood = Hood()
    values = [0.5, 0.5, 0.0, 0.5]
    idx = {"i": 0}

    def supplier():
        val = values[idx["i"]]
        idx["i"] += 1
        return val

    cmd = ManualHood(hood, supplier, deadband=0.1)
    cmd.initialize()

    cmd.execute()  # 0.5 -> nudge 1
    cmd.execute()  # 0.5 -> held, no nudge
    cmd.execute()  # 0.0 -> released
    cmd.execute()  # 0.5 -> nudge 2

    step = TEST_CON_MANUAL["hood_position_step"]
    expected = TEST_CON_MANUAL["hood_default_position"] + 2 * step
    assert hood.motor._position == expected


def test_position_clamped_at_max():
    """Nudging past max_position clamps to max."""
    hood = Hood()
    # Start near max so one nudge would exceed it
    cmd = ManualHood(hood, lambda: 0.5, deadband=0.1)
    cmd.initialize()
    cmd._target = TEST_CON_HOOD["max_position"]

    # Release then tap to trigger edge
    cmd._was_active = False
    cmd.execute()

    assert hood.motor._position == TEST_CON_HOOD["max_position"]


def test_position_clamped_at_min():
    """Nudging past min_position clamps to min."""
    hood = Hood()
    cmd = ManualHood(hood, lambda: -0.5, deadband=0.1)
    cmd.initialize()
    cmd._target = TEST_CON_HOOD["min_position"]

    cmd._was_active = False
    cmd.execute()

    assert hood.motor._position == TEST_CON_HOOD["min_position"]


def test_stick_in_deadband_holds_position():
    """Stick within deadband should hold current position, not nudge."""
    hood = Hood()
    cmd = ManualHood(hood, lambda: 0.05, deadband=0.1)

    cmd.initialize()
    cmd.execute()

    assert hood.motor._position == TEST_CON_MANUAL["hood_default_position"]


def test_end_stops_hood():
    """Ending the command stops the hood motor."""
    hood = Hood()
    cmd = ManualHood(hood, lambda: 0.0, deadband=0.1)

    cmd.initialize()
    cmd.execute()
    cmd.end(False)

    assert hood.motor.get_last_voltage() == 0
