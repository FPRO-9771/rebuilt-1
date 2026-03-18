"""
Autonomous mode compositions.
Each method returns a command that performs a complete auto routine.

All intake, shooter, and feeder actions are controlled by PathPlanner event
markers placed on each path. Register these named commands in robot_container.py:

  "IntakeDown"   -- lower intake arm
  "IntakeStart"  -- start intake spinner
  "IntakeStop"   -- stop intake spinner
  "IntakeUp"     -- raise intake arm
  "ShooterStart" -- spin up launcher + set hood from distance
  "ShooterStop"  -- stop launcher and hood
  "FeedersStart" -- run both feeders
  "FeedersStop"  -- stop both feeders

CoordinateAim (turret auto-aim) runs for the entire duration in Python code.

Example usage:
```
auton = AutonModes(drivetrain, turret, launcher, hood, h_feed, v_feed,
                   context_supplier)
auto_cmd = auton.blue_center()
auto_cmd.schedule()
```
"""

from commands2 import Command, SequentialCommandGroup, ParallelRaceGroup, WaitCommand
from pathplannerlib.auto import AutoBuilder
from pathplannerlib.path import PathPlannerPath

from utils.logger import get_logger

_log = get_logger("auton_modes")

# How long to keep auto-aim active after the path ends, while event marker
# commands (ShooterStart, FeedersStart) finish their work.
_POST_PATH_WAIT = 12.0


class AutonModes:
    """
    Factory for autonomous command compositions.
    Inject subsystems via constructor for testability.
    """

    def __init__(self, drivetrain=None, turret=None, launcher=None, hood=None,
                 h_feed=None, v_feed=None, context_supplier=None,
                 conveyor=None, vision=None):
        self.drivetrain = drivetrain
        self.turret = turret
        self.launcher = launcher
        self.hood = hood
        self.h_feed = h_feed
        self.v_feed = v_feed
        self._context_supplier = context_supplier
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

    def _build_routine(self, path_name: str) -> Command:
        """
        Build a full auto routine for the given path.
        CoordinateAim runs the entire time. All other actions (intake, shooter,
        feeders) are triggered by event markers placed on the path in PathPlanner.
        After the path ends, auto-aim stays active for _POST_PATH_WAIT seconds
        so that ShooterStart/FeedersStart event markers can finish their work.
        """
        if not all([self.turret, self._context_supplier]):
            _log.error(f"_build_routine: missing subsystems -- doing nothing")
            return WaitCommand(15.0)

        from commands.coordinate_aim import CoordinateAim
        from constants.shooter import CON_TURRET_MINION

        coord_aim = CoordinateAim(
            self.turret,
            context_supplier=self._context_supplier,
            turret_config=CON_TURRET_MINION,
        )

        # coord_aim wraps everything -- turret aims from start to finish.
        # After the path ends, WaitCommand keeps coord_aim alive while the
        # ShooterStart/FeedersStart event marker commands finish shooting.
        return ParallelRaceGroup(
            coord_aim,
            SequentialCommandGroup(
                self.follow_path(path_name),
                WaitCommand(_POST_PATH_WAIT),
            ),
        )

    # --- Blue routines ---

    def blue_center(self) -> Command:
        return self._build_routine("Auto Blue Center")

    def blue_left(self) -> Command:
        return self._build_routine("Auto Blue Left")

    def blue_right(self) -> Command:
        return self._build_routine("Auto Blue Right")

    # --- Red routines ---

    def red_center(self) -> Command:
        return self._build_routine("Auto Red Center")

    def red_left(self) -> Command:
        return self._build_routine("Auto Red Left")

    def red_right(self) -> Command:
        return self._build_routine("Auto Red Right")

    # --- Test routines ---

    def mini_test(self) -> Command:
        return self._build_routine("Mini Test")
