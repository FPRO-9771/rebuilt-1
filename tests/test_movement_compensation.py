"""
Tests for angle compensation (velocity lead) calculations.
Pure math -- no hardware dependencies.
"""

import math

from calculations.movement_compensation import compute_angle_compensation

# Bearing straight ahead in field frame (hub is directly in front)
BEARING_FORWARD = 0.0
# Bearing 90 degrees left (hub is to the left)
BEARING_LEFT = math.pi / 2


def test_zero_velocity_zero_correction():
    """No robot movement -> no correction."""
    lead = compute_angle_compensation(0.0, 0.0, 3.0, BEARING_FORWARD)
    assert lead == 0.0


def test_lateral_velocity_produces_lead():
    """Lateral velocity with hub ahead produces lead correction."""
    lead = compute_angle_compensation(0.0, 2.0, 3.0, BEARING_FORWARD)
    assert lead != 0.0


def test_lead_direction_matches_velocity():
    """Positive vy (moving left) -> negative lead (aim right to compensate)."""
    pos_lead = compute_angle_compensation(0.0, 1.0, 3.0, BEARING_FORWARD)
    neg_lead = compute_angle_compensation(0.0, -1.0, 3.0, BEARING_FORWARD)
    assert pos_lead < 0
    assert neg_lead > 0


def test_lead_disabled(monkeypatch):
    """Lead correction is zero when velocity_lead_enabled is False."""
    disabled = {"velocity_lead_enabled": False, "min_distance": 0.5}
    monkeypatch.setattr(
        "calculations.movement_compensation.CON_AUTO_SHOOT", disabled)
    lead = compute_angle_compensation(0.0, 2.0, 3.0, BEARING_FORWARD)
    assert lead == 0.0


def test_lead_zero_at_short_distance():
    """Lead correction is zero when distance is too short."""
    lead = compute_angle_compensation(0.0, 2.0, 0.3, BEARING_FORWARD)
    assert lead == 0.0


def test_forward_velocity_produces_lead_when_hub_to_side():
    """vx produces lead correction when hub is to the side (tangential)."""
    # Hub is 90 deg left; driving forward (vx) is tangential to hub line
    lead = compute_angle_compensation(2.0, 0.0, 3.0, BEARING_LEFT)
    assert lead != 0.0


def test_radial_velocity_produces_no_lead():
    """Velocity directly toward the hub produces no lead correction."""
    # Hub is straight ahead (bearing=0); driving forward (vx) is radial
    lead = compute_angle_compensation(2.0, 0.0, 3.0, BEARING_FORWARD)
    assert abs(lead) < 0.01  # Essentially zero (floating point)
