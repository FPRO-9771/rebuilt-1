"""
Angle compensation for auto-aim.
Computes how far ahead to aim the turret when the robot is moving.

Uses the velocity lead module to decompose robot velocity into
tangential and radial components relative to the Hub. Only the
tangential component causes lateral miss -- the radial component
is handled by distance compensation (separate module).

Returns a single value: lead angle in degrees, to be added to
the turret error. This is the ONLY place that adjusts turret
angle for robot movement.

Constants live in constants/shoot_auto_shoot.py (CON_AUTO_SHOOT).
Pure math -- no subsystem dependencies, easily testable.
"""

from calculations.velocity_lead import compute_velocity_lead
from constants.shoot_auto_shoot import CON_AUTO_SHOOT


def compute_angle_compensation(vx, vy, distance_m, bearing_rad):
    """Compute the lead angle to add to turret error for robot movement.

    Args:
        vx: robot X velocity (m/s, field-relative)
        vy: robot Y velocity (m/s, field-relative)
        distance_m: distance to target (meters)
        bearing_rad: angle from shooter to hub (radians, field frame)

    Returns:
        lead_deg: correction in degrees to ADD to the turret error.
        Zero when stationary, disabled, or at point-blank range.
    """
    min_dist = CON_AUTO_SHOOT["min_distance"]
    if not CON_AUTO_SHOOT["velocity_lead_enabled"] or distance_m <= min_dist:
        return 0.0

    lead_deg = compute_velocity_lead(vx, vy, distance_m, bearing_rad)
    gain = CON_AUTO_SHOOT["velocity_lead_gain"]
    return lead_deg * gain
