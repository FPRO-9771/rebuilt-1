"""
Pytest fixtures for robot testing.
Automatically enables mock hardware/vision and injects test constants.

IMPORTANT: Tests must never depend on real constant values from constants/.
All CON_* dicts here use simple round numbers chosen for easy mental math.
If you need a constant in a test, import it from here — not from constants/.
"""

import pytest

from hardware import set_mock_mode
from handlers import set_mock_vision_mode


# ============================================================================
# TEST CONSTANTS — intentionally different from production values
# ============================================================================

TEST_CON_TURRET = {
    "max_voltage": 10.0,
    "manual_speed_factor": 0.5,
    "min_position": -5.0,
    "max_position": 5.0,
    "position_tolerance": 0.1,
    "inverted": False,
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
    "turret_d_gain": 0.1,
    "turret_aim_inverted": False,
    "turret_alignment_tolerance": 2.0,
    "turret_max_auto_voltage": 5.0,
    "target_tags": {
        4: {"tx_offset": 0.0, "distance_offset": 0.0},
    },
    "distance_table": [
        (1.0, 20.0, 0.10),
        (2.0, 40.0, 0.20),
        (3.0, 60.0, 0.30),
        (4.0, 80.0, 0.40),
    ],
}

TEST_CON_MANUAL = {
    "launcher_default_rps": 50.0,
    "launcher_max_rps": 100.0,
    "launcher_speed_step": 10.0,
    "hood_default_position": 0.5,
    "hood_position_step": 0.1,
}


# ============================================================================
# AUTOUSE FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def mock_hardware():
    """Automatically use mock hardware for all tests."""
    set_mock_mode(True)
    yield
    set_mock_mode(False)


@pytest.fixture(autouse=True)
def mock_vision():
    """Automatically use mock vision for all tests."""
    set_mock_vision_mode(True)
    yield
    set_mock_vision_mode(False)


@pytest.fixture(autouse=True)
def _patch_constants(monkeypatch):
    """
    Replace every CON_* dict in every module that imports one.
    This runs before every test so production constants never leak in.
    """
    # Subsystems
    monkeypatch.setattr("subsystems.turret.CON_TURRET", TEST_CON_TURRET)
    monkeypatch.setattr("subsystems.launcher.CON_LAUNCHER", TEST_CON_LAUNCHER)
    monkeypatch.setattr("subsystems.hood.CON_HOOD", TEST_CON_HOOD)
    monkeypatch.setattr("subsystems.conveyor.CON_CONVEYOR", TEST_CON_CONVEYOR)

    # Shooter lookup + orchestrator
    monkeypatch.setattr("subsystems.shooter_lookup.CON_SHOOTER", TEST_CON_SHOOTER)
    monkeypatch.setattr("commands.shooter_orchestrator.CON_SHOOTER", TEST_CON_SHOOTER)

    # Operator controls
    monkeypatch.setattr("controls.operator_controls.CON_MANUAL", TEST_CON_MANUAL)
    monkeypatch.setattr("controls.operator_controls.CON_HOOD", TEST_CON_HOOD)
