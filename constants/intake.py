"""
Intake lever arm configuration.
"""

# =============================================================================
# INTAKE CONFIGURATION
# =============================================================================
CON_INTAKE = {
    "up_position": 0.0,         # Fully raised position (rotations)
    "gear_ratio": 15.0,         # 1:15 gearbox (motor turns 15x per arm turn)
    "down_position": -4.91,     # measured on robot -- arm settles here with brake voltage (re-measure with 1:15 gearbox)
    "position_tolerance": 0.05, # "Close enough" tolerance (rotations)
    "hold_kP": 2.0,             # Soft hold gain (volts per rotation of drift)
    "hold_max_voltage": 1.0,    # Max voltage during soft hold (low to protect gears)
    "spin_hold_enabled": False,       # Enable hold-down while spinner is running
    "spin_hold_max_voltage": 2.5,  # Max hold voltage while spinner is running -- TUNE
    "hold_deadband": 0.05,      # Ignore drift smaller than this (rotations)
    "guard_zone": 1.0,          # Position guard only active within this distance of up_position (rotations)
    "stall_current": 40.0,      # Current limit (amps) -- stop motor if exceeded
    "inverted": False,

    # Two-phase move tuning
    # Fraction of travel (0.0=up_position, 1.0=down_position) where phase 2 begins.
    # DOWN: fraction where gravity takes over and arm needs braking
    "down_transition_fraction": 0.90,   # TUNE on robot
    # UP: fraction (from up_position) where arm has enough momentum and needs easing
    "up_transition_fraction": 0.25,     # TUNE on robot (higher = switch to ease sooner)
    # Going down phase 1: pushing arm down, gravity not helping yet
    "down_push_voltage": -2,          # TUNE on robot (negative = toward down position)
    # Going down phase 2: gravity pulling hard, motors slow it down
    "down_brake_voltage": 0.1,          # TUNE on robot (positive = resists gravity)
    # Going up phase 1: fighting gravity at its worst (arm horizontal)
    "up_fight_voltage": 2.5,            # TUNE on robot (positive = toward up position)
    # Going up phase 2: slow down before hitting the up stop
    "up_ease_voltage": -0.2,            # TUNE on robot (negative = brakes against momentum)

    # Pit-mode manual jog (Start + Right stick Y on operator controller).
    # Used to raise/lower the arm by hand when mechanical locks prevent
    # moving it physically and position zeros may be stale. Voltages are
    # intentionally low so the arm creeps rather than slams.
    "pit_up_voltage": 2.0,              # Voltage while jogging UP (fights gravity)
    "pit_down_voltage": -0.8,           # Voltage while jogging DOWN (gravity helps)

    # Slot 0 gains for closed-loop position control
    # NEEDS TUNING on the real robot
    "slot0_kP": 0.35,
    "slot0_kI": 0.0,
    "slot0_kD": 0.1,
    "slot0_kS": 0.25,          # Static friction (volts to start moving)
    "slot0_kV": 0.0,
    "slot0_kA": 0.0,
    "slot0_kG": 0.0,           # Disabled -- gravity helps at up, hurts at down stop
}
