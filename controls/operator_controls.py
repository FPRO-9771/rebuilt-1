"""
Operator controller bindings.
All operator button/stick mappings live here to keep robot_container short.

Controls:
    Right stick Y   -- Conveyor manual
    X button (hold) -- Run H feed + V feed simultaneously
    Y button (hold) -- Shoot (spin launcher + set hood; feeder when locked)
    Left stick X    -- Manual turret override
    A button        -- Toggle manual launcher on/off
    Left bumper     -- Increase launcher speed (+5%)
    Left trigger    -- Decrease launcher speed (-5%)
    Right bumper    -- Nudge hood up
    Right trigger   -- Nudge hood down

Auto-tracking: turret auto-tracks scoring tags as its default command
during teleop. Manual turret stick interrupts; tracking resumes on release.
"""

from commands2 import Command, InstantCommand, ParallelCommandGroup
from commands2.button import Trigger

from constants import CON_ROBOT, CON_MANUAL, CON_HOOD, CON_H_FEED, CON_V_FEED
from utils.logger import get_logger

_log = get_logger("operator")
from subsystems.conveyor import Conveyor
from subsystems.turret import Turret
from subsystems.launcher import Launcher
from subsystems.hood import Hood
from subsystems.h_feed import HFeed
from subsystems.v_feed import VFeed
from handlers.vision import VisionProvider
from commands.auto_tracker import AutoTracker
from commands.shoot_command import ShootCommand


def configure_operator(operator, conveyor, turret, launcher, hood, vision,
                       match_setup, h_feed=None, v_feed=None):
    """
    Wire all operator controller bindings.
    Call once from RobotContainer.__init__.
    """
    deadband = CON_ROBOT["joystick_deadband"]

    # Mutable state for manual speed/position control
    state = {
        "launcher_rps": CON_MANUAL["launcher_default_rps"],
        "hood_position": CON_MANUAL["hood_default_position"],
    }

    # --- Conveyor: right stick Y ---
    if conveyor is not None:
        Trigger(lambda: abs(operator.getRightY()) > deadband).whileTrue(
            conveyor.manual(lambda: -operator.getRightY())
        )

    # --- Feeds: X button (hold) -- run both feeds simultaneously ---
    if h_feed is not None and v_feed is not None:
        operator.x().whileTrue(
            ParallelCommandGroup(
                h_feed.run_at_voltage(CON_H_FEED["feed_voltage"]),
                v_feed.run_at_voltage(CON_V_FEED["feed_voltage"]),
            )
        )

    # --- Auto-tracker: turret default command (teleop only) ---
    # Tag priority and offsets come from match_setup (SmartDashboard choosers)
    tracker = AutoTracker(
        turret, vision,
        tag_priority_supplier=match_setup.get_tag_priority,
        tag_offsets_supplier=match_setup.get_tag_offsets,
    )
    turret.setDefaultCommand(tracker)

    # --- Shoot: Y button hold ---
    operator.y().whileTrue(
        ShootCommand(tracker, launcher, hood)
    )

    # --- Manual turret: left stick X ---
    Trigger(lambda: abs(operator.getLeftX()) > deadband).whileTrue(
        turret.manual(lambda: operator.getLeftX())
    )

    # --- Manual launcher: A button toggle ---
    operator.a().toggleOnTrue(
        _LauncherToggleCommand(launcher, lambda: state["launcher_rps"])
    )

    # --- Launcher speed: left bumper (+) / left trigger (-) ---
    step = CON_MANUAL["launcher_speed_step"]
    operator.leftBumper().onTrue(
        InstantCommand(lambda: adjust_launcher_rps(state, step))
    )
    operator.leftTrigger().onTrue(
        InstantCommand(lambda: adjust_launcher_rps(state, -step))
    )

    # --- Hood: default command holds position from state ---
    if hood._enabled:
        hood.setDefaultCommand(
            hood.go_to_position_supplier(lambda: state["hood_position"])
        )

        # --- Hood nudge: right bumper (+) / right trigger (-) ---
        # Each press just updates state; default command picks up the new target
        hood_step = CON_MANUAL["hood_position_step"]
        operator.rightBumper().onTrue(
            InstantCommand(lambda: nudge_hood(state, hood_step))
        )
        operator.rightTrigger().onTrue(
            InstantCommand(lambda: nudge_hood(state, -hood_step))
        )

    return state


# --- Helpers (module-level for testability) ---

def adjust_launcher_rps(state, delta):
    """Bump launcher RPS by delta, clamped to [0, max]."""
    state["launcher_rps"] = max(
        0, min(state["launcher_rps"] + delta, CON_MANUAL["launcher_max_rps"])
    )


def nudge_hood(state, delta):
    """Bump hood position by delta, clamped to limits."""
    old = state["hood_position"]
    state["hood_position"] = max(
        CON_HOOD["min_position"],
        min(state["hood_position"] + delta, CON_HOOD["max_position"]),
    )
    _log.info(
        f"nudge delta={delta:+.4f} target={state['hood_position']:.4f}"
    )


class _LauncherToggleCommand(Command):
    """Runs launcher at a dynamic RPS read from a supplier each cycle."""

    def __init__(self, launcher, rps_supplier):
        super().__init__()
        self.launcher = launcher
        self.rps_supplier = rps_supplier
        self.addRequirements(launcher)

    def execute(self):
        self.launcher._set_velocity(self.rps_supplier())

    def isFinished(self):
        return False

    def end(self, interrupted):
        self.launcher._stop()
