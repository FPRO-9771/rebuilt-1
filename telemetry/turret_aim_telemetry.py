"""
Turret error telemetry (always-on, toggleable).
Publishes turret-to-Hub error to SmartDashboard every cycle period,
regardless of whether CoordinateAim is active.

Toggle with DEBUG["turret_aim_telemetry"] in constants/debug.py.
"""

import math

from wpilib import SmartDashboard

from calculations.target_state import compute_target_state
from calculations.shooter_position import get_shooter_field_position
from constants.debug import DEBUG
from constants.pose import CON_POSE
from utils.logger import get_logger

_log = get_logger("turret_aim_telem")

_PERIOD = 10   # publish every 10 cycles (~2 Hz at 50 ms loop)
_OFFSET = 8    # stagger offset -- avoids collisions with other telemetry


class TurretAimTelemetry:
    """Publishes turret error and distance to SmartDashboard."""

    def __init__(self, drivetrain, turret, alliance_supplier):
        self._drivetrain = drivetrain
        self._turret = turret
        self._alliance_supplier = alliance_supplier
        self._startup_logged = False

        if DEBUG["turret_aim_telemetry"]:
            SmartDashboard.putNumber("AutoAim/ErrorDeg", 0.0)
            SmartDashboard.putNumber("AutoAim/DistanceM", 0.0)

    def _log_startup_math(self, pose, shooter_xy, target_xy, turret_pos):
        """One-shot log of every intermediate value in the error calc."""
        heading_deg = pose.rotation().degrees()
        center = CON_POSE["center_position"]
        dpr = CON_POSE["degrees_per_rotation"]

        dx = target_xy[0] - shooter_xy[0]
        dy = target_xy[1] - shooter_xy[1]
        target_field_deg = math.degrees(math.atan2(dy, dx))
        desired_turret_deg = target_field_deg - heading_deg
        current_turret_deg = (center - turret_pos) * dpr
        error_deg = desired_turret_deg - current_turret_deg

        # Wrap to [-180, 180]
        while error_deg > 180:
            error_deg -= 360
        while error_deg < -180:
            error_deg += 360

        _log.warning(
            "[AIM STARTUP] -- full error breakdown --\n"
            "  pose=(%+.3f, %+.3f) heading=%.2f deg\n"
            "  shooter_offset=(%.4f, %.4f)\n"
            "  shooter_xy=(%+.3f, %+.3f)\n"
            "  target_xy=(%+.3f, %+.3f)\n"
            "  dx=%+.4f  dy=%+.4f\n"
            "  target_field_deg=%.2f  (atan2 of dx/dy)\n"
            "  desired_turret_deg=%.2f  (target_field - heading)\n"
            "  turret_pos=%.4f  center_pos=%.4f  deg_per_rot=%.2f\n"
            "  current_turret_deg=%.2f  ((center-pos)*dpr)\n"
            "  error_deg=%.2f  (desired - current, wrapped)"
            % (
                pose.X(), pose.Y(), heading_deg,
                CON_POSE["shooter_offset_x"], CON_POSE["shooter_offset_y"],
                shooter_xy[0], shooter_xy[1],
                target_xy[0], target_xy[1],
                dx, dy,
                target_field_deg,
                desired_turret_deg,
                turret_pos, center, dpr,
                current_turret_deg,
                error_deg,
            )
        )

    def update(self, cycle):
        """Compute and publish turret error. Called every robot cycle."""
        if not DEBUG["turret_aim_telemetry"]:
            return
        if cycle % _PERIOD != _OFFSET:
            return

        pose = self._drivetrain.get_pose()
        shooter_xy = get_shooter_field_position(
            pose,
            CON_POSE["shooter_offset_x"],
            CON_POSE["shooter_offset_y"],
        )

        alliance = self._alliance_supplier()
        target_xy = (alliance["target_x"], alliance["target_y"])

        turret_pos = self._turret.get_position()

        # One-shot: dump all intermediate math on first update
        if not self._startup_logged:
            self._startup_logged = True
            self._log_startup_math(pose, shooter_xy, target_xy, turret_pos)

        state = compute_target_state(
            pose.rotation().degrees(),
            shooter_xy,
            target_xy,
            (0.0, 0.0),
            turret_pos,
            CON_POSE["center_position"],
            CON_POSE["degrees_per_rotation"],
        )

        SmartDashboard.putNumber("AutoAim/ErrorDeg", round(state.error_deg, 2))
        SmartDashboard.putNumber("AutoAim/DistanceM", round(state.distance_m, 2))
