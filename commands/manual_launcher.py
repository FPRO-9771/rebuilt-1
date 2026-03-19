"""
Manual launcher command -- maps joystick axis to RPS via distance table.
Fallback for when feed subsystems are not wired. Does not control hood or feeds.
Stick full forward (1) = max distance RPS, stick full back (-1) = min distance RPS.
"""

from typing import Callable

from commands2 import Command

from subsystems.launcher import Launcher
from commands.manual_shoot import _stick_to_distance
from subsystems.shooter_lookup import get_shooter_settings


class ManualLauncher(Command):
    """Run launcher at RPS derived from joystick position via distance table."""

    def __init__(self, launcher: Launcher, stick_supplier: Callable[[], float]):
        super().__init__()
        self.launcher = launcher
        self._stick_supplier = stick_supplier
        self.addRequirements(launcher)

    def execute(self):
        stick = self._stick_supplier()
        distance = _stick_to_distance(stick)
        rps, _hood = get_shooter_settings(distance)
        self.launcher._set_velocity(rps)

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool):
        self.launcher._stop()
