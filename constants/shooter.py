"""
Shooter system constants: turret, launcher, hood, and orchestrator settings.
These stay together because the shooter is one coordinated system.
"""

# =============================================================================
# TURRET CONFIGURATION
# =============================================================================
CON_TURRET = {
    "max_voltage": 4.0,         # Maximum voltage to apply
    "manual_speed_factor": 0.20, # Manual mode runs at 20% of max voltage
    "min_position": 0,       # Soft limit: leftmost rotation (rotations)
    "max_position": 9.5,        # Soft limit: rightmost rotation (rotations)
    "position_tolerance": 0.02,  # "Close enough" tolerance (rotations)
    "inverted": False,
    "search_voltage": 0.5,      # Voltage during FindTarget sweep (tune on robot)
    "search_brake_voltage": 3.0, # Brake voltage when sweep hits a soft limit
    "search_brake_cycles": 5,   # How many cycles to brake at a soft limit before reversing
}

# =============================================================================
# TURRET MINION CONFIGURATION (alternative to Kraken -- uses TalonFXS)
# To switch: flip wired flags in ids.py and swap Turret/TurretMinion in
# robot_container.py.  All voltages and limits need re-tuning on real hardware.
# =============================================================================
CON_TURRET_MINION = {
    "max_voltage": 3.0,         # Safety cap -- tune down once moving
    "manual_speed_factor": 0.50, # Manual mode: 1.0 * 0.50 = 0.50V
    "min_position": 0,       # Soft limit: leftmost rotation (rotations)
    "max_position": 9,        # Soft limit: rightmost rotation (rotations)
    "position_tolerance": 0.02,  # "Close enough" tolerance (rotations)
    "inverted": False,           # Positive = left (unconfirmed -- flip if reversed)
    "brake": True,               # Brake on neutral -- holds turret steady
    "search_voltage": 0.10,     # Voltage during FindTarget sweep
    "search_brake_voltage": 0.30, # Brake voltage when sweep hits a soft limit
    "search_brake_cycles": 5,   # How many cycles to brake before reversing

    # Slot 0 gains for closed-loop position hold (HoldPosition command).
    # NEEDS TUNING -- start conservative to avoid oscillation.
    "slot0_kP": 1.0,
    "slot0_kI": 0.0,
    "slot0_kD": 0.01,
    "slot0_kS": 0.1,            # Static friction (volts to start moving)
    "slot0_kV": 0.0,
    "slot0_kA": 0.0,
    "slot0_kG": 0.0,
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
    "slot0_kP": 0.4,
    "slot0_kI": 0.0,
    "slot0_kD": 0.0,
    "slot0_kS": 0.1,            # Static friction (volts to start moving)
    "slot0_kV": 0.12,           # Velocity feedforward (volts per RPS)
    "slot0_kA": 0.0,            # Acceleration feedforward (volts per RPS/s)
    "slot0_kG": 0.0,            # Gravity feedforward (volts to hold against gravity)
}

# =============================================================================
# HOOD CONFIGURATION
# =============================================================================
CON_HOOD = {
    "enabled": False,           # Hood motor not connected -- flip to True when wired
    "max_voltage": 6.0,         # Maximum voltage to apply
    "min_position": 0.0,        # Minimum hood angle (rotations)
    "max_position": 0.25,       # Maximum hood angle (rotations)
    "position_tolerance": 0.01,  # "Close enough" tolerance (rotations)
    "inverted": False,
    "brake": False,              # Brake on neutral -- holds position when idle

    # Slot 0 gains for closed-loop position control
    # NEEDS TUNING -- all gains low to prevent vibration
    # Tune kP up first, then add kS if friction is a problem
    "slot0_kP": 1.0,
    "slot0_kI": 0.0,
    "slot0_kD": 0.01,
    "slot0_kS": 0.1,            # Static friction (volts to start moving)
    "slot0_kV": 0.0,            # Velocity feedforward (volts per RPS)
    "slot0_kA": 0.0,            # Acceleration feedforward (volts per RPS/s)
    "slot0_kG": 0.0,            # Gravity feedforward (volts to hold against gravity)
}

# =============================================================================
# SHOOTER SYSTEM CONFIGURATION
# =============================================================================
CON_SHOOTER = {
    "turret_p_gain": 0.16,               # Proportional gain (volts per degree) -- drives toward target
    "turret_d_velocity_gain": 0.03,      # Velocity damping -- light braking only (too high causes oscillation)
    "turret_aim_inverted": False,        # Positive tx (target right) -> positive voltage (turret right)
    "turret_alignment_tolerance": 1.5,   # Degrees of tx offset considered "aligned"

    "turret_max_auto_voltage": .6,     # Max voltage during auto-aim (sqrt P handles decel now)
    "turret_max_brake_voltage": 0.6,    # Brake limit -- higher than drive to stop quickly
    "turret_min_move_voltage": 0.20,    # Deadband comp -- minimum voltage to overcome static friction
    "turret_velocity_ff_gain": 0.15,     # Feedforward: volts per (m/s) of lateral robot velocity
    "turret_tx_filter_alpha": 0.85,      # EMA smoothing for tx (0=max smooth, 1=no filter)
    "velocity_lead_enabled": False,      # Enable velocity lead compensation (aim ahead while moving)
    "parallax_correction_enabled": False, # Enable parallax correction (aim at Hub center, not tag)

    # Per-tag offsets and priorities moved to constants/match.py.
    # They are now per-alliance and selected via SmartDashboard.

    # Distance lookup table: (distance_m, launcher_rps, hood_position, ball_speed_mps)
    # ball_speed_mps: estimated ball speed at this distance -- used for
    # velocity lead compensation (how far ahead to aim while moving).
    # Tune per-entry on real robot by shooting while strafing.
    # Sorted by distance -- interpolated at runtime
    "distance_table": [
        (1, 65.0, 0.05, 5.0),
        (2.0, 80.0, 0.10, 7.0),
        (3.0, 95.0, 0.15, 9.0),
    ],
}
