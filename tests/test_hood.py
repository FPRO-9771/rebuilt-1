"""
Tests for hood subsystem.
"""

from subsystems.hood import Hood
from constants import CON_HOOD


def test_hood_position_clamped_at_max():
    """Verify position is clamped to max limit."""
    hood = Hood()

    hood._set_position(100.0)  # Way over max
    # Mock set_position sets _position directly
    assert hood.motor._position == CON_HOOD["max_position"]


def test_hood_position_clamped_at_min():
    """Verify position is clamped to min limit."""
    hood = Hood()

    hood._set_position(-100.0)  # Way under min
    assert hood.motor._position == CON_HOOD["min_position"]


def test_hood_position_within_range():
    """Verify position within range is not clamped."""
    hood = Hood()

    mid = (CON_HOOD["min_position"] + CON_HOOD["max_position"]) / 2
    hood._set_position(mid)
    assert hood.motor._position == mid


def test_hood_is_at_position():
    """Verify is_at_position with tolerance."""
    hood = Hood()

    hood.motor.simulate_position(0.1)
    assert hood.is_at_position(0.1) is True

    # Just within tolerance
    tol = CON_HOOD["position_tolerance"]
    hood.motor.simulate_position(0.1 + tol)
    assert hood.is_at_position(0.1) is True

    # Just outside tolerance
    hood.motor.simulate_position(0.1 + tol + 0.001)
    assert hood.is_at_position(0.1) is False


def test_hood_go_to_position_holds():
    """Verify go_to_position command holds position."""
    hood = Hood()

    cmd = hood.go_to_position(0.15)
    cmd.initialize()
    cmd.execute()

    assert hood.motor._position == 0.15
    assert cmd.isFinished() is False


def test_hood_go_to_position_stops_on_end():
    """Verify go_to_position stops motor when ended."""
    hood = Hood()

    cmd = hood.go_to_position(0.15)
    cmd.initialize()
    cmd.execute()

    cmd.end(False)
    assert hood.motor.get_last_voltage() == 0
