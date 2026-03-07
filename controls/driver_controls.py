"""
Driver controller bindings.
All driver button/stick mappings live here to keep robot_container short.

Controls:
    Left stick      -- Drive (X/Y translation)
    Right stick X   -- Rotation
    A button        -- Brake (hold)
    B button        -- Point wheels in stick direction (hold)
    Left bumper     -- Reset field-centric heading
    Right bumper    -- Toggle field-centric / robot-centric
    Back + Y/X      -- SysId dynamic forward/reverse
    Start + Y/X     -- SysId quasistatic forward/reverse

Idle request is applied automatically when the robot is disabled.
"""

import math

from commands2 import InstantCommand
from commands2.button import Trigger
from commands2.sysid import SysIdRoutine

from generated.tuner_constants import TunerConstants
from phoenix6 import swerve
from wpilib import DriverStation, SmartDashboard
from wpimath.geometry import Rotation2d
from wpimath.units import rotationsToRadians

from constants.controls import CON_ROBOT
from subsystems.command_swerve_drivetrain import CommandSwerveDrivetrain
from telemetry.swerve_telemetry import SwerveTelemetry


def _apply_curve(value, exponent):
    """Apply power curve to joystick input. Preserves sign, full range unchanged."""
    return math.copysign(abs(value) ** exponent, value)


def configure_driver(driver, drivetrain: CommandSwerveDrivetrain):
    """
    Wire all driver controller bindings.
    Call once from RobotContainer.__init__.
    """
    max_speed = TunerConstants.speed_at_12_volts
    max_angular_rate = rotationsToRadians(0.75)  # 3/4 rotation per second

    # --- Swerve requests ---
    drive_fc = (
        swerve.requests.FieldCentric()
        .with_deadband(max_speed * 0.1)
        .with_rotational_deadband(max_angular_rate * 0.1)
        .with_drive_request_type(
            swerve.SwerveModule.DriveRequestType.OPEN_LOOP_VOLTAGE
        )
    )
    drive_rc = (
        swerve.requests.RobotCentric()
        .with_deadband(max_speed * 0.1)
        .with_rotational_deadband(max_angular_rate * 0.1)
        .with_drive_request_type(
            swerve.SwerveModule.DriveRequestType.OPEN_LOOP_VOLTAGE
        )
    )
    brake = swerve.requests.SwerveDriveBrake()
    point = swerve.requests.PointWheelsAt()

    # --- Drive mode toggle state ---
    state = {"robot_centric": False}

    # --- Swerve telemetry ---
    logger = SwerveTelemetry(max_speed)

    # --- Default command: field-centric or robot-centric drive ---
    # Note: X is forward, Y is left per WPILib convention
    drive_exp = CON_ROBOT["drive_exponent"]
    rot_exp = CON_ROBOT["rotation_exponent"]

    def get_drive_request():
        req = drive_rc if state["robot_centric"] else drive_fc
        SmartDashboard.putBoolean(
            "Drive/Robot Centric", state["robot_centric"]
        )
        return (
            req.with_velocity_x(
                -_apply_curve(driver.getLeftY(), drive_exp) * max_speed
            )
            .with_velocity_y(
                -_apply_curve(driver.getLeftX(), drive_exp) * max_speed
            )
            .with_rotational_rate(
                -_apply_curve(driver.getRightX(), rot_exp) * max_angular_rate
            )
        )

    drivetrain.setDefaultCommand(
        drivetrain.apply_request(get_drive_request)
    )

    # --- Idle while disabled ---
    idle = swerve.requests.Idle()
    Trigger(DriverStation.isDisabled).whileTrue(
        drivetrain.apply_request(lambda: idle).ignoringDisable(True)
    )

    # --- A button: brake ---
    driver.a().whileTrue(drivetrain.apply_request(lambda: brake))

    # --- B button: point wheels in stick direction ---
    driver.b().whileTrue(
        drivetrain.apply_request(
            lambda: point.with_module_direction(
                Rotation2d(-driver.getLeftY(), -driver.getLeftX())
            )
        )
    )

    # --- Left bumper: reset field-centric heading ---
    driver.leftBumper().onTrue(
        drivetrain.runOnce(drivetrain.seed_field_centric)
    )

    # --- Right bumper: toggle field-centric / robot-centric ---
    def _toggle_drive_mode():
        state["robot_centric"] = not state["robot_centric"]

    driver.rightBumper().onTrue(InstantCommand(_toggle_drive_mode))

    # --- SysId routines: back/start + Y/X ---
    # Run each routine exactly once per log session
    (driver.back() & driver.y()).whileTrue(
        drivetrain.sys_id_dynamic(SysIdRoutine.Direction.kForward)
    )
    (driver.back() & driver.x()).whileTrue(
        drivetrain.sys_id_dynamic(SysIdRoutine.Direction.kReverse)
    )
    (driver.start() & driver.y()).whileTrue(
        drivetrain.sys_id_quasistatic(SysIdRoutine.Direction.kForward)
    )
    (driver.start() & driver.x()).whileTrue(
        drivetrain.sys_id_quasistatic(SysIdRoutine.Direction.kReverse)
    )

    # --- Y button: drive straight forward (alignment test) ---
    drive_straight = (
        swerve.requests.RobotCentric()
        .with_drive_request_type(
            swerve.SwerveModule.DriveRequestType.OPEN_LOOP_VOLTAGE
        )
    )
    driver.y().whileTrue(
        drivetrain.apply_request(
            lambda: drive_straight
            .with_velocity_x(max_speed * 0.25)
            .with_velocity_y(0)
            .with_rotational_rate(0)
        )
    )

    # --- Register swerve telemetry ---
    drivetrain.register_telemetry(
        lambda state: logger.telemeterize(state)
    )
