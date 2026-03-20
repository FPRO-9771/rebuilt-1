"""
Operator controller bindings.
All operator button/stick mappings live here to keep robot_container short.

Controls:
    Left stick X         -- Manual turret aim
    Right stick Y        -- Launcher speed (when held via right trigger)
    Left bumper (toggle) -- Coordinate aim (turret aims at Hub via odometry)
    Left trigger (hold)  -- Shoot when ready (launcher + feed when on target)
    Right bumper (hold)  -- Reverse all feeds (un-jam, interrupts right trigger)
    Right trigger (hold) -- Manual shoot (launcher + auto-feed when at speed)
"""

from commands2.button import Trigger

from constants import CON_ROBOT
from constants.shooter import CON_TURRET_MINION
from constants.pose import CON_POSE
from calculations.shooter_position import get_shooter_field_position
from calculations.target_state import compute_range_state, ShootContext
from calculations.distance_compensation import compute_corrected_distance
from utils.logger import get_logger

_log = get_logger("operator")
from subsystems.turret import Turret
from subsystems.h_feed import HFeed
from subsystems.v_feed import VFeed
from commands.coordinate_aim import CoordinateAim
from commands.manual_launcher import ManualLauncher
from commands.manual_shoot import ManualShoot
from commands.reverse_feeds import ReverseFeeds
from commands.shoot_when_ready import ShootWhenReady


def _make_shoot_context_supplier(drivetrain, alliance_supplier,
                                 velocity_supplier=None):
    """Build a callable that returns a ShootContext with full pose context."""
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
                       match_setup, h_feed=None, v_feed=None,
                       drivetrain=None):
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
    # which sets both launcher RPS and hood position. Auto-feeds when at speed.
    if h_feed is not None and v_feed is not None:
        operator.rightTrigger().whileTrue(
            ManualShoot(launcher, hood, h_feed, v_feed,
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
            ReverseFeeds(h_feed, v_feed, conveyor)
        )

    # --- Robot velocity supplier ---
    vel_supplier = None
    if drivetrain is not None:
        def _get_robot_velocity():
            dt_state = drivetrain.get_state()
            return (dt_state.speeds.vx, dt_state.speeds.vy)
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

    # --- Shoot when ready: left trigger hold ---
    if h_feed is not None and v_feed is not None and context_supplier is not None:
        operator.leftTrigger().whileTrue(
            ShootWhenReady(
                launcher, hood, h_feed, v_feed,
                context_supplier=context_supplier,
                on_target_supplier=coord_aim.is_on_target,
            )
        )
