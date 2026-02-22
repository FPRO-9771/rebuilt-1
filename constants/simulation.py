"""
Simulation calibration values and time step.
These should be measured from the real robot and updated at events.
"""

# =============================================================================
# SIMULATION CALIBRATION - Measured from real robot
# =============================================================================
# TODO: Calibrate these values on the real robot
SIM_CALIBRATION = {
    "conveyor": {
        "voltage_to_speed": 1.0,  # rotations/s per volt (measure this)
    },
    "drivetrain": {
        "max_speed_mps": 5.0,
        "voltage_to_speed": 0.4,
        "max_rotation_dps": 360,
        "voltage_to_rotation": 30,
        "accel_mps2": 6.0,
        "rotation_accel_dps2": 540,
    },
    "turret": {
        "voltage_to_speed": 0.5,  # rotations/s per volt
    },
    "launcher": {
        "voltage_to_speed": 8.0,  # rotations/s per volt
    },
    "hood": {
        "voltage_to_speed": 0.3,  # rotations/s per volt
    },
}

# Simulation time step (matches robot periodic rate)
SIM_DT = 0.020
