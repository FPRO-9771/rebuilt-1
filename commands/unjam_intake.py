"""
Unjam-intake command -- reverse the intake spinner briefly to clear a jam.
Bound to a driver button for manual unjam on demand.

Uses the same unjam constants as the auto-unjam in RunIntake:
  unjam_speed_multiplier -- reverse voltage = spin_voltage * multiplier
  unjam_duration_cycles  -- how many 20ms cycles to reverse
"""

from commands2 import Command

from subsystems.intake_spinner import IntakeSpinner
from constants import CON_INTAKE_SPINNER
from utils.logger import get_logger

_log = get_logger("unjam_intake")


class UnjamIntake(Command):
    """Reverse the intake spinner briefly to clear a jam."""

    def __init__(self, spinner: IntakeSpinner):
        super().__init__()
        self.spinner = spinner
        self._counter = 0
        self._total = 0
        self.addRequirements(spinner)

    def initialize(self):
        self._total = CON_INTAKE_SPINNER["unjam_duration_cycles"]
        self._counter = 0
        _log.info(f"UnjamIntake ENABLED -- reversing for {self._total} cycles")

    def execute(self):
        self._counter += 1
        spin_v = CON_INTAKE_SPINNER["spin_voltage"]
        unjam_v = -(spin_v * CON_INTAKE_SPINNER["unjam_speed_multiplier"])
        self.spinner._set_voltage(unjam_v)

    def isFinished(self) -> bool:
        return self._counter >= self._total

    def end(self, interrupted: bool):
        self.spinner._stop()
        _log.info(
            f"UnjamIntake DISABLED (interrupted={interrupted})"
            f" -- ran {self._counter} cycles"
        )
