"""
Shooter field position.
Converts the robot-relative shooter offset to field coordinates
using the robot's current heading.

The shooter is not at the robot center -- it is offset to one corner.
Because the robot can rotate, the offset direction changes in field
coordinates. This function handles that rotation.

Used by both turret aiming and launcher power control so they
measure from the actual shooter position, not robot center.
"""

import math


def get_shooter_field_position(pose, offset_x, offset_y):
    """Convert a robot-relative offset to field coordinates.

    Args:
        pose: robot Pose2d (has .X(), .Y(), .rotation().radians())
        offset_x: forward offset from robot center (meters, +X = forward)
        offset_y: left offset from robot center (meters, +Y = left)

    Returns:
        (field_x, field_y) tuple in meters
    """
    heading_rad = pose.rotation().radians()
    cos_h = math.cos(heading_rad)
    sin_h = math.sin(heading_rad)

    field_x = pose.X() + offset_x * cos_h - offset_y * sin_h
    field_y = pose.Y() + offset_x * sin_h + offset_y * cos_h
    return (field_x, field_y)
