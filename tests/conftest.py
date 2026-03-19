"""
Pytest fixtures for robot testing.
Automatically enables mock hardware/vision and injects test constants.

IMPORTANT: Tests must never depend on real constant values from constants/.
All CON_* dicts here use simple round numbers chosen for easy mental math.
If you need a constant in a test, import it from here -- not from constants/.
"""

import pytest

from hardware import set_mock_mode
# from handlers import set_mock_vision_mode  # vision providers disabled


# ============================================================================
# TEST CONSTANTS -- intentionally different from production values
# ============================================================================

TEST_CON_TURRET = {
    "max_voltage": 10.0,
    "manual_speed_factor": 0.5,
    "min_position": -5.0,
    "max_position": 5.0,
    "position_tolerance": 0.1,
    "inverted": False,
    "search_voltage": 3.0,
    "search_brake_voltage": 5.0,
    "search_brake_cycles": 3,
}

TEST_CON_TURRET_MINION = {
    "max_voltage": 10.0,
    "manual_speed_factor": 0.5,
    "min_position": -5.0,
    "max_position": 5.0,
    "position_tolerance": 0.1,
    "inverted": False,
    "brake": True,
    "search_voltage": 3.0,
    "search_brake_voltage": 5.0,
    "search_brake_cycles": 3,
    "soft_limit_ramp": 2.0,
    "manual_exponent": 2.0,
    "slot0_kP": 1.0,
    "slot0_kI": 0.0,
    "slot0_kD": 0.01,
    "slot0_kS": 0.1,
    "slot0_kV": 0.0,
    "slot0_kA": 0.0,
    "slot0_kG": 0.0,
}

TEST_CON_LAUNCHER = {
    "max_voltage": 10.0,
    "velocity_tolerance": 1.0,
    "inverted": False,
    "slot0_kP": 0.1,
    "slot0_kI": 0.0,
    "slot0_kD": 0.0,
    "slot0_kS": 0.0,
    "slot0_kV": 0.0,
    "slot0_kA": 0.0,
    "slot0_kG": 0.0,
}

TEST_CON_HOOD = {
    "enabled": True,
    "max_voltage": 10.0,
    "min_position": 0.0,
    "max_position": 1.0,
    "position_tolerance": 0.1,
    "inverted": False,
    "brake": False,
    "slot0_kP": 10.0,
    "slot0_kI": 0.0,
    "slot0_kD": 0.0,
    "slot0_kS": 0.0,
    "slot0_kV": 0.0,
    "slot0_kA": 0.0,
    "slot0_kG": 0.0,
}

TEST_CON_CONVEYOR = {
    "max_voltage": 10.0,
    "intake_voltage": 5.0,
    "outtake_voltage": -5.0,
}

TEST_CON_SHOOTER = {
    "turret_p_gain": 0.5,
    "turret_d_velocity_gain": 0.0,
    "turret_aim_inverted": False,
    "turret_alignment_tolerance": 2.0,
    "turret_max_auto_voltage": 5.0,
    "turret_max_brake_voltage": 5.0,
    "turret_min_move_voltage": 0.0,
    "turret_velocity_ff_gain": 0.15,
    "turret_tx_filter_alpha": 1.0,
    "velocity_lead_enabled": True,
    "distance_table": [
        (1.0, 20.0, 0.10, 4.0),
        (2.0, 40.0, 0.20, 6.0),
        (3.0, 60.0, 0.30, 8.0),
        (4.0, 80.0, 0.40, 10.0),
    ],
    "manual_min_distance": 1.0,
    "manual_center_distance": 2.0,
    "manual_max_distance": 4.0,
}

TEST_CON_MANUAL = {
    "hood_default_position": 0.5,
    "hood_position_step": 0.1,
}

TEST_CON_INTAKE = {
    "up_position": 0.0,
    "gear_ratio": 15.0,
    "down_position": -2.0,
    "position_tolerance": 0.05,
    "hold_kP": 4.0,
    "hold_max_voltage": 2.0,
    "spin_hold_max_voltage": 4.0,
    "hold_deadband": 0.1,
    "stall_current": 40.0,
    "inverted": False,
    "down_transition_fraction": 0.25,
    "up_transition_fraction": 0.25,
    "down_push_voltage": -2.0,
    "down_brake_voltage": 1.0,
    "up_fight_voltage": 3.0,
    "up_ease_voltage": -1.0,
    "slot0_kP": 1.0,
    "slot0_kI": 0.0,
    "slot0_kD": 0.0,
    "slot0_kS": 0.0,
    "slot0_kV": 0.0,
    "slot0_kA": 0.0,
    "slot0_kG": 0.0,
}

