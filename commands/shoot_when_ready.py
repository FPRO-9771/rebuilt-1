"""
Shoot-when-ready command -- hold to engage.
Spins up launcher immediately from vision distance. Runs feeders
only when launcher is at speed AND turret is on target.
Release to stop everything.
"""

from typing import Callable

from commands2 import Command

from handlers.vision import VisionProvider
from subsystems.launcher import Launcher
from subsystems.hood import Hood
from subsystems.h_feed import HFeed
from subsystems.v_feed import VFeed
from subsystems.shooter_lookup import get_shooter_settings
from constants import CON_H_FEED, CON_V_FEED
from utils.logger import get_logger

_log = get_logger("shoot_when_ready")


class ShootWhenReady(Command):
    """Spins launcher, feeds only when at speed and on target."""

    def __init__(
        self,
        launcher: Launcher,
        hood: Hood,
        h_feed: HFeed,
        v_feed: VFeed,
        vision: VisionProvider,
        tag_priority_supplier: Callable[[], list[int]],
        on_target_supplier: Callable[[], bool],
    ):
        super().__init__()
        self.launcher = launcher
        self.hood = hood
        self.h_feed = h_feed
        self.v_feed = v_feed
        self.vision = vision
        self._tag_priority_supplier = tag_priority_supplier
        self._on_target_supplier = on_target_supplier
        self._last_distance = 2.0
        self._feeding = False
        self.addRequirements(launcher, hood, h_feed, v_feed)

    def initialize(self):
        self._last_distance = 2.0
        self._feeding = False
        _log.info("ShootWhenReady ENABLED")

    def execute(self):
        # Update distance from best visible tag
        for tag_id in self._tag_priority_supplier():
            target = self.vision.get_target(tag_id)
            if target is not None:
                self._last_distance = target.distance
                break

        # Always spin up launcher and set hood
        rps, hood_pos = get_shooter_settings(self._last_distance)
        self.launcher._set_velocity(rps)
        self.hood._set_position(hood_pos)

        # Feed only when ready
        ready = (self._on_target_supplier()
                 and self.launcher.is_at_speed(rps))

        if ready and not self._feeding:
            _log.debug("Ready -- feeding")
            self._feeding = True
        elif not ready and self._feeding:
            _log.debug("Not ready -- stopping feed")
            self._feeding = False

        if self._feeding:
            self.h_feed._set_voltage(CON_H_FEED["feed_voltage"])
            self.v_feed._set_voltage(CON_V_FEED["feed_voltage"])
        else:
            self.h_feed._stop()
            self.v_feed._stop()

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool):
        self.launcher._stop()
        self.hood._stop()
        self.h_feed._stop()
        self.v_feed._stop()
        _log.info(f"ShootWhenReady DISABLED (interrupted={interrupted})")
