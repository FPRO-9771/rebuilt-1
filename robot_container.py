"""
Central hub - creates all subsystems and wires them together.
This is where controllers are bound to commands.
"""

from commands2.button import CommandXboxController

from constants import CON_ROBOT
from subsystems.conveyor import Conveyor
from subsystems.turret import Turret
from subsystems.launcher import Launcher
from subsystems.hood import Hood
from controls import configure_operator
from handlers import get_vision_provider
from telemetry import setup_telemetry


class RobotContainer:
    """
    Creates subsystems, commands, and binds controls.
    """

    def __init__(self):
        # --- Subsystems ---
        self.conveyor = Conveyor()
        self.turret = Turret()
        self.launcher = Launcher()
        self.hood = Hood()

        # --- Vision ---
        self.vision = get_vision_provider()

        # TODO: Add more subsystems as they're built
        # self.drivetrain = Drivetrain()

        # --- Controllers ---
        self.driver = CommandXboxController(CON_ROBOT["driver_controller_port"])
        self.operator = CommandXboxController(CON_ROBOT["operator_controller_port"])

        # --- Autonomous chooser ---
        # TODO: Set up auto mode selector
        # self.auto_chooser = create_auton_chooser(...)

        # --- Configure button bindings ---
        self._configure_bindings()

        # --- Telemetry ---
        setup_telemetry(self.conveyor, self.turret, self.launcher,
                        self.hood, self.vision)

    def _configure_bindings(self):
        """Wire controller inputs to commands."""

        # --- Operator Controls ---
        configure_operator(
            self.operator, self.conveyor, self.turret,
            self.launcher, self.hood, self.vision,
        )

        # --- Driver Controls ---
        # TODO: Add drivetrain controls
        # self.drivetrain.setDefaultCommand(
        #     self.drivetrain.drive_with_joystick(
        #         lambda: -self.driver.getLeftY(),
        #         lambda: -self.driver.getLeftX(),
        #         lambda: -self.driver.getRightX(),
        #     )
        # )
