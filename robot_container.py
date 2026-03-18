"""
Central hub - creates all subsystems and wires them together.
This is where controllers are bound to commands.
"""

from constants import CON_ROBOT, CON_INTAKE_SPINNER, CON_H_FEED, CON_V_FEED
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
from commands2 import ParallelCommandGroup
from pathplannerlib.auto import NamedCommands
from commands.auto_shoot import AutoShoot
from autonomous.auton_modes import AutonModes
from autonomous.auton_mode_selector import create_test_chooser


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

        # --- Autonomous context supplier (needed by ShooterStart named command) ---
        def _get_robot_velocity():
            dt_state = self.drivetrain.get_state()
            return (dt_state.speeds.vx, dt_state.speeds.vy)

        _context_supplier = _make_shoot_context_supplier(
            self.drivetrain, self.match_setup.get_alliance, _get_robot_velocity
        )

        # --- Named commands (for PathPlanner event markers) ---

        # Intake arm
        NamedCommands.registerCommand(
            "IntakeDown",
            self.intake.hold_down(),
        )
        NamedCommands.registerCommand(
            "IntakeUp",
            self.intake.go_up(),
        )

        # Intake spinner
        NamedCommands.registerCommand(
            "IntakeStart",
            self.intake_spinner.run_at_voltage(CON_INTAKE_SPINNER["spin_voltage"]),
        )
        NamedCommands.registerCommand(
            "IntakeStop",
            self.intake_spinner.runOnce(lambda: self.intake_spinner._stop()),
        )

        # Shooter (launcher + hood, distance-based speed)
        NamedCommands.registerCommand(
            "ShooterStart",
            AutoShoot(self.launcher, self.hood, context_supplier=_context_supplier),
        )
        NamedCommands.registerCommand(
            "ShooterStop",
            ParallelCommandGroup(
                self.launcher.runOnce(lambda: self.launcher._stop()),
                self.hood.runOnce(lambda: self.hood._stop()),
            ),
        )

        # Feeders
        NamedCommands.registerCommand(
            "FeedersStart",
            ParallelCommandGroup(
                self.h_feed.run_at_voltage(CON_H_FEED["feed_voltage"]),
                self.v_feed.run_at_voltage(CON_V_FEED["feed_voltage"]),
            ),
        )
        NamedCommands.registerCommand(
            "FeedersStop",
            ParallelCommandGroup(
                self.h_feed.runOnce(lambda: self.h_feed._stop()),
                self.v_feed.runOnce(lambda: self.v_feed._stop()),
            ),
        )
        self.auton_modes = AutonModes(
            drivetrain=self.drivetrain,
            turret=self.turret,
            launcher=self.launcher,
            hood=self.hood,
            h_feed=self.h_feed,
            v_feed=self.v_feed,
            context_supplier=_context_supplier,
        )
        self.test_chooser = create_test_chooser(self.auton_modes)

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
        configure_driver(self.driver, self.drivetrain,
                         intake=self.intake,
                         intake_spinner=self.intake_spinner)

        # --- Operator Controls ---
        configure_operator(
            self.operator, None, self.turret,
            self.launcher, self.hood, self.vision["shooter"],
            self.match_setup, self.h_feed, self.v_feed,
            drivetrain=self.drivetrain,
        )
