"""
Intake lever arm configuration.
"""

# =============================================================================
# INTAKE CONFIGURATION
# =============================================================================
CON_INTAKE = {
    "max_voltage": 10.0,        # Maximum voltage to apply
    "up_position": 0.0,         # Fully raised position (rotations)
    "gear_ratio": 5.0,          # 1:5 gearbox (motor turns 5x per arm turn)
    "down_position": 1.2,       # Fully lowered position (motor rotations: 0.24 arm turns * 5)
    "position_tolerance": 0.02, # "Close enough" tolerance (rotations)
    "inverted": False,

    # Slot 0 gains for closed-loop position control
    # NEEDS TUNING -- start with low kP and increase
    "slot0_kP": 1.0,
    "slot0_kI": 0.0,
    "slot0_kD": 0.01,
    "slot0_kS": 0.1,           # Static friction (volts to start moving)
    "slot0_kV": 0.0,
    "slot0_kA": 0.0,
    "slot0_kG": 0.0,           # Gravity feedforward -- tune if arm drops
}
