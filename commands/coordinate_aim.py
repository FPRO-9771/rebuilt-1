"""
Coordinate-based turret aiming.
Rotates turret toward the alliance Hub using drivetrain odometry.
No vision required -- uses field position to calculate the angle.

Pipeline each cycle:
  1. Read ShootContext (pose, shooter position, target, velocity)
  2. Compute target state (error, distance, closing speed)
  3. Compute movement corrections (tracking + lead)
  4. Route through turret limits
  5. EMA filter
  6. PD control -> voltage
"""

import math
from typing import Callable

from commands2 import Command
from wpilib import SmartDashboard

from subsystems.turret import Turret
from calculations.target_state import compute_target_state
from calculations.movement_compensation import compute_movement_correction
from calculations.turret_routing import choose_rotation_direction
from calculations.turret_pd import compute_turret_voltage
from constants.shooter import CON_SHOOTER
from constants.pose import CON_POSE
from telemetry.auto_aim_telemetry import (
    init_auto_aim_keys, publish_auto_aim, publish_velocity_debug,
    init_aim_dashboard_keys, publish_aim_dashboard,
)
from telemetry.auto_aim_logging import log_hold, log_drive
from utils.logger import get_logger

_log = get_logger("coordinate_aim")


class CoordinateAim(Command):
    """Aim turret at the Hub using odometry-based angle calculation."""

    def __init__(
        self,
        turret: Turret,
        context_supplier: Callable,
        turret_config: dict,
    ):
        super().__init__()
        self.turret = turret
        self._context_supplier = context_supplier
        self._turret_config = turret_config
        self._aim_sign = -1.0 if CON_SHOOTER["turret_aim_inverted"] else 1.0

        self._filtered_error = 0.0
        self._cycle_count = 0
        self._active = False

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

    # --- Command lifecycle ---

    def initialize(self):
        self._filtered_error = 0.0
        self._cycle_count = 0
        self._active = True
        self._last_state = None
        SmartDashboard.putBoolean("Shooter/AutoAim", True)
        _log.info("CoordinateAim ENABLED")

    def execute(self):
        # 1. Read shared context (pose, shooter, target, velocity)
        ctx = self._context_supplier()

        # 2. Compute target state (error, distance, closing speed)
        state = compute_target_state(
            ctx.heading_deg,
            (ctx.shooter_x, ctx.shooter_y),
            (ctx.target_x, ctx.target_y),
            (ctx.vx, ctx.vy),
            self.turret.get_position(),
            CON_POSE["center_position"],
            CON_POSE["degrees_per_rotation"],
        )
        self._last_state = state

        # 3. Compute movement corrections
        # bearing_deg is the angle from robot front to hub; convert to
        # field-frame radians by adding heading, for velocity decomposition.
        bearing_field_rad = math.radians(state.bearing_deg + ctx.heading_deg)
        tracking_deg, lead_deg = compute_movement_correction(
            ctx.vx, ctx.vy, state.distance_m, bearing_field_rad, CON_SHOOTER,
        )

        # 4. Combine raw aim
        raw_aim = state.error_deg + tracking_deg + lead_deg

        # 5. Route through turret limits
        routed_aim = choose_rotation_direction(
            self.turret.get_position(), raw_aim,
            self._turret_config["min_position"],
            self._turret_config["max_position"],
            CON_POSE["degrees_per_rotation"],
        )

        # 6. EMA filter
        alpha = CON_SHOOTER["turret_tx_filter_alpha"]
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

        # 8. Control turret
        turret_pos = self.turret.get_position()
        if self._is_on_target():
            self.turret._set_voltage(0.0)
            log_hold(
                self._cycle_count,
                ctx.pose_x, ctx.pose_y, ctx.heading_deg,
                ctx.shooter_x, ctx.shooter_y,
                ctx.target_x, ctx.target_y,
                turret_pos, state.error_deg, state.distance_m,
                state.closing_speed_mps,
            )
        else:
            turret_vel = self.turret.get_velocity()
            voltage, p_term, d_term, ff_term, raw_voltage = (
                compute_turret_voltage(
                    self._filtered_error, turret_vel, ctx.vy,
                    self._aim_sign, CON_SHOOTER,
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
                tracking_deg, lead_deg, routed_aim,
                self._filtered_error,
                p_term, d_term, ff_term, raw_voltage, voltage,
                turret_vel, ctx.vx, ctx.vy,
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

    # --- Internal ---

    def _is_on_target(self) -> bool:
        """True if filtered error is within alignment tolerance."""
        tolerance = CON_SHOOTER["turret_alignment_tolerance"]
        return abs(self._filtered_error) <= tolerance
