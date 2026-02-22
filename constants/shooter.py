"""
Shooter system constants: turret, launcher, hood, and orchestrator settings.
These stay together because the shooter is one coordinated system.
"""

# =============================================================================
# TURRET CONFIGURATION
# =============================================================================
CON_TURRET = {
    "max_voltage": 4.0,         # Maximum voltage to apply
    "min_position": -0.5,       # Soft limit: leftmost rotation (rotations)
    "max_position": 0.5,        # Soft limit: rightmost rotation (rotations)
    "position_tolerance": 0.02,  # "Close enough" tolerance (rotations)
    "inverted": False,
}

# =============================================================================
# LAUNCHER CONFIGURATION
# =============================================================================
CON_LAUNCHER = {
    "max_voltage": 12.0,        # Maximum voltage to apply
    "velocity_tolerance": 2.0,  # "At speed" tolerance (rotations per second)
    "inverted": False,
}

# =============================================================================
# HOOD CONFIGURATION
# =============================================================================
CON_HOOD = {
    "max_voltage": 6.0,         # Maximum voltage to apply
    "min_position": 0.0,        # Minimum hood angle (rotations)
    "max_position": 0.25,       # Maximum hood angle (rotations)
    "position_tolerance": 0.01,  # "Close enough" tolerance (rotations)
    "inverted": False,
}

# =============================================================================
# SHOOTER SYSTEM CONFIGURATION
# =============================================================================
CON_SHOOTER = {
    "turret_p_gain": 0.3,               # Proportional gain for turret aiming (volts per degree)
    "turret_aim_inverted": False,        # Flip to True if turret tracks away from target
    "turret_alignment_tolerance": 1.5,   # Degrees of tx offset considered "aligned"

    # Per-tag offsets: corrections when aiming at the hoop via each tag.
    # tx_offset (degrees): positive = hoop is to the right of this tag
    # distance_offset (meters): positive = hoop is farther than this tag
    # All zeros to start — tune on the real robot.
    "target_tags": {
        4: {"tx_offset": 0.0, "distance_offset": 0.0},
        7: {"tx_offset": 0.0, "distance_offset": 0.0},
    },

    # Distance lookup table: (distance_m, launcher_rps, hood_position)
    # Sorted by distance — interpolated at runtime
    "distance_table": [
        (1.0, 30.0, 0.05),
        (2.0, 45.0, 0.10),
        (3.0, 55.0, 0.15),
        (4.0, 65.0, 0.20),
        (5.0, 75.0, 0.24),
    ],
}
