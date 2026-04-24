"""
Coordinate-based turret aiming.
Rotates turret toward the alliance Hub using drivetrain odometry.
No vision required -- uses field position to calculate the angle.

Pipeline each cycle:
  1. Read ShootContext (pose, shooter position, target, velocity)
  2. Compute target state (error, distance, closing speed)
  3. Compute angle compensation (lead correction for robot movement)
  4. Route through turret limits
  5. EMA filter
  6. PD control -> voltage
"""

import math
from typing import Callable

from commands2 import Command
from wpilib import SmartDashboard

from subsystems.turret_minion import TurretMinion
from calculations.target_state import compute_target_state
from calculations.movement_compensation import compute_angle_compensation
from calculations.turret_routing import choose_rotation_direction
from calculations.turret_pd import compute_turret_voltage
from constants.shoot_auto_aim import CON_AUTO_AIM
from constants.pose import CON_POSE
from telemetry.auto_aim_telemetry import (
    init_auto_aim_keys, publish_auto_aim, publish_velocity_debug,
    init_aim_dashboard_keys, publish_aim_dashboard,
)
from telemetry.auto_aim_logging import log_hold, log_drive
from telemetry.compensation_logging import log_compensation
from constants.debug import DEBUG
from utils.logger import get_logger

_log = get_logger("coordinate_aim")


