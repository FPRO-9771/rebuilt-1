"""
Distance compensation for closing speed.
Adjusts the lookup distance based on how fast the robot is
approaching or retreating from the target.

When closing, the ball needs less energy because the target will
be closer by the time the ball arrives. When retreating, it needs
more energy because the target will be farther away.

Constants live in constants/shoot_auto_shoot.py (CON_AUTO_SHOOT).
Pure math -- no subsystem dependencies, easily testable.
"""

from subsystems.shooter_lookup import get_flight_time
from constants.shoot_auto_shoot import CON_AUTO_SHOOT


def compute_corrected_distance(distance_m, closing_speed_mps):
    """Adjust lookup distance for robot closing speed.

    Uses flight time from the distance table to estimate where
    the effective distance will be when the ball arrives.

    Args:
        distance_m: raw distance to target (meters)
        closing_speed_mps: rate of closure (positive = getting closer)

    Returns:
        Corrected distance for lookup table (meters, clamped >= min_distance)
    """
    min_dist = CON_AUTO_SHOOT["min_distance"]
    if distance_m < min_dist:
        return distance_m

    flight_time = get_flight_time(distance_m)
    if closing_speed_mps >= 0:
        gain = CON_AUTO_SHOOT["distance_correction_gain_closing"]
    else:
        gain = CON_AUTO_SHOOT["distance_correction_gain_retreating"]
    corrected = distance_m - closing_speed_mps * flight_time * gain

    return max(min_dist, corrected)
