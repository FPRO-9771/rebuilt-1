"""
Feed (horizontal and vertical) configuration.
"""

# =============================================================================
# HORIZONTAL FEED CONFIGURATION
# =============================================================================
CON_H_FEED = {
    "max_voltage": 10.0,      # Maximum voltage to apply
    "feed_voltage": 8.0,      # Voltage when feeding forward
    "reverse_voltage": -6.0,  # Voltage when reversing to un-jam
    "unjam_velocity_threshold": 0.5,  # RPS below this = jammed
    "unjam_duration_cycles": 10,      # 25 cycles * 20ms = 0.5 seconds
}

# =============================================================================
# VERTICAL FEED CONFIGURATION
# =============================================================================
CON_V_FEED = {
    "max_voltage": 10.0,      # Maximum voltage to apply
    "feed_voltage": -7.0,      # Voltage when feeding forward
}
