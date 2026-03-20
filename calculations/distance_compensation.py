"""
Distance compensation for closing speed.
Adjusts the lookup distance based on how fast the robot is
approaching or retreating from the target.

When closing, the ball needs less energy because the target will
be closer by the time the ball arrives. When retreating, it needs
more energy because the target will be farther away.

Constants live in constants/compensation.py (CON_COMPENSATION).
Pure math -- no subsystem dependencies, easily testable.
"""

from subsystems.shooter_lookup import get_flight_time
from constants.compensation import CON_COMPENSATION


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
    min_dist = CON_COMPENSATION["min_distance"]
    if distance_m < min_dist:
        return distance_m

    flight_time = get_flight_time(distance_m)
    corrected = distance_m - closing_speed_mps * flight_time

    return max(min_dist, corrected)
