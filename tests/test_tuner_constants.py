"""
Tests for Tuner X generated swerve constants.
Validates structure and consistency -- catches copy-paste errors or
accidental edits to the generated file.
"""

from generated.tuner_constants import TunerConstants


# --- CAN ID uniqueness ---

def _all_module_can_ids():
    """Collect all CAN IDs from the four module definitions."""
    ids = []
    for prefix in ("_front_left", "_front_right", "_back_left", "_back_right"):
        ids.append(getattr(TunerConstants, f"{prefix}_drive_motor_id"))
        ids.append(getattr(TunerConstants, f"{prefix}_steer_motor_id"))
        ids.append(getattr(TunerConstants, f"{prefix}_encoder_id"))
    return ids


def test_all_can_ids_unique():
    """Every drive motor, steer motor, and encoder must have a unique CAN ID."""
    ids = _all_module_can_ids()
    ids.append(TunerConstants._pigeon_id)
    assert len(ids) == len(set(ids)), f"Duplicate CAN IDs found: {ids}"


def test_no_zero_can_ids():
    """CAN ID 0 is reserved -- no device should use it."""
    ids = _all_module_can_ids()
    ids.append(TunerConstants._pigeon_id)
    assert 0 not in ids, "CAN ID 0 is reserved"


# --- Module positions form a rectangle ---

def test_four_modules_exist():
    """Verify all four module constants are created."""
    assert TunerConstants.front_left is not None
    assert TunerConstants.front_right is not None
    assert TunerConstants.back_left is not None
    assert TunerConstants.back_right is not None


def test_module_positions_symmetric():
    """Front/back and left/right positions should be mirrored."""
    fl_x = TunerConstants._front_left_x_pos
    fr_x = TunerConstants._front_right_x_pos
    bl_x = TunerConstants._back_left_x_pos
    br_x = TunerConstants._back_right_x_pos

    fl_y = TunerConstants._front_left_y_pos
    fr_y = TunerConstants._front_right_y_pos
    bl_y = TunerConstants._back_left_y_pos
    br_y = TunerConstants._back_right_y_pos

    # Front pair has same X, back pair has same X
    assert fl_x == fr_x, "Front modules should have same X"
    assert bl_x == br_x, "Back modules should have same X"

    # Left pair has same Y, right pair has same Y
    assert fl_y == bl_y, "Left modules should have same Y"
    assert fr_y == br_y, "Right modules should have same Y"

    # Left/right are mirrored across center
    assert fl_y == -fr_y, "Left/right Y positions should be mirrored"

    # Front/back are mirrored across center
    assert fl_x == -bl_x, "Front/back X positions should be mirrored"


# --- Physical sanity checks ---

def test_speed_at_12_volts_positive():
    """Max speed must be positive."""
    assert TunerConstants.speed_at_12_volts > 0


def test_gear_ratios_positive():
    """Gear ratios must be positive."""
    assert TunerConstants._drive_gear_ratio > 0
    assert TunerConstants._steer_gear_ratio > 0


def test_wheel_radius_positive():
    """Wheel radius must be positive."""
    assert TunerConstants._wheel_radius > 0


def test_slip_current_positive():
    """Slip current must be positive."""
    assert TunerConstants._slip_current > 0
