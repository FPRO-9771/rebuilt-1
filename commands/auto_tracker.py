"""
Auto-tracker command -- turret default command for teleop.
Continuously aims turret at qualifying AprilTags using PD control.
Uses priority-based targeting with stickiness to avoid oscillation.
Publishes a lock boolean to SmartDashboard for drive team readiness.
"""

from typing import Callable

from commands2 import Command
from wpilib import DriverStation, SmartDashboard

from handlers.vision import VisionProvider
from subsystems.turret import Turret
from constants import CON_SHOOTER
from constants.match import TARGET_LOCK_LOST_CYCLES
from utils.logger import get_logger

_log = get_logger("auto_tracker")


class AutoTracker(Command):
    """
    Default turret command -- aims at scoring tags via PD control.

    Uses priority-based targeting: the tag_priority_supplier provides an
    ordered list of AprilTag IDs from match setup. The tracker locks onto
    the first visible tag in that list and stays locked until the tag is
    lost for several consecutive cycles (stickiness).

    Only requires turret. Manual turret override (left stick X)
    interrupts this via WPILib requirements; when released, this
    default command resumes automatically.
    """

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
        self._last_distance = 2.0
        self._target_visible = False
        self._locked_tag_id = None
        self._lost_count = 0

        self.addRequirements(turret)

    def initialize(self):
        self._last_tx = 0.0
        self._prev_tx = 0.0
        self._last_distance = 2.0
        self._target_visible = False
        self._locked_tag_id = None
        self._lost_count = 0
        _log.info("AutoTracker ENABLED")

    def _select_target(self):
        """Pick a target using priority + stickiness logic."""
        tag_priority = self._tag_priority_supplier()

        # If we have a lock, try to keep it
        if self._locked_tag_id is not None:
            target = self.vision.get_target(self._locked_tag_id)
            if target is not None:
                self._lost_count = 0
                return target

            # Locked tag not visible -- count cycles before unlocking
            self._lost_count += 1
            if self._lost_count < TARGET_LOCK_LOST_CYCLES:
                return None  # Hold lock, no new data
            # Lock expired
            _log.debug(f"Lost lock on tag {self._locked_tag_id}")
            self._locked_tag_id = None
            self._lost_count = 0

        # No lock -- find the highest-priority visible tag
        for tag_id in tag_priority:
            target = self.vision.get_target(tag_id)
            if target is not None:
                self._locked_tag_id = tag_id
                _log.debug(f"Locked onto tag {tag_id}")
                return target

        return None

    def execute(self):
        # Only track during teleop
        if not DriverStation.isTeleopEnabled():
            self._target_visible = False
            self._last_tx = 0.0
            self._prev_tx = 0.0
            self._locked_tag_id = None
            self._lost_count = 0
            SmartDashboard.putBoolean("Shooter/Lock", False)
            SmartDashboard.putNumber("Shooter/Locked Tag", -1)
            return

        # 1. Select target using priority + stickiness
        target = self._select_target()
        tag_offsets = self._tag_offsets_supplier()

        # 2. Apply per-tag offsets if we have a valid target
        if target is not None and target.tag_id in tag_offsets:
            offsets = tag_offsets[target.tag_id]
            self._last_tx = target.tx + offsets["tx_offset"]
            self._last_distance = target.distance + offsets["distance_offset"]
            self._target_visible = True
        elif target is not None:
            self._last_tx = target.tx
            self._last_distance = target.distance
            self._target_visible = True
        else:
            self._target_visible = False
            self._last_tx = 0.0

        # 3. PD control for turret aim
        p_term = self._last_tx * CON_SHOOTER["turret_p_gain"]
        d_term = (self._last_tx - self._prev_tx) * CON_SHOOTER["turret_d_gain"]
        self._prev_tx = self._last_tx

        turret_voltage = (p_term + d_term) * self._aim_sign
        max_auto_v = CON_SHOOTER["turret_max_auto_voltage"]
        turret_voltage = max(-max_auto_v, min(turret_voltage, max_auto_v))
        self.turret._set_voltage(turret_voltage)

        # 4. Publish lock and target status
        SmartDashboard.putBoolean("Shooter/Lock", self.is_locked())
        locked_id = self._locked_tag_id if self._locked_tag_id is not None else -1
        SmartDashboard.putNumber("Shooter/Locked Tag", locked_id)

    def is_locked(self) -> bool:
        """Target visible, aligned, and distance within table range."""
        if not self._target_visible:
            return False
        table = CON_SHOOTER["distance_table"]
        min_dist = table[0][0]
        max_dist = table[-1][0]
        in_range = min_dist <= self._last_distance <= max_dist
        aligned = abs(self._last_tx) <= CON_SHOOTER["turret_alignment_tolerance"]
        return aligned and in_range

    def get_distance(self) -> float:
        """Current tracked distance for ShootCommand."""
        return self._last_distance

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool):
        _log.info(f"AutoTracker DISABLED (interrupted={interrupted})")
        self.turret._stop()
        SmartDashboard.putBoolean("Shooter/Lock", False)
        SmartDashboard.putNumber("Shooter/Locked Tag", -1)
