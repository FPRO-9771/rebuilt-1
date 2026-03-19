"""
Robot lifecycle management.
Subclasses TimedRobot and delegates to RobotContainer.
"""

import wpilib
from commands2 import CommandScheduler
from wpimath.geometry import Pose2d, Rotation2d
from robot_container import RobotContainer
from telemetry import update_telemetry
from constants.debug import DEBUG
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
        self._auto_periodic_count = 0

    def robotInit(self):
        """Called once when the robot starts."""
        if self.isSimulation():
            wpilib.DriverStation.silenceJoystickConnectionWarning(True)
        self.container = RobotContainer()
        self.auto_command = None

    def _apply_selected_pose(self):
        """Reset drivetrain odometry to the pose selected in Elastic."""
        pose = self.container.match_setup.get_pose()
        x = pose.get("start_x", 0.0)
        y = pose.get("start_y", 0.0)
        heading = pose.get("start_heading", 0.0)
        _log.info(f"_apply_selected_pose: x={x:.3f} y={y:.3f} heading={heading:.1f}")
        field_pose = Pose2d(x, y, Rotation2d.fromDegrees(heading))
        self.container.drivetrain.reset_pose(field_pose)
        _log.info(f"_apply_selected_pose: odometry reset to ({x:.3f}, {y:.3f}, {heading:.1f} deg)")

    def robotPeriodic(self):
        """Called every 20ms regardless of mode."""
        CommandScheduler.getInstance().run()
        update_telemetry()
        self.container.match_setup.update()

    # --- Autonomous ---

    def autonomousInit(self):
        """Called when autonomous mode starts."""
        _log.info("autonomousInit: fired")
        self._apply_selected_pose()

        # Test override takes priority over the derived routine.
        test_factory = self.container.test_chooser.getSelected()
        if test_factory is not None:
            _log.info("autonomousInit: test override selected")
            self.auto_command = test_factory()
        else:
            alliance_name = self.container.match_setup.get_alliance()["name"]
            pose_name = self.container.match_setup.get_pose_name()
            _log.info(f"autonomousInit: deriving routine from alliance='{alliance_name}' pose='{pose_name}'")
            self.auto_command = self.container.auton_modes.get_auto_command(alliance_name, pose_name)

        _log.info(f"autonomousInit: scheduling {type(self.auto_command).__name__}")
        self.auto_command.schedule()
        _log.info("autonomousInit: done")

    def autonomousPeriodic(self):
        """Called every 20ms during autonomous."""
        if DEBUG["auto_sequence_logging"] and self.auto_command:
            self._auto_periodic_count += 1
            if self.auto_command.isFinished():
                _log.info(f"AUTO PERIODIC [{self._auto_periodic_count}]: auto command FINISHED")
            elif self._auto_periodic_count % 20 == 0:
                _log.info(f"AUTO PERIODIC [{self._auto_periodic_count}]: auto command running")

    def autonomousExit(self):
        """Called when autonomous mode ends."""
        if DEBUG["auto_sequence_logging"]:
            _log.info(f"AUTO EXIT: auto ended after {self._auto_periodic_count} cycles")
        if self.auto_command:
            self.auto_command.cancel()
        self._auto_periodic_count = 0

    # --- Teleop ---

    def teleopInit(self):
        """Called when teleop mode starts."""
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
