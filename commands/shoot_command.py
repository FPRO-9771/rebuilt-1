"""
Shoot command -- hold Y to spin up and shoot when locked.
Pre-spins launcher and sets hood always; feeder engages only when locked.
"""

from commands2 import Command

from commands.auto_tracker import AutoTracker
from subsystems.launcher import Launcher
from subsystems.hood import Hood
from subsystems.shooter_lookup import get_shooter_settings
from utils.logger import get_logger

_log = get_logger("shoot_command")


class ShootCommand(Command):
    """
    Hold-to-shoot command. Requires launcher and hood (not turret).

    Always spins up launcher and sets hood from tracked distance.
    Engages feeder only when AutoTracker reports locked.
    """

    def __init__(
        self,
        tracker: AutoTracker,
        launcher: Launcher,
        hood: Hood,
    ):
        super().__init__()
        self.tracker = tracker
        self.launcher = launcher
        self.hood = hood
        self.addRequirements(launcher, hood)

    def initialize(self):
        _log.info("ShootCommand ENABLED")

    def execute(self):
        # Look up settings from tracker's current distance
        rps, hood_pos = get_shooter_settings(self.tracker.get_distance())

        # Always pre-spin launcher and set hood
        self.launcher._set_velocity(rps)
        self.hood._set_position(hood_pos)

        # Feeder gated on lock
        if self.tracker.is_locked():
            self._engage_feeder()
        else:
            self._disengage_feeder()

    def _engage_feeder(self):
        """Placeholder -- will command feeder subsystem when wired."""
        _log.debug("Feeder: ENGAGE (placeholder)")

    def _disengage_feeder(self):
        """Placeholder -- will stop feeder subsystem when wired."""
        _log.debug("Feeder: DISENGAGE (placeholder)")

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool):
        _log.info(f"ShootCommand DISABLED (interrupted={interrupted})")
        self.launcher._stop()
        self.hood._stop()
        self._disengage_feeder()
