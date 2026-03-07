"""
Manual launcher command -- maps joystick axis to RPS range.
Stick full forward (1) = max RPS, stick full back (-1) = min RPS.
"""

from typing import Callable

from commands2 import Command

from subsystems.launcher import Launcher
from constants import CON_MANUAL


class ManualLauncher(Command):
    """Run launcher at RPS derived from joystick position."""

    def __init__(self, launcher: Launcher, stick_supplier: Callable[[], float]):
        super().__init__()
        self.launcher = launcher
        self._stick_supplier = stick_supplier
        self.addRequirements(launcher)

    def execute(self):
        stick = self._stick_supplier()
        # Map stick [-1, 1] to [min_rps, max_rps]
        t = (stick + 1.0) / 2.0
        min_rps = CON_MANUAL["launcher_min_rps"]
        max_rps = CON_MANUAL["launcher_max_rps"]
        rps = min_rps + t * (max_rps - min_rps)
        self.launcher._set_velocity(rps)

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool):
        self.launcher._stop()
