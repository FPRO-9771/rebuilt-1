"""
Auto-shoot command -- sets launcher speed and hood from pose-based distance.
Hold to engage. Reads a ShootContext from a supplier (pose math with velocity
correction), looks up launcher RPS and hood position from the distance table.
"""

from typing import Callable

from commands2 import Command

from subsystems.launcher import Launcher
from subsystems.hood import Hood
from subsystems.shooter_lookup import get_shooter_settings
from telemetry.auto_aim_logging import log_shoot
from utils.logger import get_logger

_log = get_logger("auto_shoot")


class AutoShoot(Command):
    """Reads pose-based distance, sets launcher RPS and hood from lookup table."""

    def __init__(
        self,
        launcher: Launcher,
        hood: Hood,
        context_supplier: Callable,
    ):
        super().__init__()
        self.launcher = launcher
        self.hood = hood
        self._context_supplier = context_supplier
        self._cycle_count = 0
        self.addRequirements(launcher, hood)

    def initialize(self):
        self._cycle_count = 0
        _log.info("AutoShoot ENABLED")

    def execute(self):
        ctx = self._context_supplier()
        rps, hood_pos = get_shooter_settings(ctx.corrected_distance)
        self.launcher._set_velocity(rps)
        self.hood._set_position(hood_pos)

        log_shoot(
            self._cycle_count,
            ctx=ctx,
            rps=rps,
            hood_pos=hood_pos,
            actual_rps=self.launcher.get_velocity(),
            at_speed=self.launcher.is_at_speed(rps),
        )
        self._cycle_count += 1

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool):
        self.launcher._stop()
        self.hood._stop()
        _log.info(f"AutoShoot DISABLED (interrupted={interrupted})")
