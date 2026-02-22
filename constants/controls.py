"""
Controller and robot-wide settings.
"""

# =============================================================================
# MANUAL OVERRIDE CONTROLS
# =============================================================================
CON_MANUAL = {
    "launcher_default_rps": 40.0,   # Starting speed for manual launcher
    "launcher_max_rps": 80.0,       # Maximum manual launcher speed
    "launcher_speed_step": 4.0,     # Per-press increment (~5% of max)
    "hood_default_position": 0.125,  # Starting position (mid-range of 0.0-0.25)
    "hood_position_step": 0.0125,    # Per-press nudge (~5% of range)
}

# =============================================================================
# ROBOT-WIDE SETTINGS
# =============================================================================
CON_ROBOT = {
    "driver_controller_port": 0,
    "operator_controller_port": 1,

    "joystick_deadband": 0.1,

    # Drivetrain (placeholders until tuned)
    "max_speed_mps": 5.0,
    "max_angular_rate": 3.14,
}
