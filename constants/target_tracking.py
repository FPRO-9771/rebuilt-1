"""
Target tracking constants.
Alliance Hub positions and PID gains for odometry-based aiming.

Update the target positions once you have real 2026 field measurements.
All coordinates are in meters using WPILib field coordinates:
  Origin (0, 0) = bottom-left corner of the field (blue driver station right corner).
  X = toward red alliance wall, Y = toward left side of blue driver station.
"""

# =============================================================================
# ALLIANCE TARGET POSITIONS (meters)
# =============================================================================
# Each target is the center of that alliance's Hub on the field.
# TODO: Replace with measured 2026 Hub coordinates from the game manual.

CON_TARGET_TRACKING = {
    # Blue alliance Hub position (meters)
    "blue_target_x": 0.0,
    "blue_target_y": 4.1,

    # Red alliance Hub position (meters)
    "red_target_x": 16.54,
    "red_target_y": 4.1,

    # --- PID gains for rotation toward target ---
    "aim_kP": 0.02,
    "aim_kI": 0.0,
    "aim_kD": 0.002,

    # Heading error tolerance (degrees) -- command ends when within this
    "heading_tolerance_deg": 2.0,

    # Max rotation output (fraction of max angular velocity, 0 to 1)
    "max_rotation_output": 0.5,

    # --- Turret control for CoordinateAim ---
    "turret_max_voltage": 1,          # Max voltage sent to turret during coordinate aim
    "turret_kP": 0.04,                 # Proportional gain (volts per degree of error)
    "turret_full_speed_error_deg": 45,  # Error angle (deg) at which turret hits max voltage
}
