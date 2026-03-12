"""
Tests for turret PD + feedforward voltage calculation.

Uses a local config dict so we can exercise all terms (P, D, FF,
clamp, deadband) independently of the test conftest values.
"""

import math

from calculations.turret_pd import compute_turret_voltage

# Config with all features active and easy-to-reason-about values.
_CFG = {
    "turret_p_gain": 0.5,
    "turret_d_velocity_gain": 0.1,
    "turret_velocity_ff_gain": 0.2,
    "turret_max_auto_voltage": 2.0,
    "turret_max_brake_voltage": 3.0,
    "turret_min_move_voltage": 0.3,
}


# =========================================================================
# P term
# =========================================================================

def test_positive_error_produces_positive_p():
    """Target to the right -> positive P term."""
    voltage, p_term, _, _, _ = compute_turret_voltage(
        filtered_tx=4.0, turret_vel=0.0, vy=0.0, aim_sign=1.0, config=_CFG)
    assert p_term > 0


def test_negative_error_produces_negative_p():
    """Target to the left -> negative P term."""
    voltage, p_term, _, _, _ = compute_turret_voltage(
        filtered_tx=-4.0, turret_vel=0.0, vy=0.0, aim_sign=1.0, config=_CFG)
    assert p_term < 0


def test_sqrt_compression():
    """Large errors grow slower than linear (sqrt compression)."""
    _, p_small, _, _, _ = compute_turret_voltage(
        filtered_tx=1.0, turret_vel=0.0, vy=0.0, aim_sign=1.0, config=_CFG)
    _, p_large, _, _, _ = compute_turret_voltage(
        filtered_tx=9.0, turret_vel=0.0, vy=0.0, aim_sign=1.0, config=_CFG)
    # Linear would give 9x; sqrt gives 3x
    ratio = p_large / p_small
    assert ratio < 9.0
    assert ratio == math.sqrt(9.0) / math.sqrt(1.0)


def test_zero_error_produces_zero_p():
    """No error -> no P output."""
    _, p_term, _, _, _ = compute_turret_voltage(
        filtered_tx=0.0, turret_vel=0.0, vy=0.0, aim_sign=1.0, config=_CFG)
    assert p_term == 0.0


# =========================================================================
# D term
# =========================================================================

def test_d_opposes_turret_velocity():
    """D term should brake -- oppose the turret's current motion."""
    _, _, d_term, _, _ = compute_turret_voltage(
        filtered_tx=0.0, turret_vel=2.0, vy=0.0, aim_sign=1.0, config=_CFG)
    assert d_term < 0

    _, _, d_term, _, _ = compute_turret_voltage(
        filtered_tx=0.0, turret_vel=-2.0, vy=0.0, aim_sign=1.0, config=_CFG)
    assert d_term > 0


def test_d_zero_when_stopped():
    """No turret motion -> no D output."""
    _, _, d_term, _, _ = compute_turret_voltage(
        filtered_tx=5.0, turret_vel=0.0, vy=0.0, aim_sign=1.0, config=_CFG)
    assert d_term == 0.0


# =========================================================================
# Feedforward
# =========================================================================

def test_ff_proportional_to_lateral_velocity():
    """FF should scale with robot lateral speed."""
    _, _, _, ff_slow, _ = compute_turret_voltage(
        filtered_tx=0.0, turret_vel=0.0, vy=1.0, aim_sign=1.0, config=_CFG)
    _, _, _, ff_fast, _ = compute_turret_voltage(
        filtered_tx=0.0, turret_vel=0.0, vy=2.0, aim_sign=1.0, config=_CFG)
    assert ff_fast == 2.0 * ff_slow


def test_ff_respects_aim_sign():
    """FF flips direction when aim_sign is inverted."""
    _, _, _, ff_normal, _ = compute_turret_voltage(
        filtered_tx=0.0, turret_vel=0.0, vy=1.0, aim_sign=1.0, config=_CFG)
    _, _, _, ff_inverted, _ = compute_turret_voltage(
        filtered_tx=0.0, turret_vel=0.0, vy=1.0, aim_sign=-1.0, config=_CFG)
    assert ff_normal == -ff_inverted


def test_ff_zero_when_stationary():
    """No lateral motion -> no FF output."""
    _, _, _, ff_term, _ = compute_turret_voltage(
        filtered_tx=5.0, turret_vel=0.0, vy=0.0, aim_sign=1.0, config=_CFG)
    assert ff_term == 0.0


# =========================================================================
# Clamping
# =========================================================================

def test_clamp_to_auto_voltage_when_driving():
    """Voltage clamps to max_auto_voltage when driving (not braking)."""
    voltage, _, _, _, raw = compute_turret_voltage(
        filtered_tx=100.0, turret_vel=0.0, vy=0.0, aim_sign=1.0, config=_CFG)
    assert abs(raw) > _CFG["turret_max_auto_voltage"]
    assert abs(voltage) == _CFG["turret_max_auto_voltage"]


def test_clamp_to_brake_voltage_when_opposing():
    """Voltage uses higher brake limit when opposing turret motion."""
    # Turret moving positive, voltage should be negative (braking)
    voltage, _, _, _, _ = compute_turret_voltage(
        filtered_tx=-100.0, turret_vel=2.0, vy=0.0, aim_sign=1.0, config=_CFG)
    # Should clamp to brake limit, not auto limit
    assert abs(voltage) <= _CFG["turret_max_brake_voltage"]


# =========================================================================
# Deadband compensation
# =========================================================================

def test_deadband_bumps_small_voltage():
    """When turret is stopped and voltage is below min_move, bump it up."""
    # Small error -> small P -> below min_move threshold
    # Use a config with meaningful deadband
    cfg = {**_CFG, "turret_max_auto_voltage": 5.0}
    voltage, _, _, _, _ = compute_turret_voltage(
        filtered_tx=0.1, turret_vel=0.0, vy=0.0, aim_sign=1.0, config=cfg)
    # Raw voltage from sqrt(0.1)*0.5 ~ 0.158, below min_move of 0.3
    assert abs(voltage) == cfg["turret_min_move_voltage"]


def test_deadband_does_not_fire_when_moving():
    """Deadband comp should not activate when turret is already moving."""
    voltage, _, _, _, _ = compute_turret_voltage(
        filtered_tx=0.1, turret_vel=1.0, vy=0.0, aim_sign=1.0, config=_CFG)
    # Turret is moving -- deadband should not bump voltage
    assert abs(voltage) != _CFG["turret_min_move_voltage"]
