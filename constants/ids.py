"""
CAN IDs for motors and sensors.
All IDs in one place so we never accidentally reuse a CAN address.
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

    # Shooter
    "turret": 30,
    "launcher": 31,
    "hood": 32,
}

# =============================================================================
# SENSOR CAN IDS
# =============================================================================
SENSOR_IDS = {
    # "pigeon": 40,
}
