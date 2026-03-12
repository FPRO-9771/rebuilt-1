"""
Velocity lead correction for auto-aim.

When the robot is moving laterally while shooting, the ball inherits
the robot's sideways velocity. By the time the ball reaches the target,
the turret needs to be aimed ahead of where the target appears now.

How far ahead depends on:
  - Robot lateral velocity (m/s)
  - Distance to target (m)
  - Ball speed at that distance (m/s, from the distance table)

The correction is purely additive -- it does not replace or interfere
with the PD controller, feedforward, or any other aiming logic.
"""

import math

from subsystems.shooter_lookup import get_ball_speed


def compute_velocity_lead(vy, distance):
    """Compute the lead angle to compensate for robot lateral movement.

    Args:
        vy: robot lateral velocity (m/s, positive = right)
        distance: distance to target (meters)

    Returns:
        (lead_deg, ball_speed) tuple:
          lead_deg: correction in degrees to ADD to tx
          ball_speed: ball speed used (m/s), for logging
    """
    if distance <= 0.5:
        return 0.0, 0.0

    ball_speed = get_ball_speed(distance)
    flight_time = distance / ball_speed
    lead_m = vy * flight_time
    lead_deg = math.degrees(math.atan2(lead_m, distance))
    return lead_deg, ball_speed
