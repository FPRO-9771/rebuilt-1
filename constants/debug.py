"""
Debug and logging settings.
"""

# =============================================================================
# DEBUG LOGGING
# =============================================================================
DEBUG = {
    "verbose": True,   # True = DEBUG level, False = INFO level
    "auto_aim_logging": True,  # True = show auto-aim console logs even when verbose is off
    "debug_telemetry": True,  # True = publish all telemetry, False = match-only
    # Match-only telemetry (always published):
    #   Motors/Launcher At Speed, Motors/Feeder Running, Motors/Turret Clear,
    #   Motors/Intake Running, AutoAim/HasTarget,
    #   AutoAim/LockedTagID, Limelight camera stream (registered at init)
}
