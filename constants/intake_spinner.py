"""
Intake spinner configuration.
"""

# =============================================================================
# INTAKE SPINNER CONFIGURATION
# =============================================================================
CON_INTAKE_SPINNER = {
    "max_voltage": 12.0,      # Maximum voltage to apply
    "spin_voltage": 11,      # Voltage when spinning to intake Fuel

    # Un-jam detection and recovery
    "unjam_velocity_threshold": 0.5,  # RPS below this = jammed
    "unjam_speed_multiplier": 2.0,    # Reverse at this multiple of spin_voltage
    "unjam_duration_cycles": 13,      # 13 cycles * 20ms = ~0.25 seconds
    "unjam_spinup_cycles": 10,        # Ignore stall checks for this many cycles after start/resume (motor spin-up)
}
