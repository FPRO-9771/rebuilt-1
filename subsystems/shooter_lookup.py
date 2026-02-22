"""
Shooter lookup table.
Converts distance to (launcher_rps, hood_position) via linear interpolation.
"""

from typing import Tuple
from constants import CON_SHOOTER


def get_shooter_settings(distance: float) -> Tuple[float, float]:
    """
    Look up launcher RPS and hood position for a given distance.

    Uses linear interpolation between entries in CON_SHOOTER["distance_table"].
    Clamps to nearest entry when outside table range.

    Args:
        distance: Distance to target in meters

    Returns:
        (launcher_rps, hood_position) tuple
    """
    table = CON_SHOOTER["distance_table"]

    # Clamp below minimum distance
    if distance <= table[0][0]:
        return (table[0][1], table[0][2])

    # Clamp above maximum distance
    if distance >= table[-1][0]:
        return (table[-1][1], table[-1][2])

    # Find the two entries to interpolate between
    for i in range(len(table) - 1):
        d_low, rps_low, hood_low = table[i]
        d_high, rps_high, hood_high = table[i + 1]

        if d_low <= distance <= d_high:
            # Linear interpolation factor
            t = (distance - d_low) / (d_high - d_low)
            rps = rps_low + t * (rps_high - rps_low)
            hood = hood_low + t * (hood_high - hood_low)
            return (rps, hood)

    # Should never reach here, but return last entry as fallback
    return (table[-1][1], table[-1][2])
