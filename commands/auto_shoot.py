"""
Auto-shoot command -- sets launcher speed and hood from vision distance.
Hold to engage. Reads distance from highest-priority visible tag,
looks up launcher RPS and hood position from the distance table.
"""

from typing import Callable

from commands2 import Command

from handlers.vision import VisionProvider
from subsystems.launcher import Launcher
from subsystems.hood import Hood
from subsystems.shooter_lookup import get_shooter_settings
from utils.logger import get_logger

_log = get_logger("auto_shoot")


class AutoShoot(Command):
    """Reads vision distance, sets launcher RPS and hood from lookup table."""

    def __init__(
        self,
        launcher: Launcher,
        hood: Hood,
        vision: VisionProvider,
        tag_priority_supplier: Callable[[], list[int]],
    ):
        super().__init__()
        self.launcher = launcher
        self.hood = hood
        self.vision = vision
        self._tag_priority_supplier = tag_priority_supplier
        self._last_distance = 2.0
        self.addRequirements(launcher, hood)

    def initialize(self):
        self._last_distance = 2.0
        _log.info("AutoShoot ENABLED")

    def execute(self):
        # Find distance from highest-priority visible tag
        for tag_id in self._tag_priority_supplier():
            target = self.vision.get_target(tag_id)
            if target is not None:
                self._last_distance = target.distance
                break

        rps, hood_pos = get_shooter_settings(self._last_distance)
        self.launcher._set_velocity(rps)
        self.hood._set_position(hood_pos)

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool):
        self.launcher._stop()
        self.hood._stop()
        _log.info(f"AutoShoot DISABLED (interrupted={interrupted})")
