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
from constants.debug import DEBUG
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

        # Match-critical telemetry (always published, rate-limited)
        if self._cycle_count % 10 == 1:
            SmartDashboard.putBoolean("AutoAim/HasTarget", target is not None)
            SmartDashboard.putNumber("AutoAim/LockedTagID",
                                    self._locked_tag_id if self._locked_tag_id is not None else -1)
        # Debug-only telemetry
        if DEBUG["debug_telemetry"]:
            if self._cycle_count % 10 == 1:
                SmartDashboard.putNumberArray("AutoAim/TagPriority", tag_priority)
            if self._cycle_count % 50 == 25:
                visible_ids = [t.tag_id for t in self.vision.get_all_targets()]
                SmartDashboard.putNumberArray("AutoAim/VisibleTags", visible_ids)

        # Truly lost -- no locked tag at all.  Stop the turret.
        if target is None and self._locked_tag_id is None:
            self._last_tx = 0.0
            self._filtered_tx = 0.0
            self.turret._set_voltage(0.0)
            self._cycle_count += 1
            if self._cycle_count % 2 == 0:
                _log.debug(
                    f"[AIM] t=-- tx=-- ftx=0.00 "
                    f"P=0.000 D=0.000 rv=0.000 v=0.000 [--] "
                    f"vel=0.000 pos={self.turret.get_position():.3f} "
                    f"lost=0"
                )
            return

        # Brief dropout -- tag temporarily missing but lock held.
        # Coast on last filtered_tx so the turret doesn't jerk to a stop
        # on every dropped Limelight frame.  Fall through to PD loop.

        # Update measurement only when we have a fresh target.
        # During brief dropouts, _filtered_tx holds its last value.
        _vx, _vy, _lead_deg = 0.0, 0.0, 0.0
        if target is not None:
            if target.tag_id in tag_offsets:
                self._last_tx = target.tx + tag_offsets[target.tag_id]["tx_offset"]
            else:
                self._last_tx = target.tx

            # Velocity compensation -- lead the target based on robot movement.
            if self._robot_velocity_supplier is not None:
                _vx, _vy = self._robot_velocity_supplier()
                flight_time = CON_SHOOTER["ball_flight_time"]
                dist = target.distance
                if dist > 0.5:
                    lead_m = _vy * flight_time
                    _lead_deg = math.degrees(math.atan2(lead_m, dist))
                    self._last_tx += _lead_deg
            if DEBUG["debug_telemetry"] and self._cycle_count % 10 == 5:
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
        # Sqrt P -- compresses large errors so voltage grows gradually
        # instead of saturating at the clamp.  Small errors (~1 deg) are
        # nearly linear; large errors get moderate voltage, not full blast.
        abs_tx = abs(self._filtered_tx)
        p_term = (math.sqrt(abs_tx) * math.copysign(1, self._filtered_tx)
                  * CON_SHOOTER["turret_p_gain"])
        d_term = -turret_vel * CON_SHOOTER["turret_d_velocity_gain"]

        # Velocity feedforward -- drive the turret proportionally to lateral
        # robot speed so P doesn't have to close the entire tracking gap.
        ff_term = 0.0
        if self._robot_velocity_supplier is not None:
            ff_term = _vy * CON_SHOOTER["turret_velocity_ff_gain"] * self._aim_sign

        raw_voltage = p_term * self._aim_sign + d_term + ff_term

        # Asymmetric voltage limits: allow more braking force than driving force.
        # When voltage opposes current turret motion, use the brake limit.
        if turret_vel != 0 and (raw_voltage * turret_vel) < 0:
            max_v = CON_SHOOTER["turret_max_brake_voltage"]
        else:
            max_v = CON_SHOOTER["turret_max_auto_voltage"]
        voltage = max(-max_v, min(raw_voltage, max_v))
        saturated = abs(raw_voltage) > max_v

        # Deadband compensation -- overcome static friction when starting
        # from standstill.  Once the turret is moving, dynamic friction is
        # much lower and the PD controller can output small voltages to
        # brake and settle without being overridden.
        min_move = CON_SHOOTER["turret_min_move_voltage"]
        if (abs(turret_vel) < 0.05
                and abs(voltage) > 0.01
                and abs(voltage) < min_move):
            voltage = math.copysign(min_move, voltage)

        self.turret._set_voltage(voltage)

        # Debug log every 2 cycles (~25 Hz)
        self._cycle_count += 1
        if self._cycle_count % 2 == 0:
            sat = "SAT" if saturated else "ok"
            raw_tx = f"{target.tx:.2f}" if target is not None else "--"
            coast = f" coast={self._lost_count}" if target is None else ""
            _log.debug(
                f"[AIM] t={self._locked_tag_id} "
                f"tx={raw_tx} ftx={self._filtered_tx:.2f} "
                f"P={p_term:.3f} D={d_term:.3f} FF={ff_term:.3f} "
                f"rv={raw_voltage:.3f} v={voltage:.3f} [{sat}]{coast} "
                f"vel={turret_vel:.3f} pos={self.turret.get_position():.3f} "
                f"vx={_vx:.2f} vy={_vy:.2f} ld={_lead_deg:.2f}"
            )
    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool):
        self.turret._stop()
        SmartDashboard.putBoolean("Shooter/AutoAim", False)
        _log.info(f"AutoAim DISABLED (interrupted={interrupted})")
