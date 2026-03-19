"""
Controller and robot-wide settings.
"""

# =============================================================================
# MANUAL OVERRIDE CONTROLS
# =============================================================================
CON_MANUAL = {
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
    "drive_exponent": 4.0,       # Translation response curve (1.0 = linear)
    "rotation_exponent": 5.0,    # Rotation response curve (1.0 = linear)

    # Drivetrain (placeholders until tuned)
    "max_speed_mps": 5.0,
    "max_angular_rate": 3.14,

    # Slow mode -- driver holds right trigger to reduce speed.
    # 1.0 = full speed, 0.25 = 25% speed when trigger fully held.
    "slow_mode_factor": 0.1,
}
