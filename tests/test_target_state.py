"""
Tests for target state calculation.
Pure math -- no hardware dependencies, no fake objects needed.
"""

from calculations.target_state import compute_target_state, compute_range_state


def test_target_directly_ahead_zero_error():
    """Target straight ahead of robot with turret centered -> ~0 error."""
    state = compute_target_state(
        heading_deg=0.0,  # facing +X
        shooter_xy=(0.0, 0.0),
        target_xy=(5.0, 0.0),
        velocity_xy=(0.0, 0.0),
        turret_position=0.0, center_position=0.0, deg_per_rotation=40.0,
    )
    assert abs(state.error_deg) < 0.1
    assert abs(state.distance_m - 5.0) < 0.01


def test_target_to_the_left():
    """Target 90 degrees left -> positive error (turret needs to rotate left)."""
    state = compute_target_state(
        heading_deg=0.0,
        shooter_xy=(0.0, 0.0),
        target_xy=(0.0, 5.0),
        velocity_xy=(0.0, 0.0),
        turret_position=0.0, center_position=0.0, deg_per_rotation=40.0,
    )
    assert abs(state.error_deg - 90.0) < 0.1


def test_target_to_the_right():
    """Target 90 degrees right -> negative error."""
    state = compute_target_state(
        heading_deg=0.0,
        shooter_xy=(0.0, 0.0),
        target_xy=(0.0, -5.0),
        velocity_xy=(0.0, 0.0),
        turret_position=0.0, center_position=0.0, deg_per_rotation=40.0,
    )
    assert abs(state.error_deg - (-90.0)) < 0.1


def test_turret_already_aimed_reduces_error():
    """Turret rotated toward target reduces the error."""
    state = compute_target_state(
        heading_deg=0.0,
        shooter_xy=(0.0, 0.0),
        target_xy=(0.0, 5.0),  # 90 degrees left
        velocity_xy=(0.0, 0.0),
        # Turret rotated 2.25 rotations from center -> 90 degrees
        turret_position=2.25, center_position=0.0, deg_per_rotation=40.0,
    )
    assert abs(state.error_deg) < 0.1


def test_distance_calculation():
    """Distance should be Euclidean distance from shooter to target."""
    state = compute_target_state(
        heading_deg=0.0,
        shooter_xy=(3.0, 0.0),
        target_xy=(3.0, 4.0),
        velocity_xy=(0.0, 0.0),
        turret_position=0.0, center_position=0.0, deg_per_rotation=40.0,
    )
    assert abs(state.distance_m - 4.0) < 0.01


def test_error_wraps_around_180():
    """Error wraps to [-180, 180] range."""
    state = compute_target_state(
        heading_deg=170.0,  # facing almost -X
        shooter_xy=(0.0, 0.0),
        target_xy=(-5.0, -1.0),
        velocity_xy=(0.0, 0.0),
        turret_position=0.0, center_position=0.0, deg_per_rotation=40.0,
    )
    assert -180 <= state.error_deg <= 180


def test_closing_speed_approaching():
    """Robot moving toward target -> positive closing speed."""
    state = compute_target_state(
        heading_deg=0.0,
        shooter_xy=(0.0, 0.0),
        target_xy=(5.0, 0.0),
        velocity_xy=(2.0, 0.0),
        turret_position=0.0, center_position=0.0, deg_per_rotation=40.0,
    )
    assert state.closing_speed_mps > 0


def test_closing_speed_moving_away():
    """Robot moving away from target -> negative closing speed."""
    state = compute_target_state(
        heading_deg=0.0,
        shooter_xy=(0.0, 0.0),
        target_xy=(5.0, 0.0),
        velocity_xy=(-2.0, 0.0),
        turret_position=0.0, center_position=0.0, deg_per_rotation=40.0,
    )
    assert state.closing_speed_mps < 0


def test_closing_speed_perpendicular():
    """Robot moving perpendicular to target -> ~zero closing speed."""
    state = compute_target_state(
        heading_deg=0.0,
        shooter_xy=(0.0, 0.0),
        target_xy=(5.0, 0.0),
        velocity_xy=(0.0, 2.0),
        turret_position=0.0, center_position=0.0, deg_per_rotation=40.0,
    )
    assert abs(state.closing_speed_mps) < 0.01


def test_zero_velocity_zero_closing_speed():
    """Stationary robot -> zero closing speed."""
    state = compute_target_state(
        heading_deg=0.0,
        shooter_xy=(0.0, 0.0),
        target_xy=(5.0, 0.0),
        velocity_xy=(0.0, 0.0),
        turret_position=0.0, center_position=0.0, deg_per_rotation=40.0,
    )
    assert state.closing_speed_mps == 0.0


def test_shooter_offset_changes_distance():
    """Shooter offset shifts the origin, changing the measured distance."""
    # Shooter at (1, 0) -> 4m to target at (5, 0), not 5m from robot center
    state = compute_target_state(
        heading_deg=0.0,
        shooter_xy=(1.0, 0.0),
        target_xy=(5.0, 0.0),
        velocity_xy=(0.0, 0.0),
        turret_position=0.0, center_position=0.0, deg_per_rotation=40.0,
    )
    assert abs(state.distance_m - 4.0) < 0.01


# --- compute_range_state tests ---

def test_range_state_distance():
    """Distance is Euclidean from origin to target."""
    distance, _ = compute_range_state((0.0, 0.0), (3.0, 4.0), (0.0, 0.0))
    assert abs(distance - 5.0) < 0.01


def test_range_state_closing_speed():
    """Closing speed is positive when moving toward target."""
    _, closing = compute_range_state((0.0, 0.0), (5.0, 0.0), (2.0, 0.0))
    assert closing > 0


def test_range_state_retreating():
    """Closing speed is negative when moving away."""
    _, closing = compute_range_state((0.0, 0.0), (5.0, 0.0), (-2.0, 0.0))
    assert closing < 0
