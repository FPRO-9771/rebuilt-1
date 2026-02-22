"""
Tests for shooter lookup table.
"""

import pytest
from subsystems.shooter_lookup import get_shooter_settings
from constants import CON_SHOOTER


def test_exact_table_distance():
    """Verify exact table entries return exact values."""
    table = CON_SHOOTER["distance_table"]

    for dist, expected_rps, expected_hood in table:
        rps, hood = get_shooter_settings(dist)
        assert rps == expected_rps
        assert hood == expected_hood


def test_interpolation_between_entries():
    """Verify linear interpolation between table entries."""
    # Midpoint between first two entries: (1.0, 30, 0.05) and (2.0, 45, 0.10)
    rps, hood = get_shooter_settings(1.5)

    assert rps == pytest.approx(37.5)   # midpoint of 30 and 45
    assert hood == pytest.approx(0.075)  # midpoint of 0.05 and 0.10


def test_clamp_below_min():
    """Verify distances below table min clamp to first entry."""
    table = CON_SHOOTER["distance_table"]
    first_rps = table[0][1]
    first_hood = table[0][2]

    rps, hood = get_shooter_settings(0.0)
    assert rps == first_rps
    assert hood == first_hood

    rps, hood = get_shooter_settings(-5.0)
    assert rps == first_rps
    assert hood == first_hood


def test_clamp_above_max():
    """Verify distances above table max clamp to last entry."""
    table = CON_SHOOTER["distance_table"]
    last_rps = table[-1][1]
    last_hood = table[-1][2]

    rps, hood = get_shooter_settings(100.0)
    assert rps == last_rps
    assert hood == last_hood


def test_quarter_interpolation():
    """Verify interpolation at 25% between entries."""
    # 25% between (1.0, 30, 0.05) and (2.0, 45, 0.10) = distance 1.25
    rps, hood = get_shooter_settings(1.25)

    assert rps == pytest.approx(33.75)   # 30 + 0.25 * 15
    assert hood == pytest.approx(0.0625)  # 0.05 + 0.25 * 0.05
