"""
Controller and robot-wide settings.
"""

# =============================================================================
# MANUAL OVERRIDE CONTROLS
# =============================================================================
CON_MANUAL = {
    "launcher_default_rps": 70.0,   # Starting speed for manual launcher
    "launcher_max_rps": 100.0,       # Maximum manual launcher speed
    "launcher_speed_step": 5.0,     # Per-press increment (~5% of max)
    "hood_default_position": 0.0,    # Start at zero (where motor initializes)
    "hood_position_step": 0.0125,    # Per-press nudge (~5% of range)
}

# =============================================================================
# ROBOT-WIDE SETTINGS
# =============================================================================
CON_ROBOT = {
    "use_ps4": False,  # True = PlayStation controllers, False = Xbox controllers

    "driver_controller_port": 0,
    "operator_controller_port": 1,

    "joystick_deadband": 0.1,
    "drive_exponent": 2.0,       # Translation response curve (1.0 = linear)
    "rotation_exponent": 2.0,    # Rotation response curve (1.0 = linear)

    # Drivetrain (placeholders until tuned)
    "max_speed_mps": 5.0,
    "max_angular_rate": 3.14,
}
