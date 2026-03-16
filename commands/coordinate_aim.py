"""
Coordinate-based turret aiming.
Rotates turret toward the alliance Hub using drivetrain odometry.
No vision required -- uses field position to calculate the angle.
"""

import math

from commands2 import Command

from subsystems.turret import Turret
from constants import CON_TURRET
from constants.target_tracking import CON_TARGET_TRACKING as CON_TT
from utils.logger import get_logger

_log = get_logger("coordinate_aim")


class CoordinateAim(Command):
    """Aim turret at the Hub using odometry-based angle calculation."""

    def __init__(self, turret, drivetrain, alliance_supplier):
        super().__init__()
        self.turret = turret
        self._drivetrain = drivetrain
        self._alliance_supplier = alliance_supplier
        self.addRequirements(turret)

    # --- Target calculation ---

    def _get_target_xy(self):
        """Return (x, y) of the alliance Hub."""
        alliance = self._alliance_supplier()
        if alliance["name"] == "Red":
            return (CON_TT["red_target_x"], CON_TT["red_target_y"])
        return (CON_TT["blue_target_x"], CON_TT["blue_target_y"])

    def _get_desired_turret_angle(self):
        """Angle from robot forward to the target, in degrees."""
        pose = self._drivetrain.get_pose()
        target_x, target_y = self._get_target_xy()

        dx = target_x - pose.X()
        dy = target_y - pose.Y()

        target_angle_deg = math.degrees(math.atan2(dy, dx))
        heading_deg = pose.rotation().degrees()

        error = target_angle_deg - heading_deg
        while error > 180:
            error -= 360
        while error < -180:
            error += 360
        return error

    def _get_current_turret_angle(self):
        """Current turret angle relative to robot forward, in degrees."""
        pos = self.turret.get_position()
        center = CON_TURRET["center_position"]
        deg_per_rot = CON_TURRET["degrees_per_rotation"]
        return (pos - center) * deg_per_rot

    # --- Command lifecycle ---

    def initialize(self):
        self._cycle = 0
        _log.info("CoordinateAim ENABLED")

    def execute(self):
        pose = self._drivetrain.get_pose()
        target_x, target_y = self._get_target_xy()
        desired = self._get_desired_turret_angle()
        current = self._get_current_turret_angle()
        error = desired - current

        # Wrap error to [-180, 180] so turret takes the shortest path
        while error > 180:
            error -= 360
        while error < -180:
            error += 360

        # P control with dedicated coordinate-aim constants
        max_v = CON_TT["turret_max_voltage"]
        kP = CON_TT["turret_kP"]
        voltage = -error * kP
        voltage = max(-max_v, min(voltage, max_v))

        self.turret._set_voltage(voltage)

        # Debug log every 10 cycles (~200ms at 50Hz)
        self._cycle += 1
        if self._cycle % 10 == 0:
            dist = math.hypot(target_x - pose.X(), target_y - pose.Y())
            _log.debug(
                f"CoordAim: pose=({pose.X():.2f},{pose.Y():.2f}) "
                f"hdg={pose.rotation().degrees():.1f} "
                f"tgt=({target_x:.1f},{target_y:.1f}) dist={dist:.2f}m "
                f"desired={desired:.1f} current={current:.1f} "
                f"err={error:.1f} volt={voltage:.3f}"
            )

    def isFinished(self):
        return False

    def end(self, interrupted):
        self.turret._stop()
        _log.info(f"CoordinateAim ended (interrupted={interrupted})")
