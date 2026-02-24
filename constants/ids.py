"""
CAN IDs for motors and sensors.
All IDs in one place so we never accidentally reuse a CAN address.

Motor types: "talon_fx" (KrakenX60), "talon_fxs" (WCP via TalonFXS)
Set wired=False for motors not yet physically connected.
Optional sim_rps_per_volt: motor speed in sim (rotations/sec per volt). Default 6.0.
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
    "turret":   {"can_id": 30, "type": "talon_fx",  "wired": True, "sim_rps_per_volt": 2.0},
    "launcher": {"can_id": 31, "type": "talon_fx",  "wired": True, "sim_rps_per_volt": 8.0},
    "hood":     {"can_id": 32, "type": "talon_fxs", "wired": True, "sim_rps_per_volt": 1.0},
}

# =============================================================================
# SENSOR CAN IDS
# =============================================================================
SENSOR_IDS = {
    # "pigeon": 40,
}
