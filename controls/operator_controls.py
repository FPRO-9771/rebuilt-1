"""
Operator controller bindings.
All operator button/stick mappings live here to keep robot_container short.

Controls:
    Left stick X         -- Manual turret aim
    Right stick Y        -- Launcher speed (when held via right trigger)
    B button             -- Resync turret to Hub (recalibrate after drift)
    Left bumper (toggle) -- Coordinate aim (turret aims at Hub via odometry)
    Left trigger (hold)  -- Shoot when ready (launcher + feed when on target)
                            Also runs hopper agitate IFF the robot is stationary
                            AND the driver is NOT holding their intake trigger.
    Right bumper (hold)  -- Reverse all feeds (un-jam, interrupts right trigger)
    Right trigger (hold) -- Manual shoot (launcher + auto-feed when at speed)
    Start (hold) + Right stick Y -- Pit-mode intake jog (low voltage)
"""

import math

from commands2.button import Trigger
from wpilib import DriverStation

from constants import CON_ROBOT
from constants.shoot_hardware import CON_TURRET_MINION
from constants.pose import CON_POSE
from constants.intake_hopper_agitate import CON_INTAKE_HOPPER_AGITATE
from calculations.shooter_position import get_shooter_field_position
from calculations.target_state import compute_range_state, ShootContext
from calculations.distance_compensation import compute_corrected_distance
from calculations.assist_target import AssistAimSelector
from utils.logger import get_logger

_log = get_logger("operator")
from subsystems.h_feed import HFeed
from subsystems.v_feed import VFeed
from commands.coordinate_aim import CoordinateAim
from commands.manual_launcher import ManualLauncher
from commands.manual_shoot import ManualShoot
from commands.resync_turret import ResyncTurret
from commands.reverse_feeds import ReverseFeeds
from commands.shoot_when_ready import ShootWhenReady
from commands.intake_pit_move import IntakePitMove
from commands.intake_hopper_agitate import IntakeHopperAgitate


def _make_shoot_context_supplier(drivetrain, alliance_supplier,
                                 velocity_supplier=None,
                                 teleop_supplier=DriverStation.isTeleop):
    """Build a callable that returns a ShootContext with full pose context.

    teleop_supplier: zero-arg callable returning True when the match is in
    teleop. Defaults to DriverStation.isTeleop; tests inject a stub.
    """
    assist_selector = AssistAimSelector()

    def _get_context():
        pose = drivetrain.get_pose()
        shooter_xy = get_shooter_field_position(
            pose,
            CON_POSE["shooter_offset_x"],
            CON_POSE["shooter_offset_y"],
        )
        alliance = alliance_supplier()
        hub_xy = (alliance["target_x"], alliance["target_y"])
        target_xy = assist_selector.select_target(
            shooter_xy,
            hub_xy,
            alliance.get("corners", ()),
            teleop_supplier(),
        )
        target_mode = "assist" if assist_selector.in_assist_mode else "hub"
        vx, vy = 0.0, 0.0
        if velocity_supplier is not None:
            vx, vy = velocity_supplier()
        raw_distance, closing = compute_range_state(
            shooter_xy, target_xy, (vx, vy))
        corrected = compute_corrected_distance(raw_distance, closing)
        return ShootContext(
            corrected_distance=corrected,
            raw_distance=raw_distance,
            closing_speed_mps=closing,
            pose_x=pose.X(),
            pose_y=pose.Y(),
            heading_deg=pose.rotation().degrees(),
            shooter_x=shooter_xy[0],
            shooter_y=shooter_xy[1],
            target_x=target_xy[0],
            target_y=target_xy[1],
            vx=vx,
            vy=vy,
            target_mode=target_mode,
        )
    return _get_context


