"""
Tests for turret routing (smart direction selection).
Pure math -- no hardware dependencies.
"""

from calculations.turret_routing import choose_rotation_direction


# Use test constants: min=-5, max=5, deg_per_rotation=40
_MIN = -5.0
_MAX = 5.0
_DEG_PER_ROT = 40.0


def test_shortest_path_within_limits():
    """Shortest path within limits -> error unchanged."""
    error = choose_rotation_direction(0.0, 20.0, _MIN, _MAX, _DEG_PER_ROT)
    assert error == 20.0


def test_negative_error_within_limits():
    """Negative shortest path within limits -> unchanged."""
    error = choose_rotation_direction(0.0, -20.0, _MIN, _MAX, _DEG_PER_ROT)
    assert error == -20.0


def test_shortest_path_hits_max_limit_reverses():
    """Shortest path would exceed max limit -> reverses direction."""
    # At position 4.0, error +80 deg = +2 rotations -> target 6.0 > max 5.0
    # Reverse: error -280 deg = -7 rotations -> target -3.0, within limits
    error = choose_rotation_direction(4.0, 80.0, _MIN, _MAX, _DEG_PER_ROT)
    assert error < 0  # reversed to negative direction


def test_shortest_path_hits_min_limit_reverses():
    """Shortest path would exceed min limit -> reverses direction."""
    # At position -4.0, error -80 deg = -2 rotations -> target -6.0 < min -5.0
    # Reverse: error +280 deg = +7 rotations -> target 3.0, within limits
    error = choose_rotation_direction(-4.0, -80.0, _MIN, _MAX, _DEG_PER_ROT)
    assert error > 0  # reversed to positive direction


def test_zero_error_stays_zero():
    """Zero error -> zero result."""
    error = choose_rotation_direction(0.0, 0.0, _MIN, _MAX, _DEG_PER_ROT)
    assert error == 0.0


def test_both_paths_blocked_returns_best_effort():
    """Both directions blocked -> returns error toward closest limit."""
    # At position 4.5, huge error that exceeds both directions
    # Should clamp to the nearest reachable limit
    error = choose_rotation_direction(4.5, 170.0, _MIN, _MAX, _DEG_PER_ROT)
    # Result should be finite and move toward a limit
    assert error != 0.0
    target_rot = 4.5 + error / _DEG_PER_ROT
    assert _MIN <= target_rot <= _MAX


def test_zero_deg_per_rotation_returns_error():
    """Edge case: zero degrees_per_rotation returns error unchanged."""
    error = choose_rotation_direction(0.0, 45.0, _MIN, _MAX, 0.0)
    assert error == 45.0
