"""
Run-intake command -- spin the intake wheels and hold the arm in place.
Used by driver controls and autonomous routines.

Tuning (constants/intake.py):
  hold_kP         -- how hard the arm fights drift (volts per rotation).
                     Arm bounces/oscillates? Lower this.
                     Arm drifts too much? Raise this.
  hold_max_voltage -- caps correction power. Keep low to protect gears.
                     Arm can't hold against balls? Raise this.
  hold_deadband   -- ignore drift smaller than this (rotations).
                     Arm buzzes/chatters? Raise this.
                     Arm feels sloppy? Lower this.
"""

from commands2 import Command

from subsystems.intake import Intake
from subsystems.intake_spinner import IntakeSpinner
from constants import CON_INTAKE, CON_INTAKE_SPINNER
from utils.logger import get_logger

_log = get_logger("run_intake")


class RunIntake(Command):
    """Spin intake wheels while holding the arm at its current position."""

    def __init__(self, intake: Intake, spinner: IntakeSpinner):
        super().__init__()
        self.intake = intake
        self.spinner = spinner
        self._hold_target = 0.0
        self.addRequirements(intake, spinner)

    def initialize(self):
        self._hold_target = self.intake.get_position()
        _log.info(f"RunIntake ENABLED -- holding at {self._hold_target:.4f}")

    def execute(self):
        # Spin the intake wheels
        self.spinner._set_voltage(CON_INTAKE_SPINNER["spin_voltage"])

        # Hold arm at snapshot position with soft P-control
        error = self._hold_target - self.intake.get_position()
        if abs(error) < CON_INTAKE["hold_deadband"]:
            self.intake._set_voltage(0)
        else:
            hold_kP = CON_INTAKE["hold_kP"]
            max_v = CON_INTAKE["hold_max_voltage"]
            volts = max(-max_v, min(hold_kP * error, max_v))
            self.intake._set_voltage(volts)

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool):
        self.spinner._stop()
        self.intake._stop()
        _log.info(f"RunIntake DISABLED (interrupted={interrupted})")
