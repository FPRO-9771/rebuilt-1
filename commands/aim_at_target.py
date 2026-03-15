"""
Aim-at-target command.
Rotates the robot toward the alliance Hub using a PID controller
and odometry-based target tracking (no vision required).
"""

from commands2 import Command
from wpimath.controller import PIDController

from subsystems.target_tracking import TargetTracking
from constants.target_tracking import CON_TARGET_TRACKING
from utils.logger import get_logger

_log = get_logger("aim_at_target")


class AimAtTarget(Command):
    """PID rotation to face the alliance Hub target."""

    def __init__(self, target_tracking: TargetTracking, drivetrain):
        super().__init__()
        self._target_tracking = target_tracking
        self._drivetrain = drivetrain

        # PID controller for heading correction (input = degrees of error)
        self._pid = PIDController(
            CON_TARGET_TRACKING["aim_kP"],
            CON_TARGET_TRACKING["aim_kI"],
            CON_TARGET_TRACKING["aim_kD"],
        )
        self._pid.setTolerance(CON_TARGET_TRACKING["heading_tolerance_deg"])
        self._pid.enableContinuousInput(-180, 180)

        self.addRequirements(drivetrain)

    def initialize(self):
        self._pid.reset()
        self._pid.setSetpoint(0.0)
        _log.info("AimAtTarget started")

    def execute(self):
        # Heading error: positive = need to turn left
        error = self._target_tracking.get_angle_to_target()

        # PID output is a rotation rate (clamped)
        output = self._pid.calculate(error, 0.0)
        max_out = CON_TARGET_TRACKING["max_rotation_output"]
        clamped = max(-max_out, min(output, max_out))

        # Apply rotation-only swerve request
        from phoenix6 import swerve
        self._drivetrain.set_control(
            swerve.requests.FieldCentric()
            .with_velocity_x(0)
            .with_velocity_y(0)
            .with_rotational_rate(clamped)
        )

    def isFinished(self) -> bool:
        return self._pid.atSetpoint()

    def end(self, interrupted: bool):
        # Stop rotating
        from phoenix6 import swerve
        self._drivetrain.set_control(
            swerve.requests.FieldCentric()
            .with_velocity_x(0)
            .with_velocity_y(0)
            .with_rotational_rate(0)
        )
        _log.info(
            f"AimAtTarget ended (interrupted={interrupted}, "
            f"dist={self._target_tracking.get_distance_to_target():.2f}m)"
        )
