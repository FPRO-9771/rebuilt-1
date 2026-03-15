"""
Autonomous mode compositions.
Each method returns a command that performs a complete auto routine.

Example usage:
```
auton = AutonModes(drivetrain)
auto_cmd = auton.follow_path("TEST PATH FPRO")
auto_cmd.schedule()
```
"""

from commands2 import Command, WaitCommand
from pathplannerlib.auto import AutoBuilder
from pathplannerlib.path import PathPlannerPath

from utils.logger import get_logger

_log = get_logger("auton_modes")


class AutonModes:
    """
    Factory for autonomous command compositions.
    Inject subsystems via constructor for testability.
    """

    def __init__(self, drivetrain=None, conveyor=None, vision=None):
        """
        Args:
            drivetrain: Drivetrain subsystem
            conveyor: Conveyor subsystem
            vision: VisionProvider instance
        """
        self.drivetrain = drivetrain
        self.conveyor = conveyor
        self.vision = vision

    def do_nothing(self) -> Command:
        """Auto that does nothing - safe default."""
        return WaitCommand(15.0)

    def follow_path(self, path_name: str) -> Command:
        """
        Follow a PathPlanner path by name.

        Args:
            path_name: Name of the path file (without .path extension)
        """
        try:
            path = PathPlannerPath.fromPathFile(path_name)
            return AutoBuilder.followPath(path)
        except Exception as e:
            _log.error(f"Failed to load path '{path_name}': {e}")
            return WaitCommand(15.0)
