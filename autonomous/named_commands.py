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
  CorrectOdometry   -- vision odometry correction using Limelight MegaTag1 (safe mid-path)
"""

from pathplannerlib.auto import NamedCommands
from pathplannerlib.events import EventTrigger
from commands2 import Command, ParallelCommandGroup

from commands.coordinate_aim import CoordinateAim
from commands.manual_shoot import ManualShoot
from commands.shoot_when_ready import ShootWhenReady
from constants import CON_INTAKE_SPINNER
from constants.shoot_hardware import CON_TURRET_MINION
from handlers.limelight_helpers import get_bot_pose_estimate_wpi_blue_megatag1
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
                            h_feed, v_feed, turret, context_supplier,
                            drivetrain):
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
        drivetrain:       CommandSwerveDrivetrain (for odometry reset)
    """
    # --- Intake ---
    _logged("IntakeDown", intake.go_down())
    _logged("IntakeUp", intake.go_up())
    _logged("IntakeStart",
        intake_spinner.run_at_voltage(CON_INTAKE_SPINNER["spin_voltage"]))
    _logged("IntakeStop",
        intake_spinner.runOnce(lambda: intake_spinner._stop()))

    # Trigger bindings for all intake event markers.
    # PathPlanner fires EventTrigger("<name>") for any marker with command=null.
    # Using trigger bindings means the GUI can freely edit paths without
    # re-linking commands -- the binding lives here in code, not in the path file.
    #
    # onTrue  -- fires once on the rising edge; command runs to completion.
    #            Correct for point events (arm moves, instant stops).
    # whileTrue -- holds True while in a zone, cancels on exit.
    #              Correct for zoned IntakeStart (spinner runs only in the zone).
    EventTrigger("IntakeDown").onTrue(intake.go_down())
    EventTrigger("IntakeUp").onTrue(intake.go_up())
    EventTrigger("IntakeStop").onTrue(
        intake_spinner.runOnce(lambda: intake_spinner._stop())
    )
    EventTrigger("IntakeStart").whileTrue(
        intake_spinner.run_at_voltage(CON_INTAKE_SPINNER["spin_voltage"])
    )

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

    # --- Odometry reset via Limelight MegaTag1 ---
    # MegaTag1 uses pure AprilTag geometry (no gyro fusion) and is more
    # accurate for one-shot resets than MegaTag2.
    #
    # Two ways to use this in PathPlanner GUI:
    #   - Point marker: fires once when the robot reaches that waypoint.
    #   - Zone marker:  fires every loop while the robot is inside the zone
    #                   (e.g. the full length of the Trench crossing).
    #                   Use a zone for continuous correction on the return path.
    # --- Odometry correction via Limelight MegaTag1 ---
    # Uses add_vision_measurement() instead of reset_pose() so the pose
    # estimator blends the correction in smoothly (Kalman filter). A hard
    # reset_pose() mid-path causes a sudden pose jump that makes the
    # PathPlanner controller command a large correction -- jerky motion.
    #
    # Two ways to use "CorrectOdometry" in PathPlanner GUI:
    #   - Point marker: feeds one measurement at that waypoint.
    #   - Zone marker:  feeds measurements every loop while inside the zone
    #                   (e.g. the full length of the Trench crossing).
    def _correct_odom_from_vision():
        estimate = get_bot_pose_estimate_wpi_blue_megatag1("limelight-shooter")
        if estimate and estimate.tag_count >= 1:
            drivetrain.add_vision_measurement(
                estimate.pose, estimate.timestamp_seconds
            )
            _log.debug(
                f"CorrectOdometry: ({estimate.pose.X():.2f}, "
                f"{estimate.pose.Y():.2f}) {estimate.tag_count} tag(s)"
            )
        else:
            _log.debug("CorrectOdometry: no tags visible, skipped")

    # Point marker: feeds one measurement (runOnce finishes immediately).
    _logged("CorrectOdometry", drivetrain.runOnce(_correct_odom_from_vision))

    # Zone marker: feeds measurements every loop while inside the zone.
    # PathPlanner cancels it automatically when the robot exits the zone.
    EventTrigger("CorrectOdometry").whileTrue(
        drivetrain.run(_correct_odom_from_vision)
    )

    _log.info("all named commands registered")
