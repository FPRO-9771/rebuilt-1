"""
Tests for parallax correction.
Pure math -- no hardware or mock dependencies needed.
"""

import math

from calculations.parallax import compute_parallax_correction


def test_no_offset_returns_zero():
    """No tag offset means no correction needed."""
    correction = compute_parallax_correction(
        tx_deg=10.0, distance=3.0,
        tag_y_offset_m=0.0, tag_x_offset_m=0.0,
    )
    assert correction == 0.0


def test_too_close_returns_zero():
    """Very short distance returns zero to avoid divide-by-zero."""
    correction = compute_parallax_correction(
        tx_deg=5.0, distance=0.2,
        tag_y_offset_m=-0.6, tag_x_offset_m=0.0,
    )
    assert correction == 0.0


def test_centered_tag_forward_offset_no_correction():
    """Tag directly ahead (tx=0) with only forward offset -- no lateral shift.

    When the robot is directly in front of the tag, the Hub is straight
    behind it. The correction should be near zero.
    """
    correction = compute_parallax_correction(
        tx_deg=0.0, distance=3.0,
        tag_y_offset_m=-0.6, tag_x_offset_m=0.0,
    )
    # Hub is directly behind the tag on the same line -- correction ~0
    assert abs(correction) < 0.5


def test_robot_right_of_center_tag_corrects_toward_center():
    """Robot to the right of a center tag -- Hub is more centered.

    Tag 10 is 0.6m closer to wall than Hub, no lateral offset.
    Robot sees tag to its left (tx=-15). The Hub is behind the tag
    (deeper into field), so from the robot's off-center position
    the Hub is closer to straight ahead. Correction is positive
    (aim right, toward center).
    """
    correction = compute_parallax_correction(
        tx_deg=-15.0, distance=3.0,
        tag_y_offset_m=-0.6, tag_x_offset_m=0.0,
    )
    assert correction > 0


def test_robot_left_of_center_tag_corrects_toward_center():
    """Robot to the left of a center tag -- Hub is more centered.

    Mirror of previous test. tx=+15 means tag is to the right.
    Hub behind tag is closer to straight ahead, so correction
    is negative (aim left, toward center).
    """
    correction = compute_parallax_correction(
        tx_deg=15.0, distance=3.0,
        tag_y_offset_m=-0.6, tag_x_offset_m=0.0,
    )
    assert correction < 0


def test_lateral_offset_tag_shifts_aim():
    """Tag to the left of Hub (tag_x_offset_m=-0.4) -- Hub is to the right.

    When looking straight at the tag (tx=0), the Hub is to the right,
    so correction should be positive.
    """
    correction = compute_parallax_correction(
        tx_deg=0.0, distance=3.0,
        tag_y_offset_m=-0.4, tag_x_offset_m=-0.4,
    )
    # Hub is to the right of tag -> positive correction
    assert correction > 0


def test_correction_decreases_with_distance():
    """Parallax shrinks at longer range -- same offset matters less."""
    close = compute_parallax_correction(
        tx_deg=10.0, distance=2.0,
        tag_y_offset_m=-0.6, tag_x_offset_m=0.0,
    )
    far = compute_parallax_correction(
        tx_deg=10.0, distance=6.0,
        tag_y_offset_m=-0.6, tag_x_offset_m=0.0,
    )
    assert abs(close) > abs(far)


def test_symmetry():
    """Left and right viewing angles produce opposite corrections."""
    left = compute_parallax_correction(
        tx_deg=-10.0, distance=3.0,
        tag_y_offset_m=-0.6, tag_x_offset_m=0.0,
    )
    right = compute_parallax_correction(
        tx_deg=10.0, distance=3.0,
        tag_y_offset_m=-0.6, tag_x_offset_m=0.0,
    )
    # Should be equal magnitude, opposite sign
    assert abs(left + right) < 0.01
