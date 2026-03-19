"""
Manual shoot command -- spins launcher from joystick, auto-feeds when at speed.

Maps the joystick Y axis to a virtual distance using the shooter distance
table. The distance table provides both launcher RPS and hood position.
Once the flywheel reaches speed, both H feed and V feed activate
automatically. Feeds stop when launcher drops below speed or the command ends.
"""

from typing import Callable

from commands2 import Command

from subsystems.launcher import Launcher
from subsystems.hood import Hood
from subsystems.h_feed import HFeed
from subsystems.v_feed import VFeed
from subsystems.shooter_lookup import get_shooter_settings
from constants import CON_H_FEED, CON_V_FEED
from constants.shooter import CON_SHOOTER


def _stick_to_distance(stick: float) -> float:
    """Map stick [-1, 1] to virtual distance using a two-segment linear map.

    Stick -1 = min distance, 0 = center distance, +1 = max distance.
    Center does not have to be the midpoint of min/max.
    """
    min_d = CON_SHOOTER["manual_min_distance"]
    ctr_d = CON_SHOOTER["manual_center_distance"]
    max_d = CON_SHOOTER["manual_max_distance"]
    if stick <= 0:
        # Map [-1, 0] to [min_d, ctr_d]
        t = stick + 1.0  # 0..1
        return min_d + t * (ctr_d - min_d)
    else:
        # Map [0, 1] to [ctr_d, max_d]
        return ctr_d + stick * (max_d - ctr_d)


class ManualShoot(Command):
    """Spin launcher from stick input via distance table, auto-feed when at speed."""

    def __init__(self, launcher: Launcher, hood: Hood,
                 h_feed: HFeed, v_feed: VFeed,
                 stick_supplier: Callable[[], float]):
        super().__init__()
        self.launcher = launcher
        self.hood = hood
        self.h_feed = h_feed
        self.v_feed = v_feed
        self._stick_supplier = stick_supplier
        self._feeding = False
        self.addRequirements(launcher, hood, h_feed, v_feed)

    def execute(self):
        stick = self._stick_supplier()
        distance = _stick_to_distance(stick)
        target_rps, hood_pos = get_shooter_settings(distance)
        self.launcher._set_velocity(target_rps)
        self.hood._set_position(hood_pos)

        # Run feeds when launcher is at speed
        if self.launcher.is_at_speed(target_rps):
            self.h_feed._set_voltage(CON_H_FEED["feed_voltage"])
            self.v_feed._set_voltage(CON_V_FEED["feed_voltage"])
            self._feeding = True
        else:
            if self._feeding:
                self.h_feed._stop()
                self.v_feed._stop()
                self._feeding = False

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool):
        self.launcher._stop()
        self.hood._stop()
        self.h_feed._stop()
        self.v_feed._stop()
