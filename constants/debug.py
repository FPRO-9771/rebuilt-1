"""
Debug and logging settings.
"""

# =============================================================================
# DEBUG LOGGING
# =============================================================================
DEBUG = {
    "verbose": True,   # True = DEBUG level, False = INFO level
    "debug_telemetry": True,  # True = publish all telemetry, False = match-only
    # Match-only telemetry (always published):
    #   Motors/Launcher At Speed, Motors/V Feed Running,
    #   AutoAim/HasTarget, AutoAim/LockedTagID,
    #   Limelight camera stream (registered at init)
}
