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
    "search_voltage": 3.0,
    "search_brake_voltage": 5.0,
    "search_brake_cycles": 3,
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
    "parallax_correction_enabled": False,
    "target_tags": {
        4: {"tag_y_offset_m": 0.0, "tag_x_offset_m": 0.0},
    },
    "distance_table": [
        (1.0, 20.0, 0.10, 4.0),
        (2.0, 40.0, 0.20, 6.0),
        (3.0, 60.0, 0.30, 8.0),
        (4.0, 80.0, 0.40, 10.0),
    ],
}

TEST_CON_MANUAL = {
    "launcher_min_rps": 20.0,
    "launcher_max_rps": 100.0,
    "hood_default_position": 0.5,
    "hood_position_step": 0.1,
}

# Tag priority: ordered list for priority-based targeting tests.
# Tag 4 is the only scoring tag in TEST_CON_SHOOTER, so it goes first.
TEST_TAG_PRIORITY = [4, 5, 6]

# Per-tag offsets for testing -- matches the tags in TEST_TAG_PRIORITY.
# Tag 4: centered on Hub (no offset). Tags 5/6: offset for parallax tests.
TEST_TAG_OFFSETS = {
    4: {"tag_y_offset_m": 0.0, "tag_x_offset_m": 0.0},
    5: {"tag_y_offset_m": -1.0, "tag_x_offset_m": 0.5},
    6: {"tag_y_offset_m": -1.0, "tag_x_offset_m": -0.5},
}

# How many cycles before the tracker gives up on a lost locked tag.
TEST_TARGET_LOCK_LOST_CYCLES = 5


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

    # Shooter lookup
    monkeypatch.setattr("subsystems.shooter_lookup.CON_SHOOTER", TEST_CON_SHOOTER)

    # Command modules
    monkeypatch.setattr("commands.auto_aim.CON_SHOOTER", TEST_CON_SHOOTER)
    monkeypatch.setattr(
        "commands.auto_aim.TARGET_LOCK_LOST_CYCLES",
        TEST_TARGET_LOCK_LOST_CYCLES,
    )
    monkeypatch.setattr("commands.find_target.CON_TURRET", TEST_CON_TURRET)
    monkeypatch.setattr("commands.manual_launcher.CON_MANUAL", TEST_CON_MANUAL)

    # Auto-aim telemetry and logging modules
    _test_debug = {"debug_telemetry": False, "verbose": False,
                   "auto_aim_logging": True}
    monkeypatch.setattr("telemetry.auto_aim_telemetry.DEBUG", _test_debug)
    monkeypatch.setattr("telemetry.auto_aim_logging.DEBUG", _test_debug)
