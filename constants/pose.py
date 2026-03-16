"""
Robot pose configuration.
Turret geometry constants for converting between motor rotations and field angles.
"""

# =============================================================================
# TURRET GEOMETRY
# =============================================================================
# How the turret motor maps to turret heading.
# center_position: motor rotations when turret points forward (robot heading)
# degrees_per_rotation: turret degrees per motor rotation (360 / gear ratio)
CON_POSE = {
    "center_position": 4.5,
    "degrees_per_rotation": 40.0,

    # Shooter position relative to robot center (meters).
    # WPILib robot frame: +X = forward, +Y = left.
    # Our shooter is 6 inches behind center, 8 inches to the right.
    "shooter_offset_x": -0.1524,   # 6 in back  (-X)
    "shooter_offset_y": -0.2032,   # 8 in right (-Y)
}
