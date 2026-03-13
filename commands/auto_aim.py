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
from calculations.velocity_lead import compute_velocity_lead
from calculations.turret_pd import compute_turret_voltage
from constants import CON_SHOOTER
from constants.match import TARGET_LOCK_LOST_CYCLES
from telemetry.auto_aim_telemetry import (
    init_auto_aim_keys, publish_auto_aim, publish_velocity_debug,
)
from telemetry.auto_aim_logging import log_lost, log_hold, log_drive
from calculations.parallax import compute_parallax_correction
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

        # Correction state from last _update_filtered_tx call (for logging)
        self._last_vx = 0.0
        self._last_vy = 0.0
        self._last_lead_deg = 0.0
        self._last_ball_speed = 0.0
        self._last_parallax_deg = 0.0
        self._active = False

        self.addRequirements(turret)
        init_auto_aim_keys()

    # ===================================================================
    # Command lifecycle
    # ===================================================================

    def initialize(self):
        self._last_tx = 0.0
        self._filtered_tx = 0.0
        self._locked_tag_id = None
        self._lost_count = 0
        self._cycle_count = 0
        self._active = True
        SmartDashboard.putBoolean("Shooter/AutoAim", True)
        _log.info("AutoAim ENABLED")

    def execute(self):
        # 1. Find the best target (priority + stickiness)
        target = self._select_target()

        # 2. Publish telemetry (rate-limited internally)
        self._publish_telemetry(target)

        # 3. No target and no lock -- stop and wait
        if not self._has_locked_target(target):
            self._stop_and_reset()
            return

        # 4. Fresh target available -- update our filtered tx measurement
        if target is not None:
            age_ms = 0.0
            if target.timestamp > 0:
                import time
                age_ms = (time.monotonic() - target.timestamp) * 1000
            _log.debug(
                f"[AIM-IN] t={target.tag_id} tx={target.tx:.2f} "
                f"age={age_ms:.0f}ms ftx={self._filtered_tx:.2f}")
            self._update_filtered_tx(target)

        # 5. Already on target AND we have a fresh measurement -- hold still.
        #    Without a fresh target, fall through to drive so the PD loop
        #    stays active instead of holding on a stale filtered_tx.
        if target is not None and self._is_on_target():
            self._hold_still()
            return

        # 6. Off target -- PD + feedforward to drive toward it
        self._drive_toward_target(target)

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool):
        self._active = False
        self.turret._stop()
        SmartDashboard.putBoolean("Shooter/AutoAim", False)
        SmartDashboard.putBoolean("AutoAim/OnTarget", False)
        _log.info(f"AutoAim DISABLED (interrupted={interrupted})")

    # ===================================================================
    # Target selection
    # ===================================================================

    def _select_target(self):
        """Pick target using priority list + stickiness.

        Stickiness: once locked onto a tag, keep tracking it through
        brief dropouts (up to TARGET_LOCK_LOST_CYCLES) before falling
        back to the priority scan.
        """
        tag_priority = self._tag_priority_supplier()

        # Try the currently locked tag first
        if self._locked_tag_id is not None:
            target = self.vision.get_target(self._locked_tag_id)
            if target is not None:
                self._lost_count = 0
                return target
            # --- COASTING DISABLED FOR DEBUGGING ---
            # Normally we coast on stale filtered_tx for up to
            # TARGET_LOCK_LOST_CYCLES when the tag briefly drops out.
            # Commented out to see raw behavior without caching.
            # self._lost_count += 1
            # if self._lost_count < TARGET_LOCK_LOST_CYCLES:
            #     return None  # brief dropout -- hold lock, coast on last tx
            _log.debug(f"Lost lock on tag {self._locked_tag_id}")
            self._locked_tag_id = None
            self._lost_count = 0

        # Scan priority list for the first visible tag
        for tag_id in tag_priority:
            target = self.vision.get_target(tag_id)
            if target is not None:
                self._locked_tag_id = tag_id
                # Seed filter so we don't spike from a stale value
                self._filtered_tx = target.tx
                _log.debug(f"Locked onto tag {tag_id} tx={target.tx:.2f}")
                return target
        return None

    # ===================================================================
    # State checks
    # ===================================================================

    def _has_locked_target(self, target):
        """True if we have a target or are coasting through a brief dropout."""
        return target is not None or self._locked_tag_id is not None

    def _is_on_target(self):
        """True if filtered tx is within alignment tolerance.

        When on-target, the turret should hold still. This prevents
        the deadband compensation from firing on tiny errors and
        causing stutter/oscillation at rest.
        """
        tolerance = CON_SHOOTER["turret_alignment_tolerance"]
        return abs(self._filtered_tx) <= tolerance

    def is_on_target(self):
        """Public: True if auto-aim is active and turret is aligned.

        Safe to call from other commands. Returns False when auto-aim
        is not running, so callers never see stale state.
        """
        return self._active and self._is_on_target()

    # ===================================================================
    # Measurement update
    # ===================================================================

    def _update_filtered_tx(self, target):
        """Update filtered tx from a fresh vision measurement.

        Applies parallax correction, velocity lead compensation, and
        EMA smoothing. Each correction is additive -- they adjust tx
        independently without replacing the base measurement.
        """
        self._last_tx = target.tx
        tag_offsets = self._tag_offsets_supplier()

        # Parallax correction -- shift aim from tag to Hub center.
        # Additive: adjusts tx based on geometry, does not replace PD.
        self._last_parallax_deg = 0.0
        if CON_SHOOTER["parallax_correction_enabled"]:
            offsets = tag_offsets.get(target.tag_id, {})
            self._last_parallax_deg = compute_parallax_correction(
                target.tx,
                target.distance,
                offsets.get("tag_y_offset_m", 0.0),
                offsets.get("tag_x_offset_m", 0.0),
            )
            self._last_tx += self._last_parallax_deg

        # Velocity lead -- aim ahead based on robot lateral speed
        self._last_vx, self._last_vy, self._last_lead_deg = 0.0, 0.0, 0.0
        self._last_ball_speed = 0.0
        if (CON_SHOOTER["velocity_lead_enabled"]
                and self._robot_velocity_supplier is not None):
            self._last_vx, self._last_vy = self._robot_velocity_supplier()
            self._last_lead_deg, self._last_ball_speed = (
                compute_velocity_lead(self._last_vy, target.distance))
            self._last_tx += self._last_lead_deg

        # EMA filter -- smooths noisy Limelight tx readings
        alpha = CON_SHOOTER["turret_tx_filter_alpha"]
        self._filtered_tx = (alpha * self._last_tx
                             + (1 - alpha) * self._filtered_tx)

    # ===================================================================
    # Motor output
    # ===================================================================

    def _stop_and_reset(self):
        """Stop turret and clear tx state. Used when fully lost."""
        self._last_tx = 0.0
        self._filtered_tx = 0.0
        self.turret._set_voltage(0.0)
        log_lost(self._cycle_count, self.turret.get_position())
        self._cycle_count += 1

    def _hold_still(self):
        """Hold turret at zero voltage. Used when on-target."""
        self.turret._set_voltage(0.0)
        log_hold(self._cycle_count, self._locked_tag_id,
                 self._filtered_tx, self.turret.get_position())
        self._cycle_count += 1

    def _drive_toward_target(self, target):
        """PD + feedforward control to drive turret toward target."""
        turret_vel = self.turret.get_velocity()

        # Get lateral velocity for feedforward (0 if no supplier)
        vy = 0.0
        if self._robot_velocity_supplier is not None:
            _, vy = self._robot_velocity_supplier()

        voltage, p_term, d_term, ff_term, raw_voltage = (
            compute_turret_voltage(
                self._filtered_tx, turret_vel, vy,
                self._aim_sign, CON_SHOOTER))

        self.turret._set_voltage(voltage)
        log_drive(self._cycle_count, self._locked_tag_id, target,
                  self._filtered_tx, p_term, d_term, ff_term,
                  raw_voltage, voltage, turret_vel,
                  self.turret.get_position(),
                  self._last_vx, self._last_vy, self._last_lead_deg,
                  self._last_ball_speed, self._last_parallax_deg,
                  self._lost_count)
        self._cycle_count += 1

    # ===================================================================
    # Telemetry
    # ===================================================================

    def _publish_telemetry(self, target):
        """Delegate all SmartDashboard publishing to telemetry module."""
        publish_auto_aim(
            self._cycle_count,
            has_target=target is not None,
            locked_tag_id=self._locked_tag_id,
            on_target=self._is_on_target(),
        )
        if target is not None:
            publish_velocity_debug(
                self._cycle_count,
                self._last_vx, self._last_vy, self._last_lead_deg,
            )
