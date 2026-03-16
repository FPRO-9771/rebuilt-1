"""
Tests for distance compensation (closing speed correction).
"""

from calculations.distance_compensation import compute_corrected_distance
from subsystems.shooter_lookup import get_ball_speed


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


def test_correction_uses_ball_speed():
    """Correction magnitude depends on ball flight time."""
    # At distance 3.0, ball speed from test table is 8.0 m/s
    # flight_time = 3.0 / 8.0 = 0.375s
    # closing at 1.0 m/s -> correction = 1.0 * 0.375 = 0.375m
    ball_speed = get_ball_speed(3.0)
    flight_time = 3.0 / ball_speed
    expected = 3.0 - 1.0 * flight_time
    result = compute_corrected_distance(3.0, 1.0)
    assert abs(result - expected) < 0.001


def test_clamps_minimum_distance():
    """Very high closing speed clamps to minimum 0.5m."""
    result = compute_corrected_distance(2.0, 100.0)
    assert result == 0.5


def test_short_distance_no_correction():
    """Distances below 0.5m are returned unchanged."""
    result = compute_corrected_distance(0.3, 5.0)
    assert result == 0.3


def test_faster_closing_gives_shorter_distance():
    """Faster closing speed produces shorter corrected distance."""
    slow = compute_corrected_distance(3.0, 0.5)
    fast = compute_corrected_distance(3.0, 2.0)
    assert fast < slow
