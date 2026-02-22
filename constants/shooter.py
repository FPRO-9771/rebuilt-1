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
    "target_tag_ids": [4, 7],           # AprilTag IDs on the hoop
    "turret_p_gain": 0.3,               # Proportional gain for turret aiming (volts per degree)
    "turret_alignment_tolerance": 1.5,   # Degrees of tx offset considered "aligned"
    "target_lost_timeout": 0.5,          # Seconds to hold aim after losing target

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
