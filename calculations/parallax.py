"""
Parallax correction for auto-aim.

AprilTags are not at the Hub center -- they are mounted closer to the
driver station wall and sometimes off to the side. When the robot views
a tag from an angle, "aiming at the tag" is not the same as "aiming at
the Hub center". The angular error depends on where the robot is.

This module computes a correction (in degrees) to ADD to the raw tx
value so that the turret aims at the Hub center instead of the tag.

Tag offsets use field-relative coordinates:
  tag_y_offset_m: negative = tag is closer to driver station than Hub
  tag_x_offset_m: positive = tag is to the right of Hub center

The correction is purely additive -- it does not replace or interfere
with the PD controller, deadband comp, or any other aiming logic.
"""

import math


def compute_parallax_correction(tx_deg, distance, tag_y_offset_m,
                                tag_x_offset_m):
    """Compute the angle correction from tag to Hub center.

    Args:
        tx_deg: raw tx from Limelight (degrees, positive = target right)
        distance: distance to tag (meters)
        tag_y_offset_m: tag Y offset from Hub (negative = closer to wall)
        tag_x_offset_m: tag X offset from Hub (positive = right of Hub)

    Returns:
        correction in degrees to ADD to tx (positive = aim more right)
    """
    # No offset -- no correction needed
    if tag_y_offset_m == 0.0 and tag_x_offset_m == 0.0:
        return 0.0

    # Too close for a meaningful correction -- avoid divide-by-zero
    if distance < 0.3:
        return 0.0

    tx_rad = math.radians(tx_deg)

    # Tag position relative to robot (robot at origin, Y = forward)
    tag_x = distance * math.sin(tx_rad)
    tag_y = distance * math.cos(tx_rad)

    # Hub center relative to robot:
    # Offset describes where the TAG is relative to the Hub,
    # so Hub = tag_position - offset.
    hub_x = tag_x - tag_x_offset_m
    hub_y = tag_y - tag_y_offset_m

    # Angle from robot to Hub center
    hub_angle_deg = math.degrees(math.atan2(hub_x, hub_y))

    # Correction = how much to shift tx
    return hub_angle_deg - tx_deg
