"""
Register all named commands with PathPlanner.

PathPlanner event markers and .auto files reference commands by name.
This module registers every command the team uses in auto routines.
Must be called BEFORE loading any .path or .auto files.

Named commands registered here:
  IntakeDown   -- lower the intake arm
  IntakeUp     -- raise the intake arm
  IntakeStart  -- spin intake wheels to pull in Fuel
  IntakeStop   -- stop intake wheels
  AimStart     -- start pose-based turret auto-aim
  AimStop      -- stop turret auto-aim
  ShooterStart -- spin up launcher, feed when at speed (ShootWhenReady)
  ShooterStop  -- stop launcher, hood, and feeders
"""

from pathplannerlib.auto import NamedCommands
from commands2 import ParallelCommandGroup

from commands.coordinate_aim import CoordinateAim
from commands.shoot_when_ready import ShootWhenReady
from constants import CON_INTAKE_SPINNER
from constants.shooter import CON_TURRET_MINION
from utils.logger import get_logger

_log = get_logger("named_commands")


def register_named_commands(intake, intake_spinner, launcher, hood,
                            h_feed, v_feed, turret, context_supplier):
    """Register all named commands for PathPlanner.

    Call this in RobotContainer.__init__() BEFORE creating AutonModes
    (which pre-loads .auto files that resolve named commands).

    Args:
        intake:           Intake subsystem (arm)
        intake_spinner:   IntakeSpinner subsystem (wheels)
        launcher:         Launcher subsystem
        hood:             Hood subsystem
        h_feed:           HFeed subsystem
        v_feed:           VFeed subsystem
        turret:           Turret subsystem
        context_supplier: shoot context supplier (pose, distance, velocity)
    """
    # --- Intake ---
    NamedCommands.registerCommand("IntakeDown", intake.go_down())
    NamedCommands.registerCommand("IntakeUp", intake.go_up())
    NamedCommands.registerCommand("IntakeStart",
        intake_spinner.run_at_voltage(CON_INTAKE_SPINNER["spin_voltage"]))
    NamedCommands.registerCommand("IntakeStop",
        intake_spinner.runOnce(lambda: intake_spinner._stop()))

    # --- Turret auto-aim ---
    NamedCommands.registerCommand("AimStart",
        CoordinateAim(turret,
                      context_supplier=context_supplier,
                      turret_config=CON_TURRET_MINION))
    NamedCommands.registerCommand("AimStop",
        turret.runOnce(lambda: turret._stop()))

    # --- Shooter (ShootWhenReady handles launcher + hood + feeders + unjam) ---
    NamedCommands.registerCommand("ShooterStart",
        ShootWhenReady(launcher, hood, h_feed, v_feed,
                       context_supplier=context_supplier,
                       on_target_supplier=lambda: True))
    NamedCommands.registerCommand("ShooterStop",
        ParallelCommandGroup(
            launcher.runOnce(lambda: launcher._stop()),
            hood.runOnce(lambda: hood._stop()),
            h_feed.runOnce(lambda: h_feed._stop()),
            v_feed.runOnce(lambda: v_feed._stop())))

    _log.info("all named commands registered")
