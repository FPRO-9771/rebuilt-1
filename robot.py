"""
Robot lifecycle management.
Subclasses TimedRobot and delegates to RobotContainer.
"""

import wpilib
from commands2 import CommandScheduler
from pathplannerlib.auto import AutoBuilder
from pathplannerlib.path import PathPlannerPath
from robot_container import RobotContainer
from telemetry import update_telemetry
from utils.logger import get_logger

_log = get_logger("robot")


class Robot(wpilib.TimedRobot):
    """Main robot class - handles lifecycle events."""

    # The default 20 ms loop is too fast for Python on the roboRIO.
    # 50 ms (20 Hz) keeps us within budget. Drivetrain odometry runs
    # on its own high-frequency thread so driving is not affected.
    _LOOP_PERIOD = 0.050

    def __init__(self):
        super().__init__(self._LOOP_PERIOD)

    def robotInit(self):
        """Called once when the robot starts."""
        if self.isSimulation():
            wpilib.DriverStation.silenceJoystickConnectionWarning(True)
        self.container = RobotContainer()
        self.auto_command = None

    def robotPeriodic(self):
        """Called every 20ms regardless of mode."""
        CommandScheduler.getInstance().run()
        update_telemetry()
        self.container.match_setup.update()

    # --- Autonomous ---

    def autonomousInit(self):
        """Called when autonomous mode starts."""
        pose = self.container.match_setup.get_pose()
        path_name = pose.get("auto_path", "")

        if not path_name:
            _log.warning("No auto path configured for selected pose")
            return

        try:
            path = PathPlannerPath.fromPathFile(path_name)
            self.auto_command = AutoBuilder.followPath(path)
            self.auto_command.schedule()
            _log.info(f"Auto started: {path_name}")
        except Exception as e:
            _log.error(f"Failed to load auto path '{path_name}': {e}")

    def autonomousPeriodic(self):
        """Called every 20ms during autonomous."""
        pass

    def autonomousExit(self):
        """Called when autonomous mode ends."""
        if self.auto_command:
            self.auto_command.cancel()

    # --- Teleop ---

    def teleopInit(self):
        """Called when teleop mode starts."""
        # Cancel any running auto command
        if self.auto_command:
            self.auto_command.cancel()

    def teleopPeriodic(self):
        """Called every 20ms during teleop."""
        pass

    def teleopExit(self):
        """Called when teleop mode ends."""
        pass

    # --- Disabled ---

    def disabledInit(self):
        """Called when robot is disabled."""
        pass

    def disabledPeriodic(self):
        """Called every 20ms while disabled."""
        pass

    # --- Test ---

    def testInit(self):
        """Called when test mode starts."""
        CommandScheduler.getInstance().cancelAll()

    def testPeriodic(self):
        """Called every 20ms during test mode."""
        pass
