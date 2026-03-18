"""
Intake lever arm configuration.
"""

# =============================================================================
# INTAKE CONFIGURATION
# =============================================================================
CON_INTAKE = {
    "max_voltage": 2.0,         # Maximum voltage during PID moves (low until tuned)
    "up_position": 0.0,         # Fully raised position (rotations)
    "gear_ratio": 5.0,          # 1:5 gearbox (motor turns 5x per arm turn)
    "down_position": -1.25,     # 90 degrees arm rotation * 5:1 gear ratio (negative = down)
    "position_tolerance": 0.02, # "Close enough" tolerance (rotations)
    "hold_down_voltage": 1.5,   # Small voltage to keep arms down without PID whine
    "hold_kP": 2.0,             # Soft hold gain (volts per rotation of drift)
    "hold_max_voltage": 1.0,    # Max voltage during soft hold (low to protect gears)
    "hold_deadband": 0.1,       # Ignore drift smaller than this (rotations)
    "stall_current": 40.0,      # Current limit (amps) -- stop motor if exceeded
    "inverted": False,

    # Slot 0 gains for closed-loop position control
    # NEEDS TUNING on the real robot
    "slot0_kP": 3.0,
    "slot0_kI": 0.0,
    "slot0_kD": 0.1,
    "slot0_kS": 0.25,          # Static friction (volts to start moving)
    "slot0_kV": 0.0,
    "slot0_kA": 0.0,
    "slot0_kG": 0.0,           # Disabled -- gravity helps at up, hurts at down stop
}
