"""
Auto-aim command -- PD control to aim turret at AprilTags.
Toggleable via operator button. Publishes status to SmartDashboard.
Does NOT track distance or lock status (that is auto_shoot's job).
"""

from typing import Callable

from commands2 import Command
from wpilib import SmartDashboard

from handlers.vision import VisionProvider
from subsystems.turret import Turret
from constants import CON_SHOOTER
from constants.match import TARGET_LOCK_LOST_CYCLES
from utils.logger import get_logger

_log = get_logger("auto_aim")


class AutoAim(Command):
    """PD turret tracking -- aims at highest-priority visible AprilTag."""

    def __init__(
        self,
        turret: Turret,
        vision: VisionProvider,
        tag_priority_supplier: Callable[[], list[int]],
        tag_offsets_supplier: Callable[[], dict],
    ):
        super().__init__()
        self.turret = turret
        self.vision = vision
        self._tag_priority_supplier = tag_priority_supplier
        self._tag_offsets_supplier = tag_offsets_supplier
        self._aim_sign = -1.0 if CON_SHOOTER["turret_aim_inverted"] else 1.0

        self._last_tx = 0.0
        self._prev_tx = 0.0
        self._locked_tag_id = None
        self._lost_count = 0

        self.addRequirements(turret)

    def initialize(self):
        self._last_tx = 0.0
        self._prev_tx = 0.0
        self._locked_tag_id = None
        self._lost_count = 0
        SmartDashboard.putBoolean("Shooter/AutoAim", True)
        _log.info("AutoAim ENABLED")

    def _select_target(self):
        """Pick target using priority + stickiness."""
        tag_priority = self._tag_priority_supplier()

        if self._locked_tag_id is not None:
            target = self.vision.get_target(self._locked_tag_id)
            if target is not None:
                self._lost_count = 0
                return target
            self._lost_count += 1
            if self._lost_count < TARGET_LOCK_LOST_CYCLES:
                return None
            _log.debug(f"Lost lock on tag {self._locked_tag_id}")
            self._locked_tag_id = None
            self._lost_count = 0

        for tag_id in tag_priority:
            target = self.vision.get_target(tag_id)
            if target is not None:
                self._locked_tag_id = tag_id
                _log.debug(f"Locked onto tag {tag_id}")
                return target
        return None

    def execute(self):
        target = self._select_target()
        tag_offsets = self._tag_offsets_supplier()

        if target is not None and target.tag_id in tag_offsets:
            self._last_tx = target.tx + tag_offsets[target.tag_id]["tx_offset"]
        elif target is not None:
            self._last_tx = target.tx
        else:
            self._last_tx = 0.0

        # PD control
        p_term = self._last_tx * CON_SHOOTER["turret_p_gain"]
        d_term = (self._last_tx - self._prev_tx) * CON_SHOOTER["turret_d_gain"]
        self._prev_tx = self._last_tx

        voltage = (p_term + d_term) * self._aim_sign
        max_v = CON_SHOOTER["turret_max_auto_voltage"]
        voltage = max(-max_v, min(voltage, max_v))
        self.turret._set_voltage(voltage)

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool):
        self.turret._stop()
        SmartDashboard.putBoolean("Shooter/AutoAim", False)
        _log.info(f"AutoAim DISABLED (interrupted={interrupted})")
