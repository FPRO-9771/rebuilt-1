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
    # Gear ratio: 9:1 planetary * (200t / 48t) = 37.5:1 total
    # 1 motor rotation = 1/37.5 turret rotations = ~16.6 degrees
    # max_position 22.0 motor rot ~= 364 degrees -- tune on robot to just before hard stop
    "gear_ratio": 36,

    "max_voltage": 5,         # Safety cap -- reduced for low-friction mechanism
    "manual_speed_factor": 1, # Manual mode: 1.0 * 0.40 = 1.0V max
    "manual_exponent": 2.0,     # Joystick response curve (1.0=linear, 2.0=squared, 3.0=cubed)
    "min_position": 0,       # Soft limit: leftmost rotation (rotations)
    "max_position": 41.5,        # Soft limit: (360 deg = 36 motor rot) -- tune to just before hard stop
    "position_tolerance": 0.02,  # "Close enough" tolerance (rotations)
    "inverted": False,           # Positive = left (unconfirmed -- flip if reversed)
    "brake": True,               # Brake on neutral -- holds turret steady
    "search_voltage": 0.06,     # Voltage during FindTarget sweep -- reduced for low-friction
    "search_brake_voltage": 0.15, # Brake voltage when sweep hits a soft limit
    "search_brake_cycles": 5,   # How many cycles to brake before reversing
    "soft_limit_ramp": 0.5,     # Rotations from soft limit where voltage starts ramping down

    # Slot 0 gains for closed-loop position hold (HoldPosition command).
    # Reduced kP and increased kD -- low-friction mechanism oscillates easily.
    # kP: volts per motor rotation of error. kD: damping to stop overshoot.
    "slot0_kP": 4.5,
    "slot0_kI": 0.0,
    "slot0_kD": 0.06,
    "slot0_kS": 0.10,           # Static friction -- reduced, mechanism is easier to turn
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

    # Slot 0 gains for closed-loop velocity control.
    # Tuning order: kV/kS first (feedforward dominant), then kP, then kD.
    # Heavy flywheel: kI causes integral windup oscillation -- keep at 0.
    # kA helps with spin-up inertia; increase if overshoot on initial spool-up.
    "slot0_kP": 0.40,
    "slot0_kI": 0.0,            # DO NOT use kI -- causes windup oscillation on heavy flywheel
    "slot0_kD": 0.02,           # Derivative damping -- increase until bounce stops
    "slot0_kS": 0.1,            # Static friction (volts to start moving)
    "slot0_kV": 0.14,           # Velocity feedforward (volts per RPS)
    "slot0_kA": 0.01,           # Acceleration feedforward for flywheel inertia -- tune up if needed
    "slot0_kG": 0.0,            # Gravity feedforward (volts to hold against gravity)
}

