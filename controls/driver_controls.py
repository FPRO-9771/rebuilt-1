"""
Driver controller bindings.
All driver button/stick mappings live here to keep robot_container short.

Controls:
    Left stick      -- Drive (X/Y translation)
    Right stick X   -- Rotation
    A button        -- Drive straight forward (alignment test, 7% speed)
    B button        -- Point wheels in stick direction (hold)
    Left bumper     -- Reset field-centric heading
    Right bumper    -- Toggle field-centric / robot-centric
    Y button        -- Toggle intake deploy (down/up)
    Left trigger    -- Run intake spinner (hold)
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
from constants.debug import DEBUG
from constants import CON_INTAKE_SPINNER
from subsystems.command_swerve_drivetrain import CommandSwerveDrivetrain
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
    slow = CON_ROBOT["slow_mode_factor"]
    max_speed = TunerConstants.speed_at_12_volts * slow
    max_angular_rate = rotationsToRadians(0.75) * slow

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
    point = swerve.requests.PointWheelsAt()

    # --- Drive mode toggle state ---
    state = {"robot_centric": False}

    # --- Swerve telemetry ---
    logger = SwerveTelemetry(max_speed)

    # --- Default command: field-centric or robot-centric drive ---
    # Note: X is forward, Y is left per WPILib convention
    drive_exp = CON_ROBOT["drive_exponent"]
    rot_exp = CON_ROBOT["rotation_exponent"]

    _drive_log_counter = {"n": 0}

    def get_drive_request():
        req = drive_rc if state["robot_centric"] else drive_fc
        if DEBUG["debug_telemetry"]:
            SmartDashboard.putBoolean(
                "Drive/Robot Centric", state["robot_centric"]
            )

        raw_ly = driver.getLeftY()
        raw_lx = driver.getLeftX()
        raw_rx = driver.getRightX()

        vel_x = -_apply_curve(raw_ly, drive_exp) * max_speed
        vel_y = -_apply_curve(raw_lx, drive_exp) * max_speed
        rot = -_apply_curve(raw_rx, rot_exp) * max_angular_rate

        # Log inputs + module states when driving (every 10th cycle ~2 Hz)
        # is_driving = abs(vel_x) > 0.01 or abs(vel_y) > 0.01 or abs(rot) > 0.01
        # if DEBUG["verbose"] and is_driving:
        #     _drive_log_counter["n"] += 1
        #     if _drive_log_counter["n"] % 10 == 0:
        #         _log.debug(
        #             f"INPUTS  joy_ly={raw_ly:+.3f} joy_lx={raw_lx:+.3f}"
        #             f" joy_rx={raw_rx:+.3f}"
        #             f" | cmd vx={vel_x:+.2f} vy={vel_y:+.2f} rot={rot:+.3f}"
        #         )
        #         dt_state = drivetrain.get_state()
        #         heading = dt_state.pose.rotation().degrees()
        #         for i, (ms, mt) in enumerate(
        #             zip(dt_state.module_states, dt_state.module_targets)
        #         ):
        #             _log.debug(
        #                 f"  MOD[{i}] angle={ms.angle.degrees():+7.1f}deg"
        #                 f" speed={ms.speed:+.2f}m/s"
        #                 f" | target angle={mt.angle.degrees():+7.1f}deg"
        #                 f" speed={mt.speed:+.2f}m/s"
        #             )
        #         _log.debug(f"  GYRO heading={heading:+.1f}deg")
        # elif not is_driving:
        #     _drive_log_counter["n"] = 0

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

    # --- A button: drive straight forward (alignment test, 25% speed) ---
    drive_straight = (
        swerve.requests.RobotCentric()
        .with_drive_request_type(
            swerve.SwerveModule.DriveRequestType.VELOCITY
        )
    )
    driver.a().whileTrue(
        drivetrain.apply_request(
            lambda: drive_straight
            .with_velocity_x(max_speed * 0.25)
            .with_velocity_y(0)
            .with_rotational_rate(0)
        )
    )

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

    # --- Left trigger: run intake spinner (hold) ---
    if intake_spinner is not None:
        driver.leftTrigger().whileTrue(
            intake_spinner.run_at_voltage(CON_INTAKE_SPINNER["spin_voltage"])
        )

    # --- Register swerve telemetry ---
    drivetrain.register_telemetry(
        lambda state: logger.telemeterize(state)
    )
