"""
Operator controller bindings.
All operator button/stick mappings live here to keep robot_container short.

Controls:
    Left stick X        -- Manual turret aim
    Right stick Y       -- Launcher speed (when toggled on via A)
    A button (toggle)   -- Launcher on/off (speed from right stick Y)
    B button (toggle)   -- Feed system on/off (H feed + V feed)
    X button (press)    -- Toggle intake position (out/in)
    Y button (toggle)   -- Auto-aim on/off (turret tracks tags via PD)
    Left bumper (hold)  -- Auto-shoot (vision distance -> launcher/hood)
"""

from commands2 import InstantCommand, ConditionalCommand, ParallelCommandGroup
from commands2.button import Trigger

from constants import CON_ROBOT, CON_H_FEED, CON_V_FEED
from utils.logger import get_logger

_log = get_logger("operator")
from subsystems.turret import Turret
from subsystems.launcher import Launcher
from subsystems.hood import Hood
from subsystems.h_feed import HFeed
from subsystems.v_feed import VFeed
from subsystems.intake import Intake
from handlers.vision import VisionProvider
from commands.auto_aim import AutoAim
from commands.auto_shoot import AutoShoot
from commands.manual_launcher import ManualLauncher


def configure_operator(operator, conveyor, turret, launcher, hood, vision,
                       match_setup, h_feed=None, v_feed=None, intake=None):
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

    # --- Intake: X button toggles between out/in ---
    if intake is not None:
        def _flip_intake():
            state["intake_down"] = not state["intake_down"]

        operator.x().onTrue(
            InstantCommand(_flip_intake).andThen(
                ConditionalCommand(
                    intake.go_down(),
                    intake.go_up(),
                    lambda: state["intake_down"],
                )
            )
        )

    # --- Auto-aim: Y button toggle ---
    operator.y().toggleOnTrue(
        AutoAim(
            turret, vision,
            tag_priority_supplier=match_setup.get_tag_priority,
            tag_offsets_supplier=match_setup.get_tag_offsets,
        )
    )

    # --- Auto-shoot: left bumper hold ---
    operator.leftBumper().whileTrue(
        AutoShoot(launcher, hood, vision,
                  tag_priority_supplier=match_setup.get_tag_priority)
    )

    return state
