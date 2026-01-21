"""
Autonomous mode selector.
Creates a SmartDashboard/Shuffleboard chooser for selecting auto routines.

IMPORTANT: Store factory lambdas in chooser, not command instances.
Commands carry state and must be created fresh each auto period.

TODO: Implement when AutonModes is ready.
"""

from wpilib import SmartDashboard, SendableChooser

# from .auton_modes import AutonModes


def create_auton_chooser(auton_modes) -> SendableChooser:
    """
    Create and publish the autonomous mode chooser.

    Args:
        auton_modes: AutonModes instance with subsystems injected

    Returns:
        SendableChooser that returns factory lambdas (not command instances!)
    """
    chooser = SendableChooser()

    # IMPORTANT: Store lambdas that CREATE commands, not the commands themselves
    chooser.setDefaultOption("Do Nothing", lambda: auton_modes.do_nothing())

    # TODO: Add more options as auto routines are implemented
    # chooser.addOption("Simple Exit", lambda: auton_modes.simple_exit())
    # chooser.addOption("Score Blue Left", lambda: auton_modes.simple_score("blue_left"))
    # chooser.addOption("Score Blue Center", lambda: auton_modes.simple_score("blue_center"))

    SmartDashboard.putData("Auto Mode", chooser)
    return chooser
