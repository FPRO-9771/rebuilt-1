"""
CAN IDs for motors and sensors.
All IDs in one place so we never accidentally reuse a CAN address.

Motor types: "talon_fx" (KrakenX60), "talon_fxs" (WCP via TalonFXS)
Set wired=False for motors not yet physically connected.
Optional sim_rps_per_volt: motor speed in sim (rotations/sec per volt). Default 6.0.
Optional current_limit: {"stator": amps, "supply": amps} for current limiting.
"""

# =============================================================================
# MOTOR CAN IDS
# =============================================================================
MOTOR_IDS = {
    # Drivetrain - will be configured via tuner_constants.py
    # "drive_fl": {"can_id": 1, "type": "talon_fx", "wired": True},

    # Mechanisms
    "conveyor": {"can_id": 20, "type": "talon_fx", "bus": "op_sys", "wired": False,
                 "current_limit": {"stator": 30, "supply": 15}}, #was 60/40
    "h_feed":   {"can_id": 22, "type": "talon_fx", "bus": "op_sys", "wired": True,
                 "current_limit": {"stator": 60, "supply": 40}}, #was 60/40
    "v_feed":   {"can_id": 23, "type": "talon_fx", "bus": "op_sys", "wired": True,
                 "current_limit": {"stator": 60, "supply": 40}},#was 60/40

    # Intake
    "intake_spinner": {"can_id": 40, "type": "talon_fx", "bus": "op_sys", "wired": True,
                       "current_limit": {"stator": 60, "supply": 40}},#was 60/40
    "intake_left":    {"can_id": 41, "type": "talon_fx", "bus": "op_sys", "wired": True,
                       "current_limit": {"stator": 60, "supply": 40}},#was 60/40
    "intake_right":   {"can_id": 42, "type": "talon_fx", "bus": "op_sys", "wired": True,
                       "current_limit": {"stator": 60, "supply": 40}},#was 60/40

    # Shooter
    "turret":   {"can_id": 30, "type": "talon_fx",  "bus": "op_sys", "wired": False, "sim_rps_per_volt": 2.0,
                 "current_limit": {"stator": 60, "supply": 40}},#was 30/25
    "turret_minion": {"can_id": 32, "type": "talon_fxs", "bus": "op_sys", "wired": True, "sim_rps_per_volt": 2.5,
                      "current_limit": {"stator": 30, "supply": 25}},#was 30/25
    "launcher": {"can_id": 31, "type": "talon_fx",  "bus": "op_sys", "wired": True, "sim_rps_per_volt": 8.0,
                 "current_limit": {"stator": 60, "supply": 40}},#no change
    "hood":     {"can_id": 33, "type": "talon_fxs", "bus": "op_sys", "wired": True, "sim_rps_per_volt": 1.0,
                 "current_limit": {"stator": 30, "supply": 25}}, #was 30/25
}

# =============================================================================
# SENSOR CAN IDS
# =============================================================================
SENSOR_IDS = {
    # "pigeon": 40,
}
