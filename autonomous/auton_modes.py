"""
Autonomous mode compositions.
Each method returns a command that performs a complete auto routine.

Example usage:
```
auton = AutonModes(drivetrain, turret, launcher, hood, h_feed, v_feed,
                   context_supplier, intake, intake_spinner)
auto_cmd = auton.blue_center()
auto_cmd.schedule()
```
"""

from commands2 import Command, SequentialCommandGroup, ParallelCommandGroup, ParallelRaceGroup, WaitCommand
from pathplannerlib.auto import AutoBuilder
from pathplannerlib.path import PathPlannerPath

from constants import CON_INTAKE_SPINNER
from utils.logger import get_logger

_log = get_logger("auton_modes")

# How long to try shooting after reaching the final position (seconds).
_SHOOT_TIMEOUT = 12.0

# How long to lower the intake before the path starts (non-center paths).
_INTAKE_PREDEPLOY_TIME = 1.0


class AutonModes:
    """
    Factory for autonomous command compositions.
    Inject subsystems via constructor for testability.
    """

    def __init__(self, drivetrain=None, turret=None, launcher=None, hood=None,
                 h_feed=None, v_feed=None, context_supplier=None,
                 intake=None, intake_spinner=None,
                 conveyor=None, vision=None):
        self.drivetrain = drivetrain
        self.turret = turret
        self.launcher = launcher
        self.hood = hood
        self.h_feed = h_feed
        self.v_feed = v_feed
        self._context_supplier = context_supplier
        self.intake = intake
        self.intake_spinner = intake_spinner
        self.conveyor = conveyor
        self.vision = vision

    def do_nothing(self) -> Command:
        """Auto that does nothing - safe default."""
        return WaitCommand(15.0)

    def follow_path(self, path_name: str) -> Command:
        """Follow a PathPlanner path by name (without .path extension)."""
        try:
            path = PathPlannerPath.fromPathFile(path_name)
            return AutoBuilder.followPath(path)
        except Exception as e:
            _log.error(f"Failed to load path '{path_name}': {e}")
            return WaitCommand(15.0)

    def _path_and_shoot(self, path_name: str, intake_before_path: bool = False) -> Command:
        """
        Full auto routine:
          - CoordinateAim runs the entire time, aiming turret at Hub.
          - intake_before_path=True  (left/right): intake deploys for
            _INTAKE_PREDEPLOY_TIME seconds, then path starts with intake held down.
          - intake_before_path=False (center): intake deploys 1 second into
            the path to avoid interference at the Hub wall.
          - After path ends: ShootWhenReady fires once turret is on target.
        """
        if not all([self.turret, self.launcher, self.hood,
                    self.h_feed, self.v_feed, self._context_supplier]):
            _log.error(f"_path_and_shoot: missing subsystems -- doing nothing")
            return WaitCommand(15.0)

        from commands.coordinate_aim import CoordinateAim
        from commands.shoot_when_ready import ShootWhenReady
        from constants.shooter import CON_TURRET_MINION

        coord_aim = CoordinateAim(
            self.turret,
            context_supplier=self._context_supplier,
            turret_config=CON_TURRET_MINION,
        )
        shoot = ShootWhenReady(
            self.launcher, self.hood, self.h_feed, self.v_feed,
            context_supplier=self._context_supplier,
            on_target_supplier=coord_aim.is_on_target,
        )

        intake_running = ParallelCommandGroup(
            self.intake.hold_down(),
            self.intake_spinner.run_at_voltage(CON_INTAKE_SPINNER["spin_voltage"]),
        )

        if intake_before_path:
            # Deploy intake first, then follow path with intake held down
            drive_phase = SequentialCommandGroup(
                intake_running.withTimeout(_INTAKE_PREDEPLOY_TIME),
                ParallelRaceGroup(
                    self.follow_path(path_name),
                    self.intake.hold_down(),
                    self.intake_spinner.run_at_voltage(CON_INTAKE_SPINNER["spin_voltage"]),
                ),
            )
        else:
            # Center paths: start path immediately, deploy intake after 1 second
            drive_phase = ParallelRaceGroup(
                self.follow_path(path_name),
                SequentialCommandGroup(
                    WaitCommand(1.0),
                    ParallelCommandGroup(
                        self.intake.hold_down(),
                        self.intake_spinner.run_at_voltage(CON_INTAKE_SPINNER["spin_voltage"]),
                    ),
                ),
            )

        # Shoot phase: feed once on target, timeout after _SHOOT_TIMEOUT seconds
        shoot_phase = shoot.withTimeout(_SHOOT_TIMEOUT)

        # coord_aim wraps everything -- turret aims from start to finish
        return ParallelRaceGroup(
            coord_aim,
            SequentialCommandGroup(drive_phase, shoot_phase),
        )

    # --- Blue routines ---

    def blue_center(self) -> Command:
        return self._path_and_shoot("Auto Blue Center", intake_before_path=False)

    def blue_left(self) -> Command:
        return self._path_and_shoot("Auto Blue Left", intake_before_path=True)

    def blue_right(self) -> Command:
        return self._path_and_shoot("Auto Blue Right", intake_before_path=True)

    # --- Red routines ---

    def red_center(self) -> Command:
        return self._path_and_shoot("Auto Red Center", intake_before_path=False)

    def red_left(self) -> Command:
        return self._path_and_shoot("Auto Red Left", intake_before_path=True)

    def red_right(self) -> Command:
        return self._path_and_shoot("Auto Red Right", intake_before_path=True)
