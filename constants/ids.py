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
    "conveyor": {"can_id": 20, "type": "talon_fx", "bus": "op_sys", "wired": False},
    "h_feed":   {"can_id": 22, "type": "talon_fx", "bus": "op_sys", "wired": True},
    "v_feed":   {"can_id": 23, "type": "talon_fx", "bus": "op_sys", "wired": True},

    # Intake
    "intake_left":  {"can_id": 40, "type": "talon_fx", "bus": "op_sys", "wired": False},
    "intake_right": {"can_id": 41, "type": "talon_fx", "bus": "op_sys", "wired": False},
    "intake_spinner": {"can_id": 42, "type": "talon_fx", "bus": "op_sys", "wired": False},

    # Shooter
    "turret":   {"can_id": 30, "type": "talon_fx",  "bus": "op_sys", "wired": True, "sim_rps_per_volt": 2.0},
    "launcher": {"can_id": 31, "type": "talon_fx",  "bus": "op_sys", "wired": True, "sim_rps_per_volt": 8.0},
    "hood":     {"can_id": 32, "type": "talon_fxs", "bus": "op_sys", "wired": False, "sim_rps_per_volt": 1.0},
}

# =============================================================================
# SENSOR CAN IDS
# =============================================================================
SENSOR_IDS = {
    # "pigeon": 40,
}
