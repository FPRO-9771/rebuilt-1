"""
Distance compensation for closing speed.
Adjusts the lookup distance based on how fast the robot is
approaching or retreating from the target.

When closing, the ball needs less energy because the target will
be closer by the time the ball arrives. When retreating, it needs
more energy because the target will be farther away.

Pure math -- no subsystem dependencies, easily testable.
"""

from subsystems.shooter_lookup import get_ball_speed


def compute_corrected_distance(distance_m, closing_speed_mps):
    """Adjust lookup distance for robot closing speed.

    Uses ball flight time to estimate where the effective distance
    will be when the ball arrives at the target.

    Args:
        distance_m: raw distance to target (meters)
        closing_speed_mps: rate of closure (positive = getting closer)

    Returns:
        Corrected distance for lookup table (meters, clamped >= 0.5)
    """
    if distance_m < 0.5:
        return distance_m

    ball_speed = get_ball_speed(distance_m)
    flight_time = distance_m / ball_speed
    corrected = distance_m - closing_speed_mps * flight_time

    return max(0.5, corrected)
