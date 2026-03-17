"""
Turret routing -- choose the best rotation direction given soft limits.

The turret can spin ~360 degrees (e.g. 0 to 9 rotations) but no
further. When the shortest-path rotation would hit a limit, the turret
needs to go the long way around.

Motor-to-angle sign convention: positive error_deg (CCW/left) requires
NEGATIVE motor rotation. So error_rot = -error_deg / deg_per_rotation.
See docs/architecture/auto-aim.md "Turret starting position" for why.

Pure math -- no subsystem dependencies, easily testable.
"""


def choose_rotation_direction(current_pos, error_deg, min_pos, max_pos,
                              deg_per_rotation):
    """Pick the best rotation direction to reach the target without hitting limits.

    Args:
        current_pos: current turret position (rotations)
        error_deg: desired rotation in degrees (positive = CCW/left)
        min_pos: soft limit minimum (rotations)
        max_pos: soft limit maximum (rotations)
        deg_per_rotation: turret degrees per motor rotation

    Returns:
        adjusted_error_deg: error with direction that avoids limits.
        Same magnitude as input if shortest path works; reversed if not.
    """
    if deg_per_rotation == 0:
        return error_deg

    # Convert error to rotations (negated: positive angle = negative motor)
    error_rot = -error_deg / deg_per_rotation

    # Target position if we follow the shortest path
    target_pos = current_pos + error_rot

    # Shortest path is within limits -- use it
    if min_pos <= target_pos <= max_pos:
        return error_deg

    # Shortest path hits a limit -- try the long way around
    if error_deg > 0:
        reverse_error_deg = error_deg - 360
    else:
        reverse_error_deg = error_deg + 360

    reverse_rot = -reverse_error_deg / deg_per_rotation
    reverse_target = current_pos + reverse_rot

    # Long way is within limits -- use it
    if min_pos <= reverse_target <= max_pos:
        return reverse_error_deg

    # Both directions blocked -- go toward whichever limit is closer to target
    # Clamp to the nearer limit for best effort
    if abs(target_pos - max_pos) < abs(target_pos - min_pos):
        clamped_rot = max_pos - current_pos
    else:
        clamped_rot = min_pos - current_pos

    return -clamped_rot * deg_per_rotation
