"""
Driver controller bindings.
All driver button/stick mappings live here to keep robot_container short.

Controls:
    Left stick      -- Drive (X/Y translation)
    Right stick X   -- Rotation
    A button        -- Manual Hub odometry reset (when all else fails)
    B button        -- One-shot Limelight MegaTag2 odometry reset
    Left bumper     -- Reset field-centric heading
    Right bumper    -- Toggle field-centric / robot-centric
    Y button        -- Toggle intake deploy (down/up)
    Left trigger    -- Run intake: spin wheels + hold arm (hold)
    Right trigger   -- Slow mode (hold to reduce speed)
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
from wpimath.units import rotationsToRadians

from constants.controls import CON_ROBOT
from constants.debug import DEBUG
from commands.run_intake import RunIntake
from subsystems.command_swerve_drivetrain import CommandSwerveDrivetrain
from telemetry.drive_input_logging import log_drive_inputs
from telemetry.swerve_telemetry import SwerveTelemetry
from utils.logger import get_logger

_log = get_logger("driver_controls")


def _apply_curve(value, exponent):
    """Apply power curve to joystick input. Preserves sign, full range unchanged."""
    return math.copysign(abs(value) ** exponent, value)


def configure_driver(driver, drivetrain: CommandSwerveDrivetrain,
                     intake=None, intake_spinner=None):
    """
    Wire all driver controller bindings.
    Call once from RobotContainer.__init__.
    """
    max_speed = TunerConstants.speed_at_12_volts
    max_angular_rate = rotationsToRadians(0.75)
    slow_factor = CON_ROBOT["slow_mode_factor"]

    # --- Swerve requests ---
    drive_fc = (
        swerve.requests.FieldCentric()
        .with_deadband(max_speed * 0.1)
        .with_rotational_deadband(max_angular_rate * 0.1)
        .with_drive_request_type(
            swerve.SwerveModule.DriveRequestType.VELOCITY
        )
    )
    drive_rc = (
        swerve.requests.RobotCentric()
        .with_deadband(max_speed * 0.1)
        .with_rotational_deadband(max_angular_rate * 0.1)
        .with_drive_request_type(
            swerve.SwerveModule.DriveRequestType.VELOCITY
        )
    )
    brake = swerve.requests.SwerveDriveBrake()

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
        if DEBUG["debug_telemetry"]:
            SmartDashboard.putBoolean(
                "Drive/Robot Centric", state["robot_centric"]
            )

        raw_ly = driver.getLeftY()
        raw_lx = driver.getLeftX()
        raw_rx = driver.getRightX()

        # Right trigger: blend from full speed down to slow_factor
        trigger = driver.getRightTriggerAxis()
        speed_scale = 1.0 - trigger * (1.0 - slow_factor)

        curved_ly = _apply_curve(raw_ly, drive_exp)
        curved_lx = _apply_curve(raw_lx, drive_exp)
        curved_rx = _apply_curve(raw_rx, rot_exp)

        vel_x = -curved_ly * max_speed * speed_scale
        vel_y = -curved_lx * max_speed * speed_scale
        rot = -curved_rx * max_angular_rate * speed_scale

        # --- Drive input logging ---
        log_drive_inputs(
            raw_ly, raw_lx, raw_rx,
            curved_ly, curved_lx, curved_rx,
            vel_x, vel_y, rot,
            speed_scale, drive_exp, rot_exp,
        )

        return (
            req.with_velocity_x(vel_x)
            .with_velocity_y(vel_y)
            .with_rotational_rate(rot)
        )

    drivetrain.setDefaultCommand(
        drivetrain.apply_request(get_drive_request)
    )

    # --- Idle while disabled ---
    idle = swerve.requests.Idle()
    Trigger(DriverStation.isDisabled).whileTrue(
        drivetrain.apply_request(lambda: idle).ignoringDisable(True)
    )

    # --- A button: manual Hub odometry reset (when all else fails) ---
    driver.a().onTrue(
        InstantCommand(drivetrain.request_hub_reset)
    )

    # --- B button: one-shot Limelight MegaTag2 odometry reset ---
    driver.b().onTrue(
        InstantCommand(drivetrain.request_limelight_reset)
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

    # --- Y button: toggle intake deploy (down/up) ---
    if intake is not None:
        state["intake_down"] = False

        def _toggle_intake():
            state["intake_down"] = not state["intake_down"]
            if state["intake_down"]:
                intake.go_down().schedule()
            else:
                intake.go_up().schedule()

        driver.y().onTrue(InstantCommand(_toggle_intake))

    # --- Left trigger: spin intake + hold arm in place ---
    if intake is not None and intake_spinner is not None:
        driver.leftTrigger().whileTrue(RunIntake(intake, intake_spinner))

    # --- Register swerve telemetry ---
    drivetrain.register_telemetry(
        lambda state: logger.telemeterize(state)
    )
