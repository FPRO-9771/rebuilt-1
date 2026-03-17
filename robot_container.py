"""
Central hub - creates all subsystems and wires them together.
This is where controllers are bound to commands.
"""

from constants import CON_ROBOT
from controls.game_controller import GameController
from controls.operator_controls import _make_shoot_context_supplier
from generated.tuner_constants import TunerConstants
# from subsystems.conveyor import Conveyor  # NOT WIRED YET
# --- Turret motor swap: uncomment ONE of these two lines ---
# from subsystems.turret import Turret          # Kraken X60 (TalonFX)
from subsystems.turret_minion import TurretMinion as Turret  # Minion (TalonFXS)
from subsystems.launcher import Launcher
from subsystems.hood import Hood
from subsystems.h_feed import HFeed
from subsystems.v_feed import VFeed
from subsystems.intake import Intake
from subsystems.intake_spinner import IntakeSpinner
from controls import configure_driver, configure_operator
from handlers import get_vision_providers
from match_setup import MatchSetup
from telemetry import setup_telemetry
from autonomous.auton_modes import AutonModes
from autonomous.auton_mode_selector import create_auton_chooser


class RobotContainer:
    """
    Creates subsystems, commands, and binds controls.
    """

    def __init__(self):
        # --- Match setup (SmartDashboard choosers) ---
        self.match_setup = MatchSetup()

        # --- Subsystems ---
        self.drivetrain = TunerConstants.create_drivetrain()
        # self.conveyor = Conveyor()  # NOT WIRED YET
        self.turret = Turret()
        self.launcher = Launcher()
        self.hood = Hood()
        self.h_feed = HFeed()
        self.v_feed = VFeed()
        self.intake = Intake()
        self.intake_spinner = IntakeSpinner()

        # --- Vision ---
        self.vision = get_vision_providers()

        # --- Controllers ---
        use_ps4 = CON_ROBOT["use_ps4"]
        self.driver = GameController(CON_ROBOT["driver_controller_port"], use_ps4)
        self.operator = GameController(CON_ROBOT["operator_controller_port"], use_ps4)

        # --- Autonomous chooser ---
        _context_supplier = _make_shoot_context_supplier(
            self.drivetrain, self.match_setup.get_alliance
        )
        _auton_modes = AutonModes(
            drivetrain=self.drivetrain,
            turret=self.turret,
            launcher=self.launcher,
            hood=self.hood,
            h_feed=self.h_feed,
            v_feed=self.v_feed,
            context_supplier=_context_supplier,
            intake=self.intake,
            intake_spinner=self.intake_spinner,
        )
        self.auto_chooser = create_auton_chooser(_auton_modes)

        # --- Configure button bindings ---
        self._configure_bindings()

        # --- Telemetry ---
        setup_telemetry(None, self.turret, self.launcher,
                        self.hood, self.vision,
                        self.h_feed, self.v_feed,
                        self.intake_spinner,
                        drivetrain=self.drivetrain,
                        alliance_supplier=self.match_setup.get_alliance)

    def _configure_bindings(self):
        """Wire controller inputs to commands."""

        # --- Driver Controls ---
        configure_driver(self.driver, self.drivetrain)

        # --- Operator Controls ---
        configure_operator(
            self.operator, None, self.turret,
            self.launcher, self.hood, self.vision["shooter"],
            self.match_setup, self.h_feed, self.v_feed,
            self.intake, self.intake_spinner,
            drivetrain=self.drivetrain,
        )
