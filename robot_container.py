"""
Central hub - creates all subsystems and wires them together.
This is where controllers are bound to commands.
"""

from commands2.button import CommandXboxController, Trigger

from constants import CON_ROBOT, CON_CONVEYOR
from subsystems.conveyor import Conveyor


class RobotContainer:
    """
    Creates subsystems, commands, and binds controls.
    """

    def __init__(self):
        # --- Subsystems ---
        self.conveyor = Conveyor()

        # TODO: Add more subsystems as they're built
        # self.drivetrain = Drivetrain()
        # self.arm = Arm()

        # --- Controllers ---
        self.driver = CommandXboxController(CON_ROBOT["driver_controller_port"])
        self.operator = CommandXboxController(CON_ROBOT["operator_controller_port"])

        # --- Autonomous chooser ---
        # TODO: Set up auto mode selector
        # self.auto_chooser = create_auton_chooser(...)

        # --- Configure button bindings ---
        self._configure_bindings()

    def _configure_bindings(self):
        """Wire controller inputs to commands."""

        # --- Operator Controls ---

        # Conveyor manual control with right joystick Y-axis
        # Uses a Trigger to check if joystick is past deadband
        deadband = CON_ROBOT["joystick_deadband"]

        Trigger(lambda: abs(self.operator.getRightY()) > deadband).whileTrue(
            self.conveyor.manual(lambda: -self.operator.getRightY())
        )

        # Alternative: Button-based control
        # A button = intake (forward)
        # self.operator.a().whileTrue(self.conveyor.run_at_voltage(CON_CONVEYOR["intake_voltage"]))

        # B button = outtake (reverse)
        # self.operator.b().whileTrue(self.conveyor.run_at_voltage(CON_CONVEYOR["outtake_voltage"]))

        # --- Driver Controls ---
        # TODO: Add drivetrain controls
        # self.drivetrain.setDefaultCommand(
        #     self.drivetrain.drive_with_joystick(
        #         lambda: -self.driver.getLeftY(),
        #         lambda: -self.driver.getLeftX(),
        #         lambda: -self.driver.getRightX(),
        #     )
        # )
