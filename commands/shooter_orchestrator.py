"""
Shooter orchestrator command.
Ties vision + turret + launcher + hood together for automated shooting.
"""

from commands2 import Command

from handlers.vision import VisionProvider
from subsystems.turret import Turret
from subsystems.launcher import Launcher
from subsystems.hood import Hood
from subsystems.shooter_lookup import get_shooter_settings
from constants import CON_SHOOTER
from utils.logger import get_logger

_log = get_logger("orchestrator")


class ShooterOrchestrator(Command):
    """
    Automated shooter command — aims turret, spins launcher, adjusts hood.

    Queries vision each cycle for target data, filters for scoring tags,
    applies per-tag offsets, and commands all three subsystems. Holds last
    aim on momentary target loss.

    Never auto-finishes — runs until canceled by operator.
    """

    def __init__(
        self,
        turret: Turret,
        launcher: Launcher,
        hood: Hood,
        vision: VisionProvider,
    ):
        super().__init__()
        self.turret = turret
        self.launcher = launcher
        self.hood = hood
        self.vision = vision
        self._target_tags = CON_SHOOTER["target_tags"]
        self._aim_sign = -1.0 if CON_SHOOTER["turret_aim_inverted"] else 1.0

        # State
        self._last_tx = 0.0
        self._prev_tx = 0.0  # Previous tx for derivative calculation
        self._last_distance = 2.0  # Default mid-range
        self._target_visible = False

        self.addRequirements(turret, launcher, hood)

    def initialize(self):
        self._last_tx = 0.0
        self._prev_tx = 0.0
        self._last_distance = 2.0
        self._target_visible = False
        _log.info("Orchestrator ENABLED")

    def execute(self):
        # 1. Query vision for closest visible tag
        target = self.vision.get_target()

        # 2. Filter: only use scoring tags that have offsets configured
        if target is not None and target.tag_id in self._target_tags:
            offsets = self._target_tags[target.tag_id]
            self._last_tx = target.tx + offsets["tx_offset"]
            self._last_distance = target.distance + offsets["distance_offset"]
            self._target_visible = True
        else:
            self._target_visible = False
            self._last_tx = 0.0  # Stop turret when target lost

        # 3. Aim turret: PD control from corrected tx
        p_term = self._last_tx * CON_SHOOTER["turret_p_gain"]
        d_term = (self._last_tx - self._prev_tx) * CON_SHOOTER["turret_d_gain"]
        self._prev_tx = self._last_tx

        turret_voltage = (p_term + d_term) * self._aim_sign
        max_auto_v = CON_SHOOTER["turret_max_auto_voltage"]
        turret_voltage = max(-max_auto_v, min(turret_voltage, max_auto_v))
        self.turret._set_voltage(turret_voltage)

        # 4. Look up launcher and hood settings from corrected distance
        rps, hood_pos = get_shooter_settings(self._last_distance)

        # 5. Command launcher velocity
        self.launcher._set_velocity(rps)

        # Debug: log key values every cycle
        tag_id = target.tag_id if target is not None else None
        raw_tx = target.tx if target is not None else None
        raw_dist = target.distance if target is not None else None
        _log.debug(
            f"tag={tag_id} tx={raw_tx} dist={raw_dist} "
            f"cmd_dist={self._last_distance:.2f} rps={rps:.1f} "
            f"hood={hood_pos:.4f} voltage={turret_voltage:.3f}"
        )

        # 6. Command hood position
        self.hood._set_position(hood_pos)

    def is_ready(self) -> bool:
        """Check if all components are aligned and ready to shoot."""
        turret_aligned = abs(self._last_tx) <= CON_SHOOTER["turret_alignment_tolerance"]

        rps, hood_pos = get_shooter_settings(self._last_distance)
        launcher_ready = self.launcher.is_at_speed(rps)
        hood_ready = self.hood.is_at_position(hood_pos)

        return (
            turret_aligned
            and launcher_ready
            and hood_ready
            and self._target_visible
        )

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool):
        _log.info(f"Orchestrator DISABLED (interrupted={interrupted})")
        self.turret._stop()
        self.launcher._stop()
        self.hood._stop()
