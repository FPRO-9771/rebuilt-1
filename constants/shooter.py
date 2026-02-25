"""
Shooter system constants: turret, launcher, hood, and orchestrator settings.
These stay together because the shooter is one coordinated system.
"""

# =============================================================================
# TURRET CONFIGURATION
# =============================================================================
CON_TURRET = {
    "max_voltage": 4.0,         # Maximum voltage to apply
    "manual_speed_factor": 0.10, # Manual mode runs at 20% of max voltage
    "min_position": -4.2,       # Soft limit: leftmost rotation (rotations)
    "max_position": 0,        # Soft limit: rightmost rotation (rotations)
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

    # Slot 0 gains for closed-loop velocity control
    # Tune feedforward (kS, kV) first, then add kP to close remaining error
    "slot0_kP": 0.3,
    "slot0_kI": 0.0,
    "slot0_kD": 0.0,
    "slot0_kS": 0.0,            # Static friction (volts to start moving)
    "slot0_kV": 0.12,           # Velocity feedforward (volts per RPS)
    "slot0_kA": 0.0,            # Acceleration feedforward (volts per RPS/s)
    "slot0_kG": 0.0,            # Gravity feedforward (volts to hold against gravity)
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

    # Slot 0 gains for closed-loop position control
    # NEEDS TUNING -- all gains low to prevent vibration
    # Tune kP up first, then add kS if friction is a problem
    "slot0_kP": 1.0,
    "slot0_kI": 0.0,
    "slot0_kD": 0.0,
    "slot0_kS": 0.0,            # Static friction (volts to start moving)
    "slot0_kV": 0.0,            # Velocity feedforward (volts per RPS)
    "slot0_kA": 0.0,            # Acceleration feedforward (volts per RPS/s)
    "slot0_kG": 0.0,            # Gravity feedforward (volts to hold against gravity)
}

# =============================================================================
# SHOOTER SYSTEM CONFIGURATION
# =============================================================================
CON_SHOOTER = {
    "turret_p_gain": 0.04,               # Proportional gain (volts per degree) -- drives toward target
    "turret_d_gain": 0.02,               # Derivative gain (volts per degree/cycle) -- brakes oscillation
    "turret_aim_inverted": False,        # Positive tx (target right) -> positive voltage (turret right)
    "turret_alignment_tolerance": 1.5,   # Degrees of tx offset considered "aligned"
    "turret_max_auto_voltage": 0.7,     # Max voltage during auto-aim (keep low for testing)

    # Per-tag offsets: corrections when aiming at the hoop via each tag.
    # tx_offset (degrees): positive = hoop is to the right of this tag
    # distance_offset (meters): positive = hoop is farther than this tag
    # All zeros to start — tune on the real robot.
    "target_tags": {
        8:  {"tx_offset": 0.0, "distance_offset": 0.0},
        9:  {"tx_offset": 0.0, "distance_offset": 0.0},
        10: {"tx_offset": 0.0, "distance_offset": 0.0},
        11: {"tx_offset": 0.0, "distance_offset": 0.0},
    },

    # Distance lookup table: (distance_m, launcher_rps, hood_position)
    # Sorted by distance — interpolated at runtime
    "distance_table": [
        (1.0, 60.0, 0.05),
        (2.0, 70.0, 0.10),
        (3.0, 80.0, 0.15),
        (4.0, 90.0, 0.20),
        (5.0, 100.0, 0.24),
    ],
}
