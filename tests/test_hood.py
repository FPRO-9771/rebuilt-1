"""
Tests for hood subsystem.
"""

from subsystems.hood import Hood
from tests.conftest import TEST_CON_HOOD


def test_hood_position_clamped_at_max():
    """Verify position is clamped to max limit."""
    hood = Hood()

    hood._set_position(100.0)  # Way over max
    assert hood.motor._position == TEST_CON_HOOD["max_position"]


def test_hood_position_clamped_at_min():
    """Verify position is clamped to min limit."""
    hood = Hood()

    hood._set_position(-100.0)  # Way under min
    assert hood.motor._position == TEST_CON_HOOD["min_position"]


def test_hood_position_within_range():
    """Verify position within range is not clamped."""
    hood = Hood()

    mid = (TEST_CON_HOOD["min_position"] + TEST_CON_HOOD["max_position"]) / 2
    hood._set_position(mid)
    assert hood.motor._position == mid


def test_hood_is_at_position():
    """Verify is_at_position with tolerance."""
    hood = Hood()
    tol = TEST_CON_HOOD["position_tolerance"]
    mid = (TEST_CON_HOOD["min_position"] + TEST_CON_HOOD["max_position"]) / 2

    hood.motor.simulate_position(mid)
    assert hood.is_at_position(mid) is True

    # Just within tolerance
    hood.motor.simulate_position(mid + tol)
    assert hood.is_at_position(mid) is True

    # Clearly outside tolerance
    hood.motor.simulate_position(mid + tol * 2)
    assert hood.is_at_position(mid) is False


def test_hood_go_to_position_holds():
    """Verify go_to_position command holds position."""
    hood = Hood()
    mid = (TEST_CON_HOOD["min_position"] + TEST_CON_HOOD["max_position"]) / 2

    cmd = hood.go_to_position(mid)
    cmd.initialize()
    cmd.execute()

    assert hood.motor._position == mid
    assert cmd.isFinished() is False


def test_hood_go_to_position_stops_on_end():
    """Verify go_to_position stops motor when ended."""
    hood = Hood()
    mid = (TEST_CON_HOOD["min_position"] + TEST_CON_HOOD["max_position"]) / 2

    cmd = hood.go_to_position(mid)
    cmd.initialize()
    cmd.execute()

    cmd.end(False)
    assert hood.motor.get_last_voltage() == 0
