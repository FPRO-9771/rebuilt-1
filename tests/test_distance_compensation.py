"""
Tests for distance compensation (closing speed correction).
"""

from calculations.distance_compensation import compute_corrected_distance
from subsystems.shooter_lookup import get_flight_time


def test_stationary_no_correction():
    """Zero closing speed returns original distance."""
    result = compute_corrected_distance(3.0, 0.0)
    assert result == 3.0


def test_closing_reduces_distance():
    """Positive closing speed reduces the corrected distance."""
    result = compute_corrected_distance(3.0, 1.0)
    assert result < 3.0


def test_retreating_increases_distance():
    """Negative closing speed (retreating) increases the corrected distance."""
    result = compute_corrected_distance(3.0, -1.0)
    assert result > 3.0


def test_correction_uses_flight_time():
    """Correction magnitude scales with flight time from the table."""
    flight_time = get_flight_time(3.0)
    result = compute_corrected_distance(3.0, 1.0)
    # Corrected distance should be less than raw when closing (positive speed)
    assert result < 3.0
    # The correction should be proportional to flight time: a longer
    # flight time at a different distance should give a bigger correction.
    flight_time_far = get_flight_time(4.0)
    result_far = compute_corrected_distance(4.0, 1.0)
    correction_near = 3.0 - result
    correction_far = 4.0 - result_far
    if flight_time_far > flight_time:
        assert correction_far > correction_near


def test_clamps_minimum_distance():
    """Very high closing speed clamps to minimum distance."""
    result = compute_corrected_distance(2.0, 100.0)
    assert result == 0.5


def test_short_distance_no_correction():
    """Distances below min_distance are returned unchanged."""
    result = compute_corrected_distance(0.3, 5.0)
    assert result == 0.3


def test_faster_closing_gives_shorter_distance():
    """Faster closing speed produces shorter corrected distance."""
    slow = compute_corrected_distance(3.0, 0.5)
    fast = compute_corrected_distance(3.0, 2.0)
    assert fast < slow
