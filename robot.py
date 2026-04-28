"""
Robot lifecycle management.
Subclasses TimedRobot and delegates to RobotContainer.
"""

import wpilib
from commands2 import CommandScheduler
from robot_container import RobotContainer
from telemetry import update_telemetry
from constants.debug import DEBUG
from utils.logger import get_logger, reset_auton_timer

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

    def robotPeriodic(self):
        """Called every 20ms regardless of mode."""
        CommandScheduler.getInstance().run()
        update_telemetry()
        self.container.match_setup.update()

    # --- Autonomous ---

    def _apply_selected_pose(self):
        """Seed drivetrain odometry from the selected routine's first waypoint.

        PathPlanner owns the starting pose. We read it via
        auton_modes.get_starting_pose() (which handles alliance flipping) and
        reset the drivetrain before the auto command is scheduled. In the
        normal (override=None) case, PathPlanner's own resetOdom fires ~20ms
        later with the same pose, so this is a no-op on behavior. In the
        'Do Nothing' override case, this is the only thing that sets the
        pose, so Field2d shows the selected starting spot instead of (0,0).
        """
        pose_name = self.container.match_setup.get_pose_name()
        start = self.container.auton_modes.get_starting_pose(pose_name)
        if start is None:
            _log.warning(
                f"_apply_selected_pose: no starting pose for '{pose_name}' -- leaving odometry alone"
            )
            return
        self.container.drivetrain.reset_pose(start)
        _log.info(
            f"_apply_selected_pose: seeded pose -> "
            f"x={start.X():.3f} y={start.Y():.3f} heading={start.rotation().degrees():.1f} deg"
        )

    def autonomousInit(self):
        """Called when autonomous mode starts."""
        reset_auton_timer()
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
        _log.info(f"autonomousInit: scheduled={self.auto_command.isScheduled()} finished={self.auto_command.isFinished()}")
        _log.info("autonomousInit: done")

    def autonomousPeriodic(self):
        """Called every 20ms during autonomous."""
        if DEBUG["auto_sequence_logging"] and self.auto_command:
            self._auto_periodic_count += 1
            if not self.auto_command.isScheduled() and self._auto_periodic_count <= 5:
                _log.warning(f"AUTO PERIODIC [{self._auto_periodic_count}]: command NOT scheduled after {self._auto_periodic_count} cycles!")
        self.container.power_monitor.sample("auto")

    def autonomousExit(self):
        """Called when autonomous mode ends."""
        if DEBUG["auto_sequence_logging"]:
            scheduled = self.auto_command.isScheduled() if self.auto_command else None
            finished = self.auto_command.isFinished() if self.auto_command else None
            _log.info(f"AUTO EXIT: after {self._auto_periodic_count} cycles, scheduled={scheduled} finished={finished}")
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
        self.container.power_monitor.sample("teleop")

    def teleopExit(self):
        """Called when teleop mode ends."""
        pass

    # --- Disabled ---

    def disabledInit(self):
        """Called when robot is disabled."""
        self.container.power_monitor.dump()

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
