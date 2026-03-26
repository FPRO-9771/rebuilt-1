"""
Shooter lookup table.
Converts distance to shooter settings via linear interpolation.

Table format: (distance_m, launcher_rps, flight_time_s)
"""

from constants.shoot_distance_table import CON_DISTANCE_TABLE


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
    """Look up launcher RPS for a given distance.

    Returns:
        launcher_rps (float)
    """
    table = CON_DISTANCE_TABLE["distance_table"]
    return _lerp(table, distance, 1)


def get_flight_time(distance):
    """Look up ball flight time (seconds) for a given distance.

    Used by movement compensation to determine how far ahead to aim
    (angle compensation) and how much to adjust launcher power
    (distance compensation).

    Measure by timing the ball from launch to landing in the Hub
    at each distance in the table.

    Returns:
        flight_time_s (float)
    """
    table = CON_DISTANCE_TABLE["distance_table"]
    return _lerp(table, distance, 2)
