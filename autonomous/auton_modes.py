"""
Autonomous mode compositions.
Each method returns a command that performs a complete auto routine.

TODO: Implement auto routines once drivetrain and mechanisms are built.

Example usage:
```
auton = AutonModes(drivetrain, arm, intake, vision)
simple_auto = auton.simple_score("blue_center")
simple_auto.schedule()
```
"""

from commands2 import Command, SequentialCommandGroup, WaitCommand


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

    def simple_exit(self) -> Command:
        """
        Drive forward to exit the starting zone.
        TODO: Implement when drivetrain is ready.
        """
        # return SequentialCommandGroup(
        #     self.drivetrain.drive_distance(2.0),
        # )
        return WaitCommand(15.0)

    def simple_score(self, position: str) -> Command:
        """
        Score preloaded piece and exit zone.
        TODO: Implement with actual mechanisms.

        Args:
            position: Starting position key (e.g., "blue_left")
        """
        # return SequentialCommandGroup(
        #     self.arm.go_to_position(CON_ARM["score_high"]),
        #     self.intake.outtake(),
        #     self.arm.go_to_position(CON_ARM["stow"]),
        #     self.drivetrain.follow_path(DRIVE_PATHS["exit_zone"]),
        # )
        return WaitCommand(15.0)
