"""
Shooter lookup table.
Converts distance to shooter settings via linear interpolation.

Table format: (distance_m, launcher_rps, hood_position, ball_speed_mps)
"""

from constants import CON_SHOOTER


def _lerp(table, distance, col):
    """Interpolate a single column from the distance table."""
    if distance <= table[0][0]:
        return table[0][col]
    if distance >= table[-1][0]:
        return table[-1][col]

    for i in range(len(table) - 1):
        if table[i][0] <= distance <= table[i + 1][0]:
            t = (distance - table[i][0]) / (table[i + 1][0] - table[i][0])
            return table[i][col] + t * (table[i + 1][col] - table[i][col])

    return table[-1][col]


def get_shooter_settings(distance):
    """Look up launcher RPS and hood position for a given distance.

    Returns:
        (launcher_rps, hood_position) tuple
    """
    table = CON_SHOOTER["distance_table"]
    return (_lerp(table, distance, 1), _lerp(table, distance, 2))


def get_ball_speed(distance):
    """Look up ball speed (m/s) for a given distance.

    Used by auto-aim to compute how long the ball is in the air,
    which determines how far ahead to lead the target while moving.

    Returns:
        ball_speed_mps (float)
    """
    table = CON_SHOOTER["distance_table"]
    return _lerp(table, distance, 3)
