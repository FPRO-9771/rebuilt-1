"""
Manual hood command -- nudge hood position with joystick taps.
Each stick deflection past the deadband nudges the target position by one step.
The hood holds at the target position via closed-loop control between nudges.
"""

from typing import Callable

from commands2 import Command

from subsystems.hood import Hood
from constants import CON_MANUAL, CON_HOOD
from utils.logger import get_logger

_log = get_logger("manual_hood")


class ManualHood(Command):
    """Nudge hood position with joystick axis. Holds position between nudges."""

    def __init__(self, hood: Hood, stick_supplier: Callable[[], float],
                 deadband: float = 0.1):
        super().__init__()
        self.hood = hood
        self._stick_supplier = stick_supplier
        self._deadband = deadband
        self._target = CON_MANUAL["hood_default_position"]
        self._was_active = False
        self.addRequirements(hood)

    def initialize(self):
        self._target = CON_MANUAL["hood_default_position"]
        self._was_active = False
        _log.info(f"manual hood start target={self._target:.4f}")

    def execute(self):
        stick = self._stick_supplier()
        is_active = abs(stick) > self._deadband

        # Edge-triggered: nudge once when stick crosses deadband
        if is_active and not self._was_active:
            step = CON_MANUAL["hood_position_step"]
            if stick > 0:
                self._target += step
            else:
                self._target -= step
            # Clamp to hood limits
            self._target = max(CON_HOOD["min_position"],
                               min(self._target, CON_HOOD["max_position"]))
            _log.debug(f"nudge target={self._target:.4f}")

        self._was_active = is_active
        self.hood._set_position(self._target)

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool):
        self.hood._stop()
