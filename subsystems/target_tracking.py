"""
Target tracking subsystem.
Calculates angle and distance from the robot to the alliance Hub
using odometry (no vision/AprilTags required).
"""

import math

from commands2 import Subsystem
from wpimath.geometry import Translation2d

from constants.target_tracking import CON_TARGET_TRACKING
from utils.logger import get_logger

_log = get_logger("target_tracking")


class TargetTracking(Subsystem):
    """
    Computes angle and distance from the robot's current pose to
    the selected alliance Hub target using drivetrain odometry.
    """

    def __init__(self, drivetrain):
        super().__init__()
        self._drivetrain = drivetrain

        # Default to blue alliance target
        self._target = Translation2d(
            CON_TARGET_TRACKING["blue_target_x"],
            CON_TARGET_TRACKING["blue_target_y"],
        )
        _log.info("TargetTracking initialized (default: blue)")

    # --- Alliance selection ---

    def set_alliance(self, alliance: str) -> None:
        """Switch target between 'red' and 'blue' alliance Hubs."""
        if alliance.lower() == "red":
            self._target = Translation2d(
                CON_TARGET_TRACKING["red_target_x"],
                CON_TARGET_TRACKING["red_target_y"],
            )
            _log.info("Target set to RED Hub")
        else:
            self._target = Translation2d(
                CON_TARGET_TRACKING["blue_target_x"],
                CON_TARGET_TRACKING["blue_target_y"],
            )
            _log.info("Target set to BLUE Hub")

    # --- Calculations ---

    def get_angle_to_target(self) -> float:
        """Return angle in degrees from the robot's heading to the target.

        Positive = target is to the left, negative = target is to the right.
        """
        pose = self._drivetrain.get_pose()
        dx = self._target.X() - pose.X()
        dy = self._target.Y() - pose.Y()

        # Angle from robot to target in field coordinates
        target_angle_deg = math.degrees(math.atan2(dy, dx))

        # Robot's current heading in degrees
        heading_deg = pose.rotation().degrees()

        # Error: how far the robot needs to rotate
        error = target_angle_deg - heading_deg

        # Wrap to [-180, 180]
        while error > 180:
            error -= 360
        while error < -180:
            error += 360

        return error

    def get_distance_to_target(self) -> float:
        """Return distance in meters from the robot to the target."""
        pose = self._drivetrain.get_pose()
        dx = self._target.X() - pose.X()
        dy = self._target.Y() - pose.Y()
        return math.hypot(dx, dy)
