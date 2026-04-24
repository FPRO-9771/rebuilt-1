"""
Assist-mode target selection for the turret.

Normal auto-aim points the turret at the alliance Hub. When the shooter is
inside the neutral zone in teleop, Assist mode re-targets the nearest
scoring-zone corner of our own alliance, so the turret can lob Fuel back
to our side for later collection.

Pure math -- no WPILib dependencies, easy to unit test.
"""

from constants.match import (
    NEUTRAL_ZONE_X_MIN,
    NEUTRAL_ZONE_X_MAX,
    NEUTRAL_ZONE_HYSTERESIS_M,
)


class AssistAimSelector:
    """Picks Hub vs nearest scoring-zone corner, with hysteresis on the
    neutral-zone boundary so the target does not flicker cycle to cycle."""

    def __init__(self):
        self._in_neutral = False

    @property
    def in_assist_mode(self) -> bool:
        """True if the latched state is 'aim at a corner' (Assist mode)."""
        return self._in_neutral

    def select_target(self, shooter_xy, hub_xy, corners, is_teleop: bool):
        """Return (target_x, target_y) for the current cycle.

        shooter_xy: (x, y) shooter field position in meters
        hub_xy:     (x, y) alliance Hub position in meters
        corners:    list of (x, y) alliance scoring-zone corner positions
        is_teleop:  True if the match is currently in teleop. Assist mode is
                    teleop-only; in auto or disabled we always return hub_xy.
        """
        if not is_teleop or not corners:
            self._in_neutral = False
            return hub_xy

        sx, _sy = shooter_xy
        if self._in_neutral:
            if (sx < NEUTRAL_ZONE_X_MIN - NEUTRAL_ZONE_HYSTERESIS_M
                    or sx > NEUTRAL_ZONE_X_MAX + NEUTRAL_ZONE_HYSTERESIS_M):
                self._in_neutral = False
        else:
            if NEUTRAL_ZONE_X_MIN <= sx <= NEUTRAL_ZONE_X_MAX:
                self._in_neutral = True

        if not self._in_neutral:
            return hub_xy
        return _nearest(shooter_xy, corners)


def _nearest(point, candidates):
    """Return the candidate (x, y) with the smallest squared distance to point."""
    px, py = point
    return min(candidates,
               key=lambda c: (c[0] - px) ** 2 + (c[1] - py) ** 2)