def configure_operator(operator, turret, launcher, vision,
                       match_setup, h_feed=None, v_feed=None,
                       drivetrain=None, intake=None, intake_spinner=None,
                       driver=None):
    """
    Wire all operator controller bindings.
    Call once from RobotContainer.__init__.
    """
    deadband = CON_ROBOT["stick_deadband"]

    # --- Manual turret: left stick X ---
    Trigger(lambda: abs(operator.getLeftX()) > deadband).whileTrue(
        turret.manual(lambda: operator.getLeftX())
    )

    # --- Manual shoot: right trigger hold, right stick Y controls speed ---
    # Stick Y maps to virtual distance via the shooter distance table,
    # which sets launcher RPS. Auto-feeds when at speed.
    if h_feed is not None and v_feed is not None:
        operator.rightTrigger().whileTrue(
            ManualShoot(launcher, h_feed, v_feed,
                        lambda: -operator.getRightY())
        )
    else:
        operator.rightTrigger().whileTrue(
            ManualLauncher(launcher, lambda: -operator.getRightY())
        )

    # --- Reverse all feeds (un-jam): right bumper hold ---
    # Requires h_feed + v_feed, so it interrupts the right trigger ManualShoot.
    if h_feed is not None and v_feed is not None:
        operator.rightBumper().whileTrue(
            ReverseFeeds(h_feed, v_feed)
        )

    # --- Robot velocity supplier ---
    # get_state().speeds is robot-relative ChassisSpeeds (forward/left).
    # Convert to field-relative so all downstream callers (closing speed,
    # angle compensation) use the same frame as field-coordinate math.
    vel_supplier = None
    if drivetrain is not None:
        def _get_robot_velocity():
            dt_state = drivetrain.get_state()
            vx_robot = dt_state.speeds.vx
            vy_robot = dt_state.speeds.vy
            heading_rad = math.radians(dt_state.pose.rotation().degrees())
            cos_h = math.cos(heading_rad)
            sin_h = math.sin(heading_rad)
            vx_field = vx_robot * cos_h - vy_robot * sin_h
            vy_field = vx_robot * sin_h + vy_robot * cos_h
            return (vx_field, vy_field)
        vel_supplier = _get_robot_velocity

    # --- Shoot context supplier ---
    context_supplier = None
    if drivetrain is not None:
        context_supplier = _make_shoot_context_supplier(
            drivetrain, match_setup.get_alliance, vel_supplier)

    # --- Coordinate aim: left bumper toggle ---
    coord_aim = CoordinateAim(turret, context_supplier=context_supplier,
                              turret_config=CON_TURRET_MINION)
    operator.leftBumper().toggleOnTrue(coord_aim)

    # --- Turret resync: B button ---
    # Operator manually aims at Hub, then presses B to fold the current
    # error into a runtime center-position offset. Recovers from encoder
    # slip, odometry drift, or a slightly mis-tuned center mid-match.
    if drivetrain is not None:
        operator.b().onTrue(
            ResyncTurret(
                turret,
                pose_supplier=drivetrain.get_pose,
                alliance_supplier=match_setup.get_alliance,
                coord_aim=coord_aim,
            )
        )

    # --- Shoot when ready: left trigger hold ---
    if h_feed is not None and v_feed is not None and context_supplier is not None:
        operator.leftTrigger().whileTrue(
            ShootWhenReady(
                launcher, h_feed, v_feed,
                context_supplier=context_supplier,
                on_target_supplier=coord_aim.is_on_target,
            )
        )

    # --- Pit-mode intake jog: Start held + right stick Y ---
    # Lets the pit crew raise/lower the locked intake arm without the
    # position guard interfering. Command outputs 0V when the stick is
    # centered, so just holding Start does nothing on its own. Start
    # alone is a combo the operator will never press by accident.
    if intake is not None:
        operator.start().whileTrue(
            IntakePitMove(intake, lambda: operator.getRightY())
        )

    # --- Hopper agitate: operator LT held + robot stationary + driver not intaking ---
    # Shakes the intake arm while spinning rollers slowly to un-jam Fuel
    # in the hopper during stationary auto-shooting. Suppressed when the
    # driver is running normal intake (driver LT) so we don't fight the
    # intake-while-moving workflow. The trigger composition ensures the
    # command is re-scheduled cleanly when the driver releases their
    # intake trigger (since whileTrue only (re)schedules on edge).
    if (intake is not None and intake_spinner is not None
            and drivetrain is not None and driver is not None):
        def _robot_is_stationary():
            dt_state = drivetrain.get_state()
            speed = math.hypot(dt_state.speeds.vx, dt_state.speeds.vy)
            return speed < CON_INTAKE_HOPPER_AGITATE["stationary_speed_threshold"]

        agitate_trigger = (
            operator.leftTrigger()
            & driver.leftTrigger().negate()
            & Trigger(_robot_is_stationary)
        )
        agitate_trigger.whileTrue(
            IntakeHopperAgitate(intake, intake_spinner)
        )
