"""
Autonomous mode selector.
Creates a SmartDashboard/Shuffleboard chooser for selecting auto routines.

IMPORTANT: Store factory lambdas in chooser, not command instances.
Commands carry state and must be created fresh each auto period.
"""

from wpilib import SmartDashboard, SendableChooser

from .auton_modes import AutonModes


def create_auton_chooser(auton_modes: AutonModes) -> SendableChooser:
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

    chooser.addOption("Blue Center", lambda: auton_modes.blue_center())
    chooser.addOption("Blue Left",   lambda: auton_modes.blue_left())
    chooser.addOption("Blue Right",  lambda: auton_modes.blue_right())
    chooser.addOption("Red Center",  lambda: auton_modes.red_center())
    chooser.addOption("Red Left",    lambda: auton_modes.red_left())
    chooser.addOption("Red Right",   lambda: auton_modes.red_right())

    # TODO: Remove before competition
    chooser.addOption("Mini Test",   lambda: auton_modes.mini_test())

    SmartDashboard.putData("Auto Mode", chooser)
    return chooser
