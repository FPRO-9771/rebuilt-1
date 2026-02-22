"""
Operator controller bindings.
All operator button/stick mappings live here to keep robot_container short.

Controls:
    Right stick Y   — Conveyor manual
    Y button        — Toggle auto shooter on/off
    Left stick X    — Manual turret override
    A button        — Toggle manual launcher on/off
    Left bumper     — Increase launcher speed (+5%)
    Left trigger    — Decrease launcher speed (-5%)
    Right bumper    — Nudge hood up
    Right trigger   — Nudge hood down
"""

from commands2 import Command, InstantCommand
from commands2.button import CommandXboxController, Trigger

from constants import CON_ROBOT, CON_MANUAL, CON_HOOD
from subsystems.conveyor import Conveyor
from subsystems.turret import Turret
from subsystems.launcher import Launcher
from subsystems.hood import Hood
from handlers.vision import VisionProvider
from commands.shooter_orchestrator import ShooterOrchestrator


def configure_operator(operator, conveyor, turret, launcher, hood, vision):
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
    Trigger(lambda: abs(operator.getRightY()) > deadband).whileTrue(
        conveyor.manual(lambda: -operator.getRightY())
    )

    # --- Auto shooter: Y button toggle ---
    operator.y().toggleOnTrue(
        ShooterOrchestrator(turret, launcher, hood, vision)
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

    # --- Hood nudge: right bumper (+) / right trigger (-) ---
    hood_step = CON_MANUAL["hood_position_step"]
    operator.rightBumper().onTrue(
        hood.runOnce(lambda: nudge_hood(state, hood_step, hood))
    )
    operator.rightTrigger().onTrue(
        hood.runOnce(lambda: nudge_hood(state, -hood_step, hood))
    )

    return state


# --- Helpers (module-level for testability) ---

def adjust_launcher_rps(state, delta):
    """Bump launcher RPS by delta, clamped to [0, max]."""
    state["launcher_rps"] = max(
        0, min(state["launcher_rps"] + delta, CON_MANUAL["launcher_max_rps"])
    )


def nudge_hood(state, delta, hood):
    """Bump hood position by delta, clamp to limits, and command the motor."""
    state["hood_position"] = max(
        CON_HOOD["min_position"],
        min(state["hood_position"] + delta, CON_HOOD["max_position"]),
    )
    hood._set_position(state["hood_position"])


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
