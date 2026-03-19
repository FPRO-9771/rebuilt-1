"""
Debug and logging settings.
"""

# =============================================================================
# DEBUG LOGGING
# =============================================================================
DEBUG = {
    "verbose": False,   # True = DEBUG level, False = INFO level
    "auto_aim_logging": False,  # True = show auto-aim pipeline logs (pose, error, PD, voltage) without turning on all verbose
    "debug_telemetry": True,  # True = publish all telemetry, False = match-only
    "auto_aim_dashboard": False,  # True = publish aim geometry to SmartDashboard (distance, bearing to Hub)
    "turret_aim_telemetry": False,  # True = always publish turret error/distance (even without CoordinateAim active)
    "limelight_reset_logging": True,  # True = log full input/output details on Limelight one-shot pose resets
    "drive_input_logging": False,  # True = log drive input pipeline (raw stick, curved, velocity) to console + SmartDashboard
    # Match-only telemetry (always published):
    #   Motors/Launcher At Speed, Motors/Feeder Running, Motors/Turret Clear,
    #   Motors/Intake Running, AutoAim/HasTarget,
    #   AutoAim/LockedTagID, Limelight camera stream (registered at init)
}
