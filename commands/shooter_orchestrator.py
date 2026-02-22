"""
Shooter orchestrator command.
Ties vision + turret + launcher + hood together for automated shooting.
"""

from typing import Optional
from commands2 import Command

from handlers.vision import VisionProvider
from subsystems.turret import Turret
from subsystems.launcher import Launcher
from subsystems.hood import Hood
from subsystems.shooter_lookup import get_shooter_settings
from constants import CON_SHOOTER


class ShooterOrchestrator(Command):
    """
    Automated shooter command — aims turret, spins launcher, adjusts hood.

    Queries vision each cycle for target data, computes aiming and shot
    parameters, and commands all three subsystems. Holds last aim on
    momentary target loss.

    Never auto-finishes — runs until canceled by operator.
    """

    def __init__(
        self,
        turret: Turret,
        launcher: Launcher,
        hood: Hood,
        vision: VisionProvider,
        target_tag_id: Optional[int] = None,
    ):
        super().__init__()
        self.turret = turret
        self.launcher = launcher
        self.hood = hood
        self.vision = vision
        self.target_tag_id = target_tag_id

        # State
        self._last_tx = 0.0
        self._last_distance = 2.0  # Default mid-range
        self._target_visible = False

        self.addRequirements(turret, launcher, hood)

    def initialize(self):
        self._last_tx = 0.0
        self._last_distance = 2.0
        self._target_visible = False

    def execute(self):
        # 1. Query vision for target
        target = self.vision.get_target(self.target_tag_id)

        # 2. Update state from target (or hold last values)
        if target is not None:
            self._last_tx = target.tx
            self._last_distance = target.distance
            self._target_visible = True
        else:
            self._target_visible = False

        # 3. Aim turret: proportional control from tx offset
        turret_voltage = self._last_tx * CON_SHOOTER["turret_p_gain"]
        self.turret._set_voltage(turret_voltage)

        # 4. Look up launcher and hood settings from distance
        rps, hood_pos = get_shooter_settings(self._last_distance)

        # 5. Command launcher velocity
        self.launcher._set_velocity(rps)

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
        self.turret._stop()
        self.launcher._stop()
        self.hood._stop()
