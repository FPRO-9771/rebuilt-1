"""
Test override chooser for autonomous.

Normally the auto routine is derived automatically from the Alliance and
Starting Pose choosers in MatchSetup. This chooser lets the team override
that and run a specific test routine instead.

REMOVE test entries before competition (or just leave override on "None").
IMPORTANT: Store factory lambdas in chooser, not command instances.
Commands carry state and must be created fresh each auto period.
"""

from wpilib import SmartDashboard, SendableChooser

from .auton_modes import AutonModes


def create_test_chooser(auton_modes: AutonModes) -> SendableChooser:
    """
    Create and publish the test override chooser.

    Default is None (no override -- derive routine from Alliance + Starting Pose).
    Add test paths here as needed; remove before competition.

    Returns:
        SendableChooser that returns a factory lambda or None.
    """
    chooser = SendableChooser()

    chooser.setDefaultOption("None", None)

    chooser.addOption("Do Nothing", lambda: auton_modes.do_nothing())

    # TODO: Remove before competition
    chooser.addOption("Mini Test", lambda: auton_modes.mini_test())

    SmartDashboard.putData("Auton Override", chooser)
    return chooser
