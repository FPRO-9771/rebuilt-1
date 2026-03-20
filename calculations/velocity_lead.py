"""
Velocity lead correction for auto-aim.

When the robot is moving while shooting, the ball inherits the robot's
velocity. By the time the ball reaches the target, the turret needs to
be aimed ahead of where the target appears now.

The correction decomposes the robot's full velocity vector (vx, vy) into
radial (toward/away from Hub) and tangential (perpendicular to Hub line)
components. Only the tangential component causes lateral miss -- the
radial component is handled by distance compensation.

How far ahead depends on:
  - Tangential velocity (m/s) -- perpendicular to the shooter-to-hub line
  - Distance to target (m)
  - Flight time at that distance (seconds, from the distance table)

The correction is purely additive -- it does not replace or interfere
with the PD controller or any other aiming logic.
"""

import math

from subsystems.shooter_lookup import get_flight_time
from constants.compensation import CON_COMPENSATION


def compute_velocity_lead(vx, vy, distance, bearing_rad):
    """Compute the lead angle to compensate for robot movement.

    Decomposes full velocity into radial and tangential components
    relative to the shooter-to-hub line. Uses tangential velocity
    for lead correction (radial is handled by distance compensation).

    Args:
        vx: robot forward velocity (m/s, field-relative)
        vy: robot lateral velocity (m/s, field-relative)
        distance: distance to target (meters)
        bearing_rad: angle from shooter to hub (radians, field frame)

    Returns:
        lead_deg: correction in degrees to ADD to turret error
    """
    if distance <= CON_COMPENSATION["min_distance"]:
        return 0.0

    # Unit vector from shooter toward hub
    ux = math.cos(bearing_rad)
    uy = math.sin(bearing_rad)

    # Tangential velocity: component of robot velocity perpendicular
    # to the shooter-to-hub line (cross product magnitude in 2D).
    # Positive = robot moving to the left of the hub line.
    v_tangential = -vx * uy + vy * ux

    flight_time = get_flight_time(distance)
    lead_m = v_tangential * flight_time
    lead_deg = math.degrees(math.atan2(lead_m, distance))
    return lead_deg
