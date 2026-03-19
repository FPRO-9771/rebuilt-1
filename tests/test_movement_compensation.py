"""
Tests for movement compensation calculations.
Pure math -- no hardware dependencies.
"""

import math

from calculations.movement_compensation import compute_movement_correction
from tests.conftest import TEST_CON_SHOOTER

# Bearing straight ahead in field frame (hub is directly in front)
BEARING_FORWARD = 0.0
# Bearing 90 degrees left (hub is to the left)
BEARING_LEFT = math.pi / 2


def test_zero_velocity_zero_corrections():
    """No robot movement -> no corrections."""
    tracking, lead = compute_movement_correction(
        0.0, 0.0, 3.0, BEARING_FORWARD, TEST_CON_SHOOTER)
    assert tracking == 0.0
    assert lead == 0.0


def test_lateral_velocity_produces_tracking_correction():
    """Lateral velocity produces a tracking correction."""
    tracking, _ = compute_movement_correction(
        0.0, 2.0, 3.0, BEARING_FORWARD, TEST_CON_SHOOTER)
    expected = 2.0 * TEST_CON_SHOOTER["turret_velocity_ff_gain"]
    assert tracking == expected


def test_tracking_direction_matches_velocity():
    """Positive vy -> positive tracking correction, negative -> negative."""
    pos_tracking, _ = compute_movement_correction(
        0.0, 1.0, 3.0, BEARING_FORWARD, TEST_CON_SHOOTER)
    neg_tracking, _ = compute_movement_correction(
        0.0, -1.0, 3.0, BEARING_FORWARD, TEST_CON_SHOOTER)
    assert pos_tracking > 0
    assert neg_tracking < 0


def test_lead_correction_with_velocity_lead_enabled():
    """Lead correction is nonzero when velocity_lead_enabled and moving."""
    config = {**TEST_CON_SHOOTER, "velocity_lead_enabled": True}
    # Moving laterally (vy) with hub straight ahead produces tangential velocity
    _, lead = compute_movement_correction(
        0.0, 2.0, 3.0, BEARING_FORWARD, config)
    assert lead != 0.0


def test_lead_correction_disabled():
    """Lead correction is zero when velocity_lead_enabled is False."""
    config = {**TEST_CON_SHOOTER, "velocity_lead_enabled": False}
    _, lead = compute_movement_correction(
        0.0, 2.0, 3.0, BEARING_FORWARD, config)
    assert lead == 0.0


def test_lead_correction_zero_at_short_distance():
    """Lead correction is zero when distance is too short."""
    config = {**TEST_CON_SHOOTER, "velocity_lead_enabled": True}
    _, lead = compute_movement_correction(
        0.0, 2.0, 0.3, BEARING_FORWARD, config)
    assert lead == 0.0


def test_forward_velocity_does_not_affect_tracking():
    """Forward velocity (vx) does not affect tracking correction."""
    tracking_with_vx, _ = compute_movement_correction(
        3.0, 0.0, 3.0, BEARING_FORWARD, TEST_CON_SHOOTER)
    tracking_without, _ = compute_movement_correction(
        0.0, 0.0, 3.0, BEARING_FORWARD, TEST_CON_SHOOTER)
    assert tracking_with_vx == tracking_without


def test_forward_velocity_produces_lead_when_hub_to_side():
    """vx produces lead correction when hub is to the side (tangential)."""
    config = {**TEST_CON_SHOOTER, "velocity_lead_enabled": True}
    # Hub is 90 deg left; driving forward (vx) is tangential to hub line
    _, lead = compute_movement_correction(
        2.0, 0.0, 3.0, BEARING_LEFT, config)
    assert lead != 0.0


def test_radial_velocity_produces_no_lead():
    """Velocity directly toward the hub produces no lead correction."""
    config = {**TEST_CON_SHOOTER, "velocity_lead_enabled": True}
    # Hub is straight ahead (bearing=0); driving forward (vx) is radial
    _, lead = compute_movement_correction(
        2.0, 0.0, 3.0, BEARING_FORWARD, config)
    assert abs(lead) < 0.01  # Essentially zero (floating point)
