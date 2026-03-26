"""
Shooter hardware constants: turret, launcher, and feed orchestrator.

Motor-level configuration for each shooter mechanism. For auto-aim
tuning (PD gains, voltage limits), see shoot_auto_aim.py. For the
distance lookup table, see shoot_distance_table.py.
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
    "max_voltage": 4.0,         # Safety cap -- tune down once moving
    "manual_speed_factor": 0.50, # Manual mode: 1.0 * 0.50 = 0.50V
    "manual_exponent": 2.0,     # Joystick response curve (1.0=linear, 2.0=squared, 3.0=cubed)
    "min_position": 0,       # Soft limit: leftmost rotation (rotations)
    "max_position": 10.3,        # Soft limit: rightmost rotation (rotations)
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

