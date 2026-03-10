"""
Auto-aim command -- PD control to aim turret at AprilTags.
Toggleable via operator button. Publishes status to SmartDashboard.
Does NOT track distance or lock status (that is auto_shoot's job).
"""

import math
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
        robot_velocity_supplier: Callable[[], tuple[float, float]] | None = None,
    ):
        super().__init__()
        self.turret = turret
        self.vision = vision
        self._tag_priority_supplier = tag_priority_supplier
        self._tag_offsets_supplier = tag_offsets_supplier
        self._robot_velocity_supplier = robot_velocity_supplier
        self._aim_sign = -1.0 if CON_SHOOTER["turret_aim_inverted"] else 1.0

        self._last_tx = 0.0
        self._filtered_tx = 0.0
        self._locked_tag_id = None
        self._lost_count = 0
        self._cycle_count = 0

        self.addRequirements(turret)

        # Publish diagnostic keys at boot so Elastic can find them immediately
        SmartDashboard.putNumberArray("AutoAim/TagPriority", [])
        SmartDashboard.putNumber("AutoAim/LockedTagID", -1)
        SmartDashboard.putBoolean("AutoAim/HasTarget", False)
        SmartDashboard.putNumberArray("AutoAim/VisibleTags", [])

    def initialize(self):
        self._last_tx = 0.0
        self._filtered_tx = 0.0
        self._locked_tag_id = None
        self._lost_count = 0
        self._cycle_count = 0
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
                # Seed filter with new tag's actual tx so we don't inherit
                # a stale value from the previous tag and spike the output.
                self._filtered_tx = target.tx
                _log.debug(f"Locked onto tag {tag_id} tx={target.tx:.2f}")
                return target
        return None

    def execute(self):
        target = self._select_target()
        tag_offsets = self._tag_offsets_supplier()
        tag_priority = self._tag_priority_supplier()

        # Diagnostic telemetry -- shows what the aimer is actually doing
        SmartDashboard.putNumberArray("AutoAim/TagPriority", tag_priority)
        SmartDashboard.putNumber("AutoAim/LockedTagID",
                                self._locked_tag_id if self._locked_tag_id is not None else -1)
        SmartDashboard.putBoolean("AutoAim/HasTarget", target is not None)
        # Rate-limit get_all_targets() -- it makes a blocking network call to
        # Limelight and can cause 100+ ms loop overruns if called every cycle.
        if self._cycle_count % 25 == 0:
            visible_ids = [t.tag_id for t in self.vision.get_all_targets()]
            SmartDashboard.putNumberArray("AutoAim/VisibleTags", visible_ids)

        if target is not None and target.tag_id in tag_offsets:
            self._last_tx = target.tx + tag_offsets[target.tag_id]["tx_offset"]
        elif target is not None:
            self._last_tx = target.tx
        else:
            self._last_tx = 0.0

        # Velocity compensation -- lead the target based on robot movement.
        # If the robot is strafing right, the target appears to drift left,
        # so we aim further right to compensate for ball flight time.
        _vx, _vy, _lead_deg = 0.0, 0.0, 0.0
        if target is not None and self._robot_velocity_supplier is not None:
            _vx, _vy = self._robot_velocity_supplier()
            flight_time = CON_SHOOTER["ball_flight_time"]
            dist = target.distance
            if dist > 0.5:
                lead_m = _vy * flight_time
                _lead_deg = math.degrees(math.atan2(lead_m, dist))
                self._last_tx += _lead_deg
        SmartDashboard.putNumber("AutoAim/RobotVX", _vx)
        SmartDashboard.putNumber("AutoAim/RobotVY", _vy)
        SmartDashboard.putNumber("AutoAim/LeadDeg", _lead_deg)

        # Smooth tx with EMA filter to reduce noise-induced derivative kick
        alpha = CON_SHOOTER["turret_tx_filter_alpha"]
        self._filtered_tx = alpha * self._last_tx + (1 - alpha) * self._filtered_tx

        # PD control -- P on tx error, D on turret encoder velocity.
        # Velocity-based D brakes the turret's own motion directly, which is
        # more stable than D on tx (which mixes target motion with turret motion).
        turret_vel = self.turret.get_velocity()
        p_term = self._filtered_tx * CON_SHOOTER["turret_p_gain"]
        d_term = -turret_vel * CON_SHOOTER["turret_d_velocity_gain"]

        voltage = p_term * self._aim_sign + d_term

        # Asymmetric voltage limits: allow more braking force than driving force.
        # When voltage opposes current turret motion, use the brake limit.
        if turret_vel != 0 and (voltage * turret_vel) < 0:
            max_v = CON_SHOOTER["turret_max_brake_voltage"]
        else:
            max_v = CON_SHOOTER["turret_max_auto_voltage"]
        voltage = max(-max_v, min(voltage, max_v))

        self.turret._set_voltage(voltage)

        # Debug log every 2 cycles (~25 Hz)
        self._cycle_count += 1
        if self._cycle_count % 2 == 0:
            raw_tx = f"{target.tx:.2f}" if target is not None else "none"
            _log.debug(
                f"[AIM] tag={self._locked_tag_id} "
                f"raw_tx={raw_tx} "
                f"filtered_tx={self._filtered_tx:.2f} "
                f"P={p_term:.3f} D={d_term:.3f} "
                f"vel={turret_vel:.3f} "
                f"voltage={voltage:.3f} "
                f"lost={self._lost_count} "
                f"| robot vx={_vx:.2f} vy={_vy:.2f} lead={_lead_deg:.2f}deg"
            )
    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool):
        self.turret._stop()
        SmartDashboard.putBoolean("Shooter/AutoAim", False)
        _log.info(f"AutoAim DISABLED (interrupted={interrupted})")