TEST_CON_INTAKE_SPINNER = {
    "max_voltage": 10.0,
    "spin_voltage": 5.0,
}

TEST_CON_POSE = {
    "center_position": 0.0,
    "degrees_per_rotation": 40.0,
    "shooter_offset_x": 0.0,    # zero offset for simple test math
    "shooter_offset_y": 0.0,
}

# Tag priority: ordered list for vision-based distance lookup tests.
TEST_TAG_PRIORITY = [4, 5, 6]


# ============================================================================
# AUTOUSE FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def mock_hardware():
    """Automatically use mock hardware for all tests."""
    set_mock_mode(True)
    yield
    set_mock_mode(False)


# mock_vision fixture removed -- vision providers disabled (2026-03-19)


@pytest.fixture(autouse=True)
def _patch_constants(monkeypatch):
    """
    Replace every CON_* dict in every module that imports one.
    This runs before every test so production constants never leak in.
    """
    # Subsystems
    monkeypatch.setattr("subsystems.turret.CON_TURRET", TEST_CON_TURRET)
    monkeypatch.setattr("subsystems.turret_minion.CON_TURRET_MINION", TEST_CON_TURRET_MINION)
    monkeypatch.setattr("subsystems.launcher.CON_LAUNCHER", TEST_CON_LAUNCHER)
    monkeypatch.setattr("subsystems.hood.CON_HOOD", TEST_CON_HOOD)
    monkeypatch.setattr("subsystems.conveyor.CON_CONVEYOR", TEST_CON_CONVEYOR)

    # Shooter lookup
    monkeypatch.setattr("subsystems.shooter_lookup.CON_SHOOTER", TEST_CON_SHOOTER)

    # Coordinate aim command
    monkeypatch.setattr("commands.coordinate_aim.CON_SHOOTER", TEST_CON_SHOOTER)
    monkeypatch.setattr("commands.coordinate_aim.CON_POSE", TEST_CON_POSE)

    # Operator controls -- CON_POSE removed (shoot context supplier commented out)

    # Intake
    monkeypatch.setattr("subsystems.intake.CON_INTAKE", TEST_CON_INTAKE)
    monkeypatch.setattr("subsystems.intake_spinner.CON_INTAKE_SPINNER", TEST_CON_INTAKE_SPINNER)
    monkeypatch.setattr("commands.run_intake.CON_INTAKE", TEST_CON_INTAKE)
    monkeypatch.setattr("commands.run_intake.CON_INTAKE_SPINNER", TEST_CON_INTAKE_SPINNER)

    # Manual shoot / launcher -- stick-to-distance mapping uses CON_SHOOTER
    monkeypatch.setattr("commands.manual_shoot.CON_SHOOTER", TEST_CON_SHOOTER)

    # Other commands
    monkeypatch.setattr("commands.manual_hood.CON_MANUAL", TEST_CON_MANUAL)
    monkeypatch.setattr("commands.manual_hood.CON_HOOD", TEST_CON_HOOD)

    # Auto-aim telemetry and logging modules
    _test_debug = {"debug_telemetry": False, "verbose": False,
                   "auto_aim_logging": True, "auto_aim_dashboard": False}
    monkeypatch.setattr("telemetry.auto_aim_telemetry.DEBUG", _test_debug)
    monkeypatch.setattr("telemetry.auto_aim_logging.DEBUG", _test_debug)

    # Swerve and motor telemetry -- enable debug so tests can verify all keys
    _test_debug_on = {"debug_telemetry": True, "verbose": False,
                      "auto_aim_logging": True, "auto_aim_dashboard": False}
    monkeypatch.setattr("telemetry.swerve_telemetry.DEBUG", _test_debug_on)
    monkeypatch.setattr("telemetry.motor_telemetry.DEBUG", _test_debug_on)
