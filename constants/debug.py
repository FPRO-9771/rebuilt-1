"""
Debug and logging settings.
"""

# =============================================================================
# DEBUG LOGGING
# =============================================================================
DEBUG = {
    "verbose": True,   # True = DEBUG level, False = INFO level
    "auto_aim_logging": True,  # True = show auto-aim pipeline logs (pose, error, PD, voltage) without turning on all verbose
    "debug_telemetry": True,  # True = publish all telemetry, False = match-only
    "auto_aim_dashboard": True,  # True = publish aim geometry to SmartDashboard (distance, bearing to Hub)
    "turret_aim_telemetry": True,  # True = always publish turret error/distance (even without CoordinateAim active)
    # Match-only telemetry (always published):
    #   Motors/Launcher At Speed, Motors/Feeder Running, Motors/Turret Clear,
    #   Motors/Intake Running, AutoAim/HasTarget,
    #   AutoAim/LockedTagID, Limelight camera stream (registered at init)
}
