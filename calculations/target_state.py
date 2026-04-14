"""
Target state calculation.
Given shooter position, heading, velocity, and turret position, compute
the full geometric relationship to the Hub target.

Used by CoordinateAim (turret aiming). ShootContext is used by all
shooter commands for shared pose + distance data.

Pure math -- no subsystem dependencies, easily testable.
"""

import math
from collections import namedtuple

TargetState = namedtuple("TargetState", [
    "error_deg",         # turret angular error to target (degrees)
    "distance_m",        # distance from shooter to target (meters)
    "closing_speed_mps", # rate of distance change (positive = closing)
    "bearing_deg",       # angle from robot front to target (degrees, + = left)
])

ShootContext = namedtuple("ShootContext", [
    "corrected_distance",  # velocity-adjusted distance for lookup table (meters)
    "raw_distance",        # raw shooter-to-target distance (meters)
    "closing_speed_mps",   # rate of closure (positive = closing)
    "pose_x",              # robot X position (meters)
    "pose_y",              # robot Y position (meters)
    "heading_deg",         # robot heading (degrees)
    "shooter_x",           # shooter field X (meters)
    "shooter_y",           # shooter field Y (meters)
    "target_x",            # target X (meters) -- Hub or nearest corner
    "target_y",            # target Y (meters) -- Hub or nearest corner
    "vx",                  # robot forward velocity (m/s)
    "vy",                  # robot lateral velocity (m/s)
    "target_mode",         # "hub" or "corner" -- which target the turret is chasing
], defaults=["hub"])


def compute_range_state(origin_xy, target_xy, velocity_xy):
    """Compute distance and closing speed from an origin to a target.

    Lighter than compute_target_state -- no turret angle calculation.
    Used by both turret aiming and launcher power control.

    Args:
        origin_xy: (x, y) position to measure from (meters, field coords)
        target_xy: (x, y) target position (meters, field coords)
        velocity_xy: (vx, vy) velocity in m/s (field-relative)

    Returns:
        (distance_m, closing_speed_mps) tuple
    """
    dx = target_xy[0] - origin_xy[0]
    dy = target_xy[1] - origin_xy[1]
    distance_m = math.hypot(dx, dy)

    closing_speed_mps = 0.0
    if distance_m > 0.1:
        vx, vy = velocity_xy
        closing_speed_mps = (vx * dx + vy * dy) / distance_m

    return distance_m, closing_speed_mps


def compute_target_state(heading_deg, shooter_xy, target_xy,
                         velocity_xy, turret_position,
                         center_position, deg_per_rotation):
    """Compute the turret error, distance, and closing speed to a target.

    All inputs are scalars or tuples -- no WPILib objects needed.

    Args:
        heading_deg: robot heading in degrees
        shooter_xy: (x, y) shooter field position (meters)
        target_xy: (x, y) Hub position (meters)
        velocity_xy: (vx, vy) robot velocity in m/s (field-relative)
        turret_position: current turret motor position (rotations)
        center_position: motor rotations when turret faces forward
        deg_per_rotation: turret degrees per motor rotation

    Returns:
        TargetState namedtuple with error_deg, distance_m,
        closing_speed_mps, bearing_deg
    """
    # Distance and closing speed
    distance_m, closing_speed_mps = compute_range_state(
        shooter_xy, target_xy, velocity_xy)

    # Angle from shooter to target in field coordinates
    dx = target_xy[0] - shooter_xy[0]
    dy = target_xy[1] - shooter_xy[1]
    target_field_deg = math.degrees(math.atan2(dy, dx))

    # Desired turret angle relative to robot forward
    desired_turret_deg = target_field_deg - heading_deg

    # Current turret angle relative to robot forward
    current_turret_deg = (center_position - turret_position) * deg_per_rotation

    # Error: how far the turret needs to rotate
    error_deg = desired_turret_deg - current_turret_deg
    # Wrap to [-180, 180]
    while error_deg > 180:
        error_deg -= 360
    while error_deg < -180:
        error_deg += 360

    return TargetState(
        error_deg=error_deg,
        distance_m=distance_m,
        closing_speed_mps=closing_speed_mps,
        bearing_deg=desired_turret_deg,
    )