class CoordinateAim(Command):
    """Aim turret at the Hub using odometry-based angle calculation."""

    def __init__(
        self,
        turret: TurretMinion,
        context_supplier: Callable,
        turret_config: dict,
    ):
        super().__init__()
        self.turret = turret
        self._context_supplier = context_supplier
        self._turret_config = turret_config
        self._aim_sign = -1.0 if CON_AUTO_AIM["turret_aim_inverted"] else 1.0

        self._filtered_error = 0.0
        self._i_accumulator = 0.0
        self._cycle_count = 0
        self._active = False
        self._target_mode = "hub"

        self.addRequirements(turret)
        init_auto_aim_keys()
        init_aim_dashboard_keys()

    # --- Public API ---

    def is_on_target(self) -> bool:
        """True if auto-aim is active and turret is aligned.

        Safe to call from other commands (e.g. ShootWhenReady).
        Returns False when not running so callers never see stale state.
        """
        return self._active and self._is_on_target()

    def get_target_state(self):
        """Return the most recent TargetState, or None if not active.

        Allows other commands (e.g. ShootWhenReady) to read distance and
        closing speed without duplicating the pose calculation.
        """
        if not self._active:
            return None
        return self._last_state

    def reset_state(self) -> None:
        """Zero the EMA filter and integral accumulator.

        Called by ResyncTurret so the turret does not lurch on residual
        integral windup after the operator recalibrates mid-match.
        """
        self._filtered_error = 0.0
        self._i_accumulator = 0.0

    # --- Command lifecycle ---

    def initialize(self):
        self._filtered_error = 0.0
        self._i_accumulator = 0.0
        self._cycle_count = 0
        self._active = True
        self._last_state = None
        self._target_mode = "hub"
        SmartDashboard.putBoolean("Shooter/AutoAim", True)
        _log.info("CoordinateAim ENABLED")
        if DEBUG["auto_sequence_logging"]:
            _log.info("AUTO SEQ: CoordinateAim initialize -- turret aiming started")

    def execute(self):
        # 1. Read shared context (pose, shooter, target, velocity)
        ctx = self._context_supplier()
        self._target_mode = ctx.target_mode

        # 2. Compute target state (error, distance, closing speed).
        # Effective center includes any runtime calibration offset set by
        # ResyncTurret (operator B), so drift can be corrected in-match.
        state = compute_target_state(
            ctx.heading_deg,
            (ctx.shooter_x, ctx.shooter_y),
            (ctx.target_x, ctx.target_y),
            (ctx.vx, ctx.vy),
            self.turret.get_position(),
            self.turret.get_effective_center_position(),
            CON_POSE["degrees_per_rotation"],
        )
        self._last_state = state

        # 3. Compute angle compensation (lead correction for movement)
        # velocity is field-relative (converted in operator_controls.py),
        # so use field-frame bearing here to match.
        bearing_field_rad = math.radians(state.bearing_deg + ctx.heading_deg)
        lead_deg = compute_angle_compensation(
            ctx.vx, ctx.vy, state.distance_m, bearing_field_rad,
        )

        # 4. Combine raw aim
        raw_aim = state.error_deg + lead_deg

        # 5. Route through turret limits
        routed_aim = choose_rotation_direction(
            self.turret.get_position(), raw_aim,
            self._turret_config["min_position"],
            self._turret_config["max_position"],
            CON_POSE["degrees_per_rotation"],
        )

        # 6. EMA filter
        alpha = CON_AUTO_AIM["turret_tx_filter_alpha"]
        self._filtered_error = (
            alpha * routed_aim + (1 - alpha) * self._filtered_error
        )

        # 7. Publish telemetry
        publish_auto_aim(
            self._cycle_count,
            on_target=self._is_on_target(),
            error_deg=state.error_deg,
            distance_m=state.distance_m,
        )
        publish_velocity_debug(self._cycle_count, ctx.vx, ctx.vy, lead_deg)
        publish_aim_dashboard(
            self._cycle_count, state.distance_m, state.bearing_deg,
        )

        # 7b. Compensation debug logging
        log_compensation(
            self._cycle_count,
            ctx.vx, ctx.vy, state.distance_m, bearing_field_rad,
            state.closing_speed_mps, ctx.corrected_distance, lead_deg,
        )

        # 8. Control turret
        turret_pos = self.turret.get_position()
        if self._in_hold_state():
            self.turret._set_voltage(0.0)
            log_hold(
                self._cycle_count,
                ctx.pose_x, ctx.pose_y, ctx.heading_deg,
                ctx.shooter_x, ctx.shooter_y,
                ctx.target_x, ctx.target_y,
                turret_pos, state.error_deg, state.distance_m,
                state.closing_speed_mps,
                target_mode=ctx.target_mode,
            )
        else:
            turret_vel = self.turret.get_velocity()
            voltage, p_term, i_term, d_term, raw_voltage, self._i_accumulator = (
                compute_turret_voltage(
                    self._filtered_error, turret_vel,
                    self._aim_sign, self._active_aim_config(),
                    self._i_accumulator,
                )
            )
            self.turret._set_voltage(voltage)
            log_drive(
                self._cycle_count,
                ctx.pose_x, ctx.pose_y, ctx.heading_deg,
                ctx.shooter_x, ctx.shooter_y,
                ctx.target_x, ctx.target_y,
                turret_pos, state.error_deg, state.distance_m,
                state.closing_speed_mps,
                lead_deg, routed_aim,
                self._filtered_error,
                p_term, i_term, d_term, raw_voltage, voltage,
                turret_vel, ctx.vx, ctx.vy,
                target_mode=ctx.target_mode,
            )

        self._cycle_count += 1

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool):
        self._active = False
        self.turret._stop()
        SmartDashboard.putBoolean("Shooter/AutoAim", False)
        SmartDashboard.putBoolean("AutoAim/OnTarget", False)
        _log.info(f"CoordinateAim ended (interrupted={interrupted})")
        if DEBUG["auto_sequence_logging"]:
            _log.info(f"AUTO SEQ: CoordinateAim end -- ran {self._cycle_count} cycles")

    # --- Internal ---

    def _get_tolerance(self) -> float:
        """Return alignment tolerance, widened in Assist mode."""
        tolerance = CON_AUTO_AIM["turret_alignment_tolerance"]
        if self._target_mode == "assist":
            tolerance *= CON_AUTO_AIM["assist_tolerance_multiplier"]
        return tolerance

    def _active_aim_config(self) -> dict:
        """Return the PD config for this cycle.

        In Assist mode, override the voltage caps with the softer assist
        limits so aggressive chassis moves in the neutral zone don't slam
        the turret gears. All other gains stay the same.
        """
        if self._target_mode != "assist":
            return CON_AUTO_AIM
        return {
            **CON_AUTO_AIM,
            "turret_max_auto_voltage": CON_AUTO_AIM["assist_max_auto_voltage"],
            "turret_max_brake_voltage": CON_AUTO_AIM["assist_max_brake_voltage"],
        }

    def _in_hold_state(self) -> bool:
        """True if error is within tolerance -- sets motor to 0V so turret coasts.

        No velocity check here: if we kept applying PD voltage whenever
        tvel > max_vel, the D term would sustain oscillation indefinitely
        for small initial errors. Cutting voltage lets the turret coast
        to a stop naturally. Firing clearance uses is_on_target() instead.
        """
        return abs(self._filtered_error) <= self._get_tolerance()

    def _is_on_target(self) -> bool:
        """True if turret is in hold AND velocity is settled (safe to fire).

        Stricter than _in_hold_state(): requires low velocity so shots are
        not fired while the turret is still coasting through the target.
        """
        max_vel = CON_AUTO_AIM.get("turret_on_target_max_vel", 2.0)
        return self._in_hold_state() and abs(self.turret.get_velocity()) <= max_vel
