"""
Central hub - creates all subsystems and wires them together.
This is where controllers are bound to commands.
"""

from constants import CON_ROBOT
from controls.game_controller import GameController
# from subsystems.conveyor import Conveyor  # NOT WIRED YET
from subsystems.turret import Turret
from subsystems.launcher import Launcher
from subsystems.hood import Hood
from controls import configure_operator
from handlers import get_vision_providers
from telemetry import setup_telemetry


class RobotContainer:
    """
    Creates subsystems, commands, and binds controls.
    """

    def __init__(self):
        # --- Subsystems ---
        # self.conveyor = Conveyor()  # NOT WIRED YET
        self.turret = Turret()
        self.launcher = Launcher()
        self.hood = Hood()

        # --- Vision ---
        self.vision = get_vision_providers()

        # TODO: Add more subsystems as they're built
        # self.drivetrain = Drivetrain()

        # --- Controllers ---
        use_ps4 = CON_ROBOT["use_ps4"]
        self.driver = GameController(CON_ROBOT["driver_controller_port"], use_ps4)
        self.operator = GameController(CON_ROBOT["operator_controller_port"], use_ps4)

        # --- Autonomous chooser ---
        # TODO: Set up auto mode selector
        # self.auto_chooser = create_auton_chooser(...)

        # --- Configure button bindings ---
        self._configure_bindings()

        # --- Telemetry ---
        setup_telemetry(None, self.turret, self.launcher,
                        self.hood, self.vision)

    def _configure_bindings(self):
        """Wire controller inputs to commands."""

        # --- Operator Controls ---
        configure_operator(
            self.operator, None, self.turret,
            self.launcher, self.hood, self.vision["shooter"],
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
