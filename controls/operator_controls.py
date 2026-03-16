"""
Operator controller bindings.
All operator button/stick mappings live here to keep robot_container short.

Controls:
    Left stick X        -- Manual turret aim
    Right stick Y       -- Launcher speed (when toggled on via A)
    A button (toggle)   -- Launcher on/off (speed from right stick Y)
    B button (toggle)   -- Feed system on/off (H feed + V feed)
    X button (toggle)   -- TEMP: FindTarget sweep (turret sweeps to find tags)
    Y button (toggle)   -- Coordinate aim (turret aims at Hub via odometry)
    Left bumper (hold)  -- Auto-shoot (vision distance -> launcher/hood)
    Left trigger (hold) -- Shoot when ready (launcher + feed when on target)
    Right bumper (toggle) -- Intake deploy + spinner on/off
"""

from commands2 import InstantCommand, ParallelCommandGroup
from commands2.button import Trigger

from constants import CON_ROBOT, CON_H_FEED, CON_V_FEED, CON_INTAKE_SPINNER
from utils.logger import get_logger

_log = get_logger("operator")
from subsystems.turret import Turret
from subsystems.launcher import Launcher
from subsystems.hood import Hood
from subsystems.h_feed import HFeed
from subsystems.v_feed import VFeed
from subsystems.intake import Intake
from subsystems.intake_spinner import IntakeSpinner
from handlers.vision import VisionProvider
from commands.auto_aim import AutoAim
from commands.auto_shoot import AutoShoot
from commands.coordinate_aim import CoordinateAim
from commands.find_target import FindTarget
from commands.manual_launcher import ManualLauncher
from commands.shoot_when_ready import ShootWhenReady


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

    # --- TEMP: FindTarget sweep on X button (toggle) ---
    # For testing the sweep on the real robot. Remove once integrated with AutoAim.
    operator.x().toggleOnTrue(
        FindTarget(
            turret, vision,
            tag_priority_supplier=match_setup.get_tag_priority,
        )
    )

    # --- Intake: X button toggles between out/in ---
    # COMMENTED OUT -- intake held down for practice, no toggle needed
    # if intake is not None:
    #     def _toggle_intake():
    #         state["intake_down"] = not state["intake_down"]
    #         if state["intake_down"]:
    #             intake.go_down().schedule()
    #         else:
    #             intake.go_up().schedule()
    #
    #     operator.x().onTrue(InstantCommand(_toggle_intake))

    # --- Intake deploy + spinner: right bumper toggle ---
    if intake is not None and intake_spinner is not None:
        operator.rightBumper().toggleOnTrue(
            ParallelCommandGroup(
                intake.hold_down(),
                intake_spinner.run_at_voltage(CON_INTAKE_SPINNER["spin_voltage"]),
            )
        )

    # --- Coordinate aim: Y button toggle ---
    # Aims turret at Hub using odometry -- no vision needed.
    coord_aim = CoordinateAim(
        turret, drivetrain,
        alliance_supplier=match_setup.get_alliance,
    )
    operator.y().toggleOnTrue(coord_aim)

    # --- Auto-aim (not bound to a button -- used by shoot-when-ready) ---
    vel_supplier = None
    if drivetrain is not None:
        def _get_robot_velocity():
            state = drivetrain.get_state()
            return (state.speeds.vx, state.speeds.vy)
        vel_supplier = _get_robot_velocity

    auto_aim = AutoAim(
        turret, vision,
        tag_priority_supplier=match_setup.get_tag_priority,
        tag_offsets_supplier=match_setup.get_tag_offsets,
        robot_velocity_supplier=vel_supplier,
    )

    # --- Auto-shoot: left bumper hold ---
    operator.leftBumper().whileTrue(
        AutoShoot(launcher, hood, vision,
                  tag_priority_supplier=match_setup.get_tag_priority)
    )

    # --- Shoot when ready: left trigger hold ---
    # Spins launcher immediately; feeds only when at speed AND on target.
    if h_feed is not None and v_feed is not None:
        operator.leftTrigger().whileTrue(
            ShootWhenReady(
                launcher, hood, h_feed, v_feed, vision,
                tag_priority_supplier=match_setup.get_tag_priority,
                on_target_supplier=auto_aim.is_on_target,
            )
        )

    return state
