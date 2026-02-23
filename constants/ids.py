"""
CAN IDs for motors and sensors.
All IDs in one place so we never accidentally reuse a CAN address.

Motor types: "talon_fx" (KrakenX60), "talon_fxs" (WCP via TalonFXS)
Set wired=False for motors not yet physically connected.
"""

# =============================================================================
# MOTOR CAN IDS
# =============================================================================
MOTOR_IDS = {
    # Drivetrain - will be configured via tuner_constants.py
    # "drive_fl": {"can_id": 1, "type": "talon_fx", "wired": True},

    # Mechanisms
    "conveyor": {"can_id": 20, "type": "talon_fx", "wired": False},
    # "arm":    {"can_id": 21, "type": "talon_fx", "wired": False},
    # "intake": {"can_id": 22, "type": "talon_fx", "wired": False},

    # Shooter
    "turret":   {"can_id": 30, "type": "talon_fx",  "wired": True},
    "launcher": {"can_id": 31, "type": "talon_fx",  "wired": True},
    "hood":     {"can_id": 32, "type": "talon_fxs", "wired": True},
}

# =============================================================================
# SENSOR CAN IDS
# =============================================================================
SENSOR_IDS = {
    # "pigeon": 40,
}
