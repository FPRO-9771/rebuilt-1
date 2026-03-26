"""
Controller and robot-wide settings.
"""

# =============================================================================
# MANUAL OVERRIDE CONTROLS
# =============================================================================
CON_MANUAL = {
}

# =============================================================================
# ROBOT-WIDE SETTINGS
# =============================================================================
CON_ROBOT = {
    "use_ps4": False,  # True = PlayStation controllers, False = Xbox controllers

    "driver_controller_port": 0,
    "operator_controller_port": 1,

    "stick_deadband": 0.03,      # 3% stick deadband (handles drift)
    "drive_exponent": 4.0,       # Translation response curve (1.0 = linear)
    "rotation_exponent": 5.0,    # Rotation response curve (1.0 = linear)

    # Drivetrain (placeholders until tuned)
    "max_speed_mps": 5.0,
    "max_angular_rate": 3.14,

    # Slow mode -- driver holds right trigger to activate.
    # Trigger controls max speed: light squeeze = slow_max_speed,
    # full squeeze = slow_min_speed. Stick is linear within that range.
    "slow_max_speed": 2.0,       # m/s at lightest trigger squeeze
    "slow_min_speed": 0.5,       # m/s at full trigger squeeze
}
