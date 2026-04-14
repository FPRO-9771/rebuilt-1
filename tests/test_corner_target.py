"""
Tests for CornerAimSelector -- neutral-zone corner aim selection.
Pure math, no hardware. Expected values are derived from constants so
that tuning neutral-zone bounds never requires editing this test.
"""

from calculations.corner_target import CornerAimSelector
from constants.match import (
    ALLIANCES,
    NEUTRAL_ZONE_X_MIN,
    NEUTRAL_ZONE_X_MAX,
    NEUTRAL_ZONE_HYSTERESIS_M,
)


def _blue_hub():
    b = ALLIANCES["Blue"]
    return (b["target_x"], b["target_y"])


def _blue_corners():
    return ALLIANCES["Blue"]["corners"]


def _red_hub():
    r = ALLIANCES["Red"]
    return (r["target_x"], r["target_y"])


def _red_corners():
    return ALLIANCES["Red"]["corners"]


def _neutral_x_midpoint():
    return (NEUTRAL_ZONE_X_MIN + NEUTRAL_ZONE_X_MAX) / 2


def test_outside_zone_returns_hub():
    sel = CornerAimSelector()
    hub = _blue_hub()
    # Just outside the min boundary on the blue (near) side.
    shooter_xy = (NEUTRAL_ZONE_X_MIN - 1.0, 4.0)
    out = sel.select_target(shooter_xy, hub, _blue_corners(), is_teleop=True)
    assert out == hub
    assert sel.in_corner_mode is False


def test_inside_zone_returns_nearest_blue_corner_top():
    sel = CornerAimSelector()
    hub = _blue_hub()
    corners = _blue_corners()
    # High Y -> nearest corner should be the top one (max y).
    top_corner = max(corners, key=lambda c: c[1])
    shooter_xy = (_neutral_x_midpoint(), 6.5)
    out = sel.select_target(shooter_xy, hub, corners, is_teleop=True)
    assert out == top_corner
    assert sel.in_corner_mode is True


def test_inside_zone_returns_nearest_blue_corner_bottom():
    sel = CornerAimSelector()
    hub = _blue_hub()
    corners = _blue_corners()
    bottom_corner = min(corners, key=lambda c: c[1])
    shooter_xy = (_neutral_x_midpoint(), 1.0)
    out = sel.select_target(shooter_xy, hub, corners, is_teleop=True)
    assert out == bottom_corner


def test_inside_zone_returns_nearest_red_corner():
    sel = CornerAimSelector()
    hub = _red_hub()
    corners = _red_corners()
    top_corner = max(corners, key=lambda c: c[1])
    shooter_xy = (_neutral_x_midpoint(), 6.5)
    out = sel.select_target(shooter_xy, hub, corners, is_teleop=True)
    assert out == top_corner


def test_not_teleop_always_returns_hub_and_clears_latch():
    sel = CornerAimSelector()
    hub = _blue_hub()
    corners = _blue_corners()

    # First latch corner mode in teleop.
    sel.select_target((_neutral_x_midpoint(), 4.0), hub, corners,
                      is_teleop=True)
    assert sel.in_corner_mode is True

    # Then drop out of teleop -- should return hub and clear the latch.
    out = sel.select_target((_neutral_x_midpoint(), 4.0), hub, corners,
                            is_teleop=False)
    assert out == hub
    assert sel.in_corner_mode is False


def test_hysteresis_holds_corner_mode_inside_buffer():
    """After latching corner mode, crossing the boundary by less than the
    hysteresis buffer should NOT fall back to hub aim."""
    sel = CornerAimSelector()
    hub = _blue_hub()
    corners = _blue_corners()

    # Latch inside the zone.
    sel.select_target((_neutral_x_midpoint(), 4.0), hub, corners,
                      is_teleop=True)
    assert sel.in_corner_mode is True

    # Step just past the min edge but inside the hysteresis buffer.
    x_just_outside = NEUTRAL_ZONE_X_MIN - (NEUTRAL_ZONE_HYSTERESIS_M / 2)
    out = sel.select_target((x_just_outside, 4.0), hub, corners,
                            is_teleop=True)
    assert sel.in_corner_mode is True
    assert out in corners


def test_hysteresis_releases_past_buffer():
    """Stepping past the buffer on either side should release the latch."""
    sel = CornerAimSelector()
    hub = _blue_hub()
    corners = _blue_corners()

    sel.select_target((_neutral_x_midpoint(), 4.0), hub, corners,
                      is_teleop=True)

    # Low side: well past min - hysteresis.
    x_below = NEUTRAL_ZONE_X_MIN - NEUTRAL_ZONE_HYSTERESIS_M - 0.1
    out = sel.select_target((x_below, 4.0), hub, corners, is_teleop=True)
    assert out == hub
    assert sel.in_corner_mode is False

    # Re-latch, then exit the high side.
    sel.select_target((_neutral_x_midpoint(), 4.0), hub, corners,
                      is_teleop=True)
    x_above = NEUTRAL_ZONE_X_MAX + NEUTRAL_ZONE_HYSTERESIS_M + 0.1
    out = sel.select_target((x_above, 4.0), hub, corners, is_teleop=True)
    assert out == hub
    assert sel.in_corner_mode is False


def test_empty_corners_falls_back_to_hub():
    sel = CornerAimSelector()
    hub = _blue_hub()
    out = sel.select_target((_neutral_x_midpoint(), 4.0), hub, (),
                            is_teleop=True)
    assert out == hub
    assert sel.in_corner_mode is False
