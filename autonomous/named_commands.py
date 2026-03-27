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
  ShooterStart      -- spin up launcher, feed when at speed (ShootWhenReady)
  ManualShootStart  -- manual shoot at center distance (for center autons)
  ShooterStop       -- stop launcher and feeders
"""

from pathplannerlib.auto import NamedCommands
from commands2 import Command, ParallelCommandGroup

from commands.coordinate_aim import CoordinateAim
from commands.manual_shoot import ManualShoot
from commands.shoot_when_ready import ShootWhenReady
from constants import CON_INTAKE_SPINNER
from constants.shoot_hardware import CON_TURRET_MINION
from utils.logger import get_logger

_log = get_logger("named_commands")


class _LoggedCommand(Command):
    """Wrapper that logs when a named command starts and ends."""

    def __init__(self, name: str, inner: Command):
        super().__init__()
        self._name = name
        self._inner = inner
        # Forward subsystem requirements so the scheduler sees them
        self.addRequirements(*inner.getRequirements())

    def initialize(self):
        _log.warning(f"NAMED CMD '{self._name}' -> initialize")
        self._inner.initialize()

    def execute(self):
        self._inner.execute()

    def isFinished(self) -> bool:
        finished = self._inner.isFinished()
        if finished:
            _log.warning(f"NAMED CMD '{self._name}' -> isFinished=True")
        return finished

    def end(self, interrupted: bool):
        _log.warning(
            f"NAMED CMD '{self._name}' -> end(interrupted={interrupted})"
        )
        self._inner.end(interrupted)

    def runsWhenDisabled(self) -> bool:
        return self._inner.runsWhenDisabled()


def _logged(name: str, cmd: Command) -> Command:
    """Register a named command with logging wrapper."""
    wrapped = _LoggedCommand(name, cmd)
    NamedCommands.registerCommand(name, wrapped)
    return wrapped


def register_named_commands(intake, intake_spinner, launcher,
                            h_feed, v_feed, turret, context_supplier):
    """Register all named commands for PathPlanner.

    Call this in RobotContainer.__init__() BEFORE creating AutonModes
    (which pre-loads .auto files that resolve named commands).

    Args:
        intake:           Intake subsystem (arm)
        intake_spinner:   IntakeSpinner subsystem (wheels)
        launcher:         Launcher subsystem
        h_feed:           HFeed subsystem
        v_feed:           VFeed subsystem
        turret:           Turret subsystem
        context_supplier: shoot context supplier (pose, distance, velocity)
    """
    # --- Intake ---
    _logged("IntakeDown", intake.go_down())
    _logged("IntakeUp", intake.go_up())
    _logged("IntakeStart",
        intake_spinner.run_at_voltage(CON_INTAKE_SPINNER["spin_voltage"]))
    _logged("IntakeStop",
        intake_spinner.runOnce(lambda: intake_spinner._stop()))

    # --- Turret auto-aim ---
    aim_cmd = CoordinateAim(turret,
                            context_supplier=context_supplier,
                            turret_config=CON_TURRET_MINION)
    _logged("AimStart", aim_cmd)
    _logged("AimStop",
        turret.runOnce(lambda: turret._stop()))

    # --- Shooter (ShootWhenReady handles launcher + feeders + unjam) ---
    _logged("ShooterStart",
        ShootWhenReady(launcher, h_feed, v_feed,
                       context_supplier=context_supplier,
                       on_target_supplier=aim_cmd.is_on_target))

    # --- Manual shoot (fixed stick=0.0 = center distance, for center autons) ---
    _logged("ManualShootStart",
        ManualShoot(launcher, h_feed, v_feed,
                    stick_supplier=lambda: 0.0))

    _logged("ShooterStop",
        ParallelCommandGroup(
            launcher.runOnce(lambda: launcher._stop()),
            h_feed.runOnce(lambda: h_feed._stop()),
            v_feed.runOnce(lambda: v_feed._stop())))

    _log.info("all named commands registered")
