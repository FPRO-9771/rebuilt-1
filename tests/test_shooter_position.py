"""
Tests for shooter field position calculation.
Pure math -- no hardware dependencies.
"""

import math

from calculations.shooter_position import get_shooter_field_position


class _FakePose:
    """Minimal pose stub for testing."""

    def __init__(self, x, y, heading_deg):
        self._x = x
        self._y = y
        self._heading_rad = math.radians(heading_deg)

    def X(self):
        return self._x

    def Y(self):
        return self._y

    def rotation(self):
        return self

    def radians(self):
        return self._heading_rad


def test_zero_offset_returns_robot_center():
    """Zero offset means shooter is at robot center."""
    pose = _FakePose(3.0, 4.0, 0.0)
    x, y = get_shooter_field_position(pose, 0.0, 0.0)
    assert abs(x - 3.0) < 0.001
    assert abs(y - 4.0) < 0.001


def test_forward_offset_facing_positive_x():
    """Robot facing +X with forward offset shifts in +X."""
    pose = _FakePose(0.0, 0.0, 0.0)
    x, y = get_shooter_field_position(pose, 1.0, 0.0)
    assert abs(x - 1.0) < 0.001
    assert abs(y - 0.0) < 0.001


def test_right_offset_facing_positive_x():
    """Robot facing +X with right offset (negative Y) shifts in -Y."""
    pose = _FakePose(0.0, 0.0, 0.0)
    x, y = get_shooter_field_position(pose, 0.0, -1.0)
    assert abs(x - 0.0) < 0.001
    assert abs(y - (-1.0)) < 0.001


def test_offset_rotates_with_heading():
    """Robot facing +Y (90 degrees): forward offset goes in +Y."""
    pose = _FakePose(0.0, 0.0, 90.0)
    x, y = get_shooter_field_position(pose, 1.0, 0.0)
    assert abs(x - 0.0) < 0.001
    assert abs(y - 1.0) < 0.001


def test_right_offset_rotated_90():
    """Robot facing +Y (90 degrees): right offset (-Y robot) goes in +X."""
    pose = _FakePose(0.0, 0.0, 90.0)
    x, y = get_shooter_field_position(pose, 0.0, -1.0)
    assert abs(x - 1.0) < 0.001
    assert abs(y - 0.0) < 0.001


def test_180_rotation_flips_offsets():
    """Robot facing -X (180 degrees): forward offset goes in -X."""
    pose = _FakePose(0.0, 0.0, 180.0)
    x, y = get_shooter_field_position(pose, 1.0, 0.0)
    assert abs(x - (-1.0)) < 0.001
    assert abs(y - 0.0) < 0.001


def test_combined_offset_at_45_degrees():
    """Combined offset at 45 degrees checks both axes."""
    pose = _FakePose(0.0, 0.0, 45.0)
    # Forward offset of 1.0 at 45 degrees -> (cos45, sin45)
    x, y = get_shooter_field_position(pose, 1.0, 0.0)
    expected = math.sqrt(2) / 2
    assert abs(x - expected) < 0.001
    assert abs(y - expected) < 0.001
