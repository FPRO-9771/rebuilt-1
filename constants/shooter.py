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
    "manual_exponent": 2.0,     # Joystick response curve (1.0=linear, 2.0=squared, 3.0=cubed)
    "min_position": 0,       # Soft limit: leftmost rotation (rotations)
    "max_position": 9,        # Soft limit: rightmost rotation (rotations)
    "position_tolerance": 0.02,  # "Close enough" tolerance (rotations)
    "inverted": False,           # Positive = left (unconfirmed -- flip if reversed)
    "brake": True,               # Brake on neutral -- holds turret steady
    "search_voltage": 0.10,     # Voltage during FindTarget sweep
    "search_brake_voltage": 0.30, # Brake voltage when sweep hits a soft limit
    "search_brake_cycles": 5,   # How many cycles to brake before reversing
    "soft_limit_ramp": 0.5,     # Rotations from soft limit where voltage starts ramping down

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
    "velocity_tolerance": 5.0,  # "At speed" tolerance (rotations per second)
    "inverted": True,

    # Slot 0 gains for closed-loop velocity control
    # Tune feedforward (kS, kV) first, then add kP to close remaining error
    "slot0_kP": 1.0,
    "slot0_kI": 0.0,
    "slot0_kD": 0.0,
    "slot0_kS": 0.1,            # Static friction (volts to start moving)
    "slot0_kV": 0.21,           # Velocity feedforward (volts per RPS)
    "slot0_kA": 0.0,            # Acceleration feedforward (volts per RPS/s)
    "slot0_kG": 0.0,            # Gravity feedforward (volts to hold against gravity)
}

# =============================================================================
# HOOD CONFIGURATION
# =============================================================================
CON_HOOD = {
    "enabled": True,            # Hood motor connected
    "max_voltage": 6.0,         # Maximum voltage to apply
    "min_position": 0.0,        # Minimum hood angle (rotations)
    "max_position": 0.25,       # Maximum hood angle (rotations)
    "position_tolerance": 0.01,  # "Close enough" tolerance (rotations)
    "inverted": False,
    "brake": True,               # Brake on neutral -- holds position when idle

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
#4 seconds setting time at kp=0.5/ki=0.1
#2 seconds setting time at kp=0.5/ki=0.05
#next test kp=0.5 / ki=0.02


CON_SHOOTER = {
    "turret_p_gain": 0.7,                # Proportional gain (volts per degree) -- drives toward target
    "turret_i_gain": 0.05,               # Integral gain -- accumulates error to push through friction
    "turret_i_max": 1.5,                 # Max integral voltage -- caps windup to prevent overshoot
    "turret_d_velocity_gain": 0.05,      # Velocity damping -- counterbalances P to prevent oscillation
    "turret_aim_inverted": True,         # Motor direction is opposite to angle convention (positive error = CCW, but motor negative = turret left)
    "turret_alignment_tolerance": 1.5,   # Degrees of tx offset considered "aligned"
    "feed_off_target_debounce": 20,      # Cycles off-target before stopping feed (~400ms at 50Hz)

    "turret_max_auto_voltage": 1.5,     # Max voltage during auto-aim (sqrt P handles decel now)
    "turret_max_brake_voltage": 0.5,    # Brake limit -- higher than drive to stop quickly
    "turret_min_move_voltage": 0.50,    # Deadband comp -- minimum voltage to overcome static friction
    "turret_tx_filter_alpha": 0.95,      # EMA smoothing for tx (0=max smooth, 1=no filter)

    # Distance lookup table: (distance_m, launcher_rps, hood_position, flight_time_s)
    # flight_time_s: how long the ball is in the air (seconds) at this distance.
    # Used by movement compensation to calculate lead angle and distance correction.
    # Measure with a stopwatch: time from launch to landing in the Hub.
    # Sorted by distance -- interpolated at runtime
    "distance_table": [
        (1.5, 35.0, 0, 0.85),
        (2.0, 37.0, 0, 0.95),
        (3.0, 45.0, 0, 1.1),
        (4.0, 54.0, 0, 1.4),
        (5.0, 67.0, 0, 2),
    ],

    # Manual shoot stick mapping -- maps joystick Y to virtual distance,
    # then looks up RPS and hood from the distance table above.
    # Stick -1 = min, stick 0 = center, stick +1 = max.
    "manual_min_distance": 1.5,     # Stick full back
    "manual_center_distance": 2.0,  # Stick at rest
    "manual_max_distance": 3.0,     # Stick full forward
}
