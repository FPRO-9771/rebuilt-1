"""
Intake lever arm configuration.
"""

# =============================================================================
# INTAKE CONFIGURATION
# =============================================================================
CON_INTAKE = {
    "max_voltage": 4.0,         # Maximum voltage to apply
    "up_position": 0.0,         # Fully raised position (rotations)
    "gear_ratio": 5.0,          # 1:5 gearbox (motor turns 5x per arm turn)
    "down_position": -0.6528,   # 47 degrees arm rotation * 5:1 gear ratio (negative = down)
    "position_tolerance": 0.02, # "Close enough" tolerance (rotations)
    "hold_down_voltage": 1.5,  # Small voltage to keep arms down without PID whine
    "inverted": False,

    # Slot 0 gains for closed-loop position control
    # NEEDS TUNING on the real robot
    "slot0_kP": 1.0,
    "slot0_kI": 0.0,
    "slot0_kD": 0.1,
    "slot0_kS": 0.25,          # Static friction (volts to start moving)
    "slot0_kV": 0.0,
    "slot0_kA": 0.0,
    "slot0_kG": 1.5,           # Gravity feedforward -- tune if arm drops
}
