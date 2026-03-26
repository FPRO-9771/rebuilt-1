"""
Tests for shooter lookup table.

Uses the test distance table from conftest (not the real one):
    (1.0, 20, 0.25)
    (2.0, 40, 0.33)
    (3.0, 60, 0.38)
    (4.0, 80, 0.40)
"""

import pytest
from subsystems.shooter_lookup import get_shooter_settings, get_flight_time
from tests.conftest import TEST_CON_DISTANCE_TABLE

_TABLE = TEST_CON_DISTANCE_TABLE["distance_table"]


def test_exact_table_distance():
    """Verify exact table entries return exact values."""
    for dist, expected_rps, _ft in _TABLE:
        rps = get_shooter_settings(dist)
        assert rps == expected_rps


def test_interpolation_between_entries():
    """Verify linear interpolation between table entries."""
    # Midpoint between first two: (1.0, 20) and (2.0, 40)
    rps = get_shooter_settings(1.5)

    assert rps == pytest.approx(30.0)   # midpoint of 20 and 40


def test_clamp_below_min():
    """Verify distances below table min clamp to first entry."""
    first_rps = _TABLE[0][1]

    rps = get_shooter_settings(0.0)
    assert rps == first_rps

    rps = get_shooter_settings(-5.0)
    assert rps == first_rps


def test_clamp_above_max():
    """Verify distances above table max clamp to last entry."""
    last_rps = _TABLE[-1][1]

    rps = get_shooter_settings(100.0)
    assert rps == last_rps


def test_quarter_interpolation():
    """Verify interpolation at 25% between entries."""
    # 25% between (1.0, 20) and (2.0, 40) = distance 1.25
    rps = get_shooter_settings(1.25)

    assert rps == pytest.approx(25.0)    # 20 + 0.25 * 20


# =========================================================================
# Flight time lookup
# =========================================================================

def test_flight_time_exact():
    """Verify exact table entries return exact flight time."""
    for dist, _rps, expected_ft in _TABLE:
        assert get_flight_time(dist) == expected_ft


def test_flight_time_interpolation():
    """Verify flight time interpolates between entries."""
    # Midpoint between (1.0, ..., 0.25) and (2.0, ..., 0.33)
    assert get_flight_time(1.5) == pytest.approx(0.29)


def test_flight_time_clamp_below():
    """Flight time clamps to first entry below table range."""
    assert get_flight_time(0.0) == _TABLE[0][2]


def test_flight_time_clamp_above():
    """Flight time clamps to last entry above table range."""
    assert get_flight_time(100.0) == _TABLE[-1][2]
