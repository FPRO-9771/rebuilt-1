"""
Robot pose configuration.
Turret geometry constants for converting between motor rotations and field angles.
"""

# =============================================================================
# TURRET GEOMETRY
# =============================================================================
# How the turret motor maps to turret heading.
# start_angle_deg: physical turret angle at power-on, measured from robot forward
#   0 = forward, 90 = right, 180 = backward, 270 = left
# degrees_per_rotation: turret degrees per motor rotation (360 / gear ratio)
# center_position: motor position where turret faces forward.
#   Negative because start_angle_deg is CW-positive but motor-negative = turret-left.
#   See docs/architecture/auto-aim.md "Turret starting position" for full derivation.
_START_ANGLE_DEG = 158     # ..
_DEG_PER_ROT = 10.8          # 360 / 33.333 gear ratio

CON_POSE = {
    "start_angle_deg": _START_ANGLE_DEG,
    "degrees_per_rotation": _DEG_PER_ROT,
    "center_position": -_START_ANGLE_DEG / _DEG_PER_ROT,  # -1.125

    # Shooter position relative to robot center (meters).
    # WPILib robot frame: +X = forward, +Y = left.
    # Our shooter is 6 inches behind center, 8 inches to the right.
    "shooter_offset_x": -0.1524,   # 6 in back  (-X)
    "shooter_offset_y": -0.2032,   # 8 in right (-Y)
}
