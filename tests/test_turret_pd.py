"""
Tests for turret PID voltage calculation.

Uses a local config dict so we can exercise all terms (P, I, D,
clamp, deadband) independently of the test conftest values.
"""

import math

from calculations.turret_pd import compute_turret_voltage

# Config with all features active and easy-to-reason-about values.
_CFG = {
    "turret_p_gain": 0.5,
    "turret_i_gain": 0.1,
    "turret_i_max": 1.0,
    "turret_d_velocity_gain": 0.1,
    "turret_max_auto_voltage": 2.0,
    "turret_max_brake_voltage": 3.0,
    "turret_min_move_voltage": 0.3,
}


# =========================================================================
# P term
# =========================================================================

def test_positive_error_produces_positive_p():
    """Target to the right -> positive P term."""
    voltage, p_term, _, _, _, _ = compute_turret_voltage(
        filtered_tx=4.0, turret_vel=0.0, aim_sign=1.0, config=_CFG)
    assert p_term > 0


def test_negative_error_produces_negative_p():
    """Target to the left -> negative P term."""
    voltage, p_term, _, _, _, _ = compute_turret_voltage(
        filtered_tx=-4.0, turret_vel=0.0, aim_sign=1.0, config=_CFG)
    assert p_term < 0


def test_sqrt_compression():
    """Large errors grow slower than linear (sqrt compression)."""
    _, p_small, _, _, _, _ = compute_turret_voltage(
        filtered_tx=1.0, turret_vel=0.0, aim_sign=1.0, config=_CFG)
    _, p_large, _, _, _, _ = compute_turret_voltage(
        filtered_tx=9.0, turret_vel=0.0, aim_sign=1.0, config=_CFG)
    # Linear would give 9x; sqrt gives 3x
    ratio = p_large / p_small
    assert ratio < 9.0
    assert ratio == math.sqrt(9.0) / math.sqrt(1.0)


def test_zero_error_produces_zero_p():
    """No error -> no P output."""
    _, p_term, _, _, _, _ = compute_turret_voltage(
        filtered_tx=0.0, turret_vel=0.0, aim_sign=1.0, config=_CFG)
    assert p_term == 0.0


# =========================================================================
# I term
# =========================================================================

def test_i_accumulates_over_calls():
    """Integral term grows when error persists across cycles."""
    accum = 0.0
    for _ in range(5):
        _, _, i_term, _, _, accum = compute_turret_voltage(
            filtered_tx=2.0, turret_vel=0.0, aim_sign=1.0,
            config=_CFG, i_accumulator=accum)
    # After 5 cycles of error=2.0: accumulator = 10.0, i_term = 10.0 * 0.1 = 1.0
    assert i_term > 0
    assert accum == 10.0


def test_i_resets_on_zero_crossing():
    """Integral accumulator resets when error crosses zero."""
    # Build up positive accumulator
    accum = 0.0
    for _ in range(5):
        _, _, _, _, _, accum = compute_turret_voltage(
            filtered_tx=2.0, turret_vel=0.0, aim_sign=1.0,
            config=_CFG, i_accumulator=accum)
    assert accum > 0
    # Now flip error sign -- accumulator should reset
    _, _, i_term, _, _, accum = compute_turret_voltage(
        filtered_tx=-1.0, turret_vel=0.0, aim_sign=1.0,
        config=_CFG, i_accumulator=accum)
    # Accumulator reset to 0 then added -1.0
    assert accum == -1.0


def test_i_windup_capped():
    """Integral accumulator is capped by turret_i_max / turret_i_gain."""
    max_accum = _CFG["turret_i_max"] / _CFG["turret_i_gain"]
    accum = 0.0
    for _ in range(200):
        _, _, i_term, _, _, accum = compute_turret_voltage(
            filtered_tx=5.0, turret_vel=0.0, aim_sign=1.0,
            config=_CFG, i_accumulator=accum)
    assert accum == max_accum
    assert abs(i_term) <= _CFG["turret_i_max"]


def test_i_zero_when_disabled():
    """No I output when turret_i_gain is 0 or missing."""
    cfg_no_i = {k: v for k, v in _CFG.items()
                if k not in ("turret_i_gain", "turret_i_max")}
    _, _, i_term, _, _, accum = compute_turret_voltage(
        filtered_tx=5.0, turret_vel=0.0, aim_sign=1.0,
        config=cfg_no_i, i_accumulator=10.0)
    assert i_term == 0.0


# =========================================================================
# D term
# =========================================================================

def test_d_opposes_turret_velocity():
    """D term should brake -- oppose the turret's current motion."""
    _, _, _, d_term, _, _ = compute_turret_voltage(
        filtered_tx=0.0, turret_vel=2.0, aim_sign=1.0, config=_CFG)
    assert d_term < 0

    _, _, _, d_term, _, _ = compute_turret_voltage(
        filtered_tx=0.0, turret_vel=-2.0, aim_sign=1.0, config=_CFG)
    assert d_term > 0


def test_d_zero_when_stopped():
    """No turret motion -> no D output."""
    _, _, _, d_term, _, _ = compute_turret_voltage(
        filtered_tx=5.0, turret_vel=0.0, aim_sign=1.0, config=_CFG)
    assert d_term == 0.0


# =========================================================================
# Clamping
# =========================================================================

def test_clamp_to_auto_voltage_when_driving():
    """Voltage clamps to max_auto_voltage when driving (not braking)."""
    voltage, _, _, _, raw, _ = compute_turret_voltage(
        filtered_tx=100.0, turret_vel=0.0, aim_sign=1.0, config=_CFG)
    assert abs(raw) > _CFG["turret_max_auto_voltage"]
    assert abs(voltage) == _CFG["turret_max_auto_voltage"]


def test_clamp_to_brake_voltage_when_opposing():
    """Voltage uses higher brake limit when opposing turret motion."""
    # Turret moving positive, voltage should be negative (braking)
    voltage, _, _, _, _, _ = compute_turret_voltage(
        filtered_tx=-100.0, turret_vel=2.0, aim_sign=1.0, config=_CFG)
    # Should clamp to brake limit, not auto limit
    assert abs(voltage) <= _CFG["turret_max_brake_voltage"]


# =========================================================================
# Deadband compensation
# =========================================================================

def test_deadband_bumps_small_voltage():
    """When turret is stopped and voltage is below min_move, bump it up."""
    # Small error -> small P -> below min_move threshold
    # Use a config with meaningful deadband and no I to isolate the test
    cfg = {**_CFG, "turret_max_auto_voltage": 5.0, "turret_i_gain": 0.0}
    voltage, _, _, _, _, _ = compute_turret_voltage(
        filtered_tx=0.1, turret_vel=0.0, aim_sign=1.0, config=cfg)
    # Raw voltage from sqrt(0.1)*0.5 ~ 0.158, below min_move of 0.3
    assert abs(voltage) == cfg["turret_min_move_voltage"]


def test_deadband_does_not_fire_when_moving():
    """Deadband comp should not activate when turret is already moving."""
    voltage, _, _, _, _, _ = compute_turret_voltage(
        filtered_tx=0.1, turret_vel=1.0, aim_sign=1.0, config=_CFG)
    # Turret is moving -- deadband should not bump voltage
    assert abs(voltage) != _CFG["turret_min_move_voltage"]
