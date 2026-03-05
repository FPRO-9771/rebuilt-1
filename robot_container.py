"""
Central hub - creates all subsystems and wires them together.
This is where controllers are bound to commands.
"""

from constants import CON_ROBOT
from controls.game_controller import GameController
from generated.tuner_constants import TunerConstants
# from subsystems.conveyor import Conveyor  # NOT WIRED YET
from subsystems.turret import Turret
from subsystems.launcher import Launcher
from subsystems.hood import Hood
from controls import configure_driver, configure_operator
from handlers import get_vision_providers
from telemetry import setup_telemetry


class RobotContainer:
    """
    Creates subsystems, commands, and binds controls.
    """

    def __init__(self):
        # --- Subsystems ---
        self.drivetrain = TunerConstants.create_drivetrain()
        # self.conveyor = Conveyor()  # NOT WIRED YET
        self.turret = Turret()
        self.launcher = Launcher()
        self.hood = Hood()

        # --- Vision ---
        self.vision = get_vision_providers()

        # --- Controllers ---
        use_ps4 = CON_ROBOT["use_ps4"]
        self.driver = GameController(CON_ROBOT["driver_controller_port"], use_ps4)
        self.operator = GameController(CON_ROBOT["operator_controller_port"], use_ps4)

        # --- Autonomous chooser ---
        # TODO: Set up auto mode selector

        # --- Configure button bindings ---
        self._configure_bindings()

        # --- Telemetry ---
        setup_telemetry(None, self.turret, self.launcher,
                        self.hood, self.vision)

    def _configure_bindings(self):
        """Wire controller inputs to commands."""

        # --- Driver Controls ---
        configure_driver(self.driver, self.drivetrain)

        # --- Operator Controls ---
        configure_operator(
            self.operator, None, self.turret,
            self.launcher, self.hood, self.vision["shooter"],
        )
