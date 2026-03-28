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
from subsystems.h_feed import HFeed
from subsystems.v_feed import VFeed
from subsystems.intake import Intake
from subsystems.intake_spinner import IntakeSpinner
from controls import configure_driver, configure_operator
# from handlers import get_vision_providers  # COMMENTED OUT -- not using vision providers (2026-03-19)
from match_setup import MatchSetup
from telemetry import setup_telemetry
from autonomous.named_commands import register_named_commands
from autonomous.auton_modes import AutonModes
from autonomous.auton_mode_selector import create_test_chooser
from utils.logger import get_logger

_log = get_logger("robot_container")


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
        self.h_feed = HFeed()
        self.v_feed = VFeed()
        self.intake = Intake()
        self.intake_spinner = IntakeSpinner()

        # --- Vision ---
        # Vision providers commented out -- not using vision-based aiming.
        # Limelight stream and odometry resets work without VisionProvider.
        # self.vision = get_vision_providers()

        # --- Controllers ---
        use_ps4 = CON_ROBOT["use_ps4"]
        self.driver = GameController(CON_ROBOT["driver_controller_port"], use_ps4)
        self.operator = GameController(CON_ROBOT["operator_controller_port"], use_ps4)

        # --- Autonomous context supplier (needed by ShooterStart named command) ---
        def _get_robot_velocity():
            dt_state = self.drivetrain.get_state()
            return (dt_state.speeds.vx, dt_state.speeds.vy)

        _context_supplier = _make_shoot_context_supplier(
            self.drivetrain, self.match_setup.get_alliance, _get_robot_velocity
        )

        # --- PathPlanner named commands ---
        # Register all named commands BEFORE loading .auto files.
        # See autonomous/named_commands.py for the full list.
        register_named_commands(
            intake=self.intake,
            intake_spinner=self.intake_spinner,
            launcher=self.launcher,
            h_feed=self.h_feed,
            v_feed=self.v_feed,
            turret=self.turret,
            context_supplier=_context_supplier,
            drivetrain=self.drivetrain,
        )

        self.auton_modes = AutonModes()
        self.test_chooser = create_test_chooser(self.auton_modes)

        # --- Configure button bindings ---
        self._configure_bindings()

        # --- Telemetry ---
        setup_telemetry(None, self.turret, self.launcher,
                        {},  # vision providers disabled
                        self.h_feed, self.v_feed,
                        self.intake_spinner,
                        drivetrain=self.drivetrain,
                        alliance_supplier=self.match_setup.get_alliance)

    def _configure_bindings(self):
        """Wire controller inputs to commands."""

        # --- Driver Controls ---
        configure_driver(self.driver, self.drivetrain,
                         intake=self.intake,
                         intake_spinner=self.intake_spinner)

        # --- Operator Controls ---
        configure_operator(
            self.operator, None, self.turret,
            self.launcher, None,  # vision provider disabled
            self.match_setup, self.h_feed, self.v_feed,
            drivetrain=self.drivetrain,
        )
