"""
Operator controller bindings.
All operator button/stick mappings live here to keep robot_container short.

Controls:
    Left stick X        -- Manual turret aim
    Left stick Y        -- Manual hood nudge (tap up = more closed, tap down = more open)
    Right stick Y       -- Launcher speed (when toggled on via A)
    A button (toggle)   -- Launcher on/off (speed from right stick Y)
    B button (toggle)   -- Feed system on/off (H feed + V feed)
    Y button (toggle)   -- Coordinate aim (turret aims at Hub via odometry)
    Left bumper (hold)  -- Auto-shoot (pose distance -> launcher/hood)
    Left trigger (hold) -- Shoot when ready (launcher + feed when on target)
    Right trigger (hold) -- Reverse H feed (un-jam)
    X button (toggle)     -- Intake up/down
    Right bumper (toggle) -- Intake spinner on/off
"""

import commands2
from commands2 import ParallelCommandGroup
from commands2.button import Trigger

from constants import CON_ROBOT, CON_H_FEED, CON_V_FEED, CON_INTAKE_SPINNER
from constants.shooter import CON_TURRET_MINION
from constants.pose import CON_POSE
from calculations.shooter_position import get_shooter_field_position
from calculations.target_state import compute_range_state, ShootContext
from calculations.distance_compensation import compute_corrected_distance
from utils.logger import get_logger

_log = get_logger("operator")
from subsystems.turret import Turret
from subsystems.launcher import Launcher
from subsystems.hood import Hood
from subsystems.h_feed import HFeed
from subsystems.v_feed import VFeed
from subsystems.intake import Intake
from subsystems.intake_spinner import IntakeSpinner
from commands.auto_shoot import AutoShoot
from commands.coordinate_aim import CoordinateAim
from commands.manual_hood import ManualHood
from commands.manual_launcher import ManualLauncher
from commands.shoot_when_ready import ShootWhenReady


def _make_shoot_context_supplier(drivetrain, alliance_supplier,
                                 velocity_supplier=None):
    """Build a callable that returns a ShootContext with full pose context.

    Computes the distance from the shooter (not robot center) to the
    alliance Hub, adjusts for closing speed, and packages everything
    the commands need for both control and logging.
    """
    def _get_context():
        pose = drivetrain.get_pose()
        shooter_xy = get_shooter_field_position(
            pose,
            CON_POSE["shooter_offset_x"],
            CON_POSE["shooter_offset_y"],
        )

        alliance = alliance_supplier()
        target_xy = (alliance["target_x"], alliance["target_y"])

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
        )

    return _get_context


def configure_operator(operator, conveyor, turret, launcher, hood, vision,
                       match_setup, h_feed=None, v_feed=None, intake=None,
                       intake_spinner=None, drivetrain=None):
    """
    Wire all operator controller bindings.
    Call once from RobotContainer.__init__.
    """
    deadband = CON_ROBOT["joystick_deadband"]

    # Mutable state for intake toggle
    state = {"intake_down": False}

    # --- Manual turret: left stick X ---
    Trigger(lambda: abs(operator.getLeftX()) > deadband).whileTrue(
        turret.manual(lambda: operator.getLeftX())
    )

    # --- Manual hood: left stick Y nudge ---
    # Tap up = more closed, tap down = more open
    hood.setDefaultCommand(
        ManualHood(hood, lambda: -operator.getLeftY(), deadband)
    )

    # --- DEBUG: D-pad up/down sends raw voltage to hood ---
    # This bypasses closed-loop control to test if the motor moves at all.
    # Remove after debugging.
    _test_volts = 6.0
    operator.povUp().whileTrue(
        hood.runEnd(
            lambda: hood._set_voltage(_test_volts),
            lambda: hood._stop(),
        )
    )
    operator.povDown().whileTrue(
        hood.runEnd(
            lambda: hood._set_voltage(-_test_volts),
            lambda: hood._stop(),
        )
    )

    # --- Launcher: A button toggle, right stick Y controls speed ---
    operator.a().toggleOnTrue(
        ManualLauncher(launcher, lambda: -operator.getRightY())
    )

    # --- Feeds: B button toggle ---
    if h_feed is not None and v_feed is not None:
        operator.b().toggleOnTrue(
            ParallelCommandGroup(
                h_feed.run_at_voltage(CON_H_FEED["feed_voltage"]),
                v_feed.run_at_voltage(CON_V_FEED["feed_voltage"]),
            )
        )

    # --- Intake spinner: right bumper toggle ---
    if intake_spinner is not None:
        operator.rightBumper().toggleOnTrue(
            intake_spinner.run_at_voltage(CON_INTAKE_SPINNER["spin_voltage"]),
        )

    # --- Intake up/down: X button alternates ---
    if intake is not None:
        intake_state = {"down": False}

        def _toggle_intake():
            intake_state["down"] = not intake_state["down"]
            if intake_state["down"]:
                return intake.go_down()
            else:
                return intake.go_up()

        operator.x().onTrue(
            commands2.DeferredCommand(_toggle_intake, intake)
        )

    # --- Reverse H feed (un-jam): right trigger hold ---
    if h_feed is not None:
        operator.rightTrigger().whileTrue(
            h_feed.run_at_voltage(CON_H_FEED["reverse_voltage"])
        )

    # --- Robot velocity supplier for coordinate aim and distance ---
    vel_supplier = None
    if drivetrain is not None:
        def _get_robot_velocity():
            dt_state = drivetrain.get_state()
            return (dt_state.speeds.vx, dt_state.speeds.vy)
        vel_supplier = _get_robot_velocity

    # --- Shoot context supplier (shared by all shooter commands) ---
    context_supplier = None
    if drivetrain is not None:
        context_supplier = _make_shoot_context_supplier(
            drivetrain, match_setup.get_alliance, vel_supplier)

    # --- Coordinate aim: Y button toggle ---
    # Aims turret at Hub using odometry -- no vision needed.
    coord_aim = CoordinateAim(turret, context_supplier=context_supplier,
                              turret_config=CON_TURRET_MINION)
    operator.y().toggleOnTrue(coord_aim)

    # --- Auto-shoot: left bumper hold ---
    if context_supplier is not None:
        operator.leftBumper().whileTrue(
            AutoShoot(launcher, hood,
                      context_supplier=context_supplier)
        )

    # --- Shoot when ready: left trigger hold ---
    # Spins launcher immediately; feeds only when at speed AND on target.
    if h_feed is not None and v_feed is not None and context_supplier is not None:
        operator.leftTrigger().whileTrue(
            ShootWhenReady(
                launcher, hood, h_feed, v_feed,
                context_supplier=context_supplier,
                on_target_supplier=coord_aim.is_on_target,
            )
        )

    return state
