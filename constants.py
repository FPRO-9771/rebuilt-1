"""
Configuration constants for Team 9771 Robot 2026.
All magic numbers go here - no hardcoded values in subsystem code.
"""

# =============================================================================
# MOTOR CAN IDS
# =============================================================================
MOTOR_IDS = {
    # Drivetrain - will be configured via tuner_constants.py
    # "drive_fl": 1, "steer_fl": 2, etc.

    # Mechanisms
    "conveyor": 20,
    # "arm": 21,
    # "intake": 22,
}

# =============================================================================
# SENSOR CAN IDS
# =============================================================================
SENSOR_IDS = {
    # "pigeon": 40,
}

# =============================================================================
# CONVEYOR CONFIGURATION
# =============================================================================
CON_CONVEYOR = {
    "max_voltage": 10.0,      # Maximum voltage to apply
    "intake_voltage": 6.0,    # Voltage when intaking game pieces
    "outtake_voltage": -6.0,  # Voltage when ejecting (negative = reverse)
}

# =============================================================================
# ROBOT-WIDE SETTINGS
# =============================================================================
CON_ROBOT = {
    "driver_controller_port": 0,
    "operator_controller_port": 1,

    "joystick_deadband": 0.1,

    # Drivetrain (placeholders until tuned)
    "max_speed_mps": 5.0,
    "max_angular_rate": 3.14,
}

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
}

# Simulation time step (matches robot periodic rate)
SIM_DT = 0.020
