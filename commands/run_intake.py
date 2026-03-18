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
        self._exec_count = 0
        self.addRequirements(intake, spinner)

    def initialize(self):
        self._hold_target = self.intake.get_position()
        self._exec_count = 0
        _log.info(f"RunIntake ENABLED -- holding at {self._hold_target:.4f}")

    def execute(self):
        self._exec_count += 1

        # Spin the intake wheels
        spin_v = CON_INTAKE_SPINNER["spin_voltage"]
        self.spinner._set_voltage(spin_v)

        # Log first execute to confirm command is actually running
        if self._exec_count == 1:
            _log.debug(f"RunIntake execute #1: sending {spin_v:.1f}V to spinner")

        # Hold arm at snapshot position with soft P-control
        # Use higher voltage cap while spinner is active (reaction force pushes arm up)
        pos = self.intake.get_position()
        error = self._hold_target - pos
        if abs(error) < CON_INTAKE["hold_deadband"]:
            self.intake._set_voltage(0)
            hold_v = 0.0
        else:
            hold_kP = CON_INTAKE["hold_kP"]
            max_v = CON_INTAKE["spin_hold_max_voltage"]
            hold_v = max(-max_v, min(hold_kP * error, max_v))
            self.intake._set_voltage(hold_v)

        # Log hold state every 10 cycles (~5 Hz)
        if self._exec_count % 10 == 0:
            _log.debug(
                f"RunIntake hold: pos={pos:.3f} target={self._hold_target:.3f}"
                f" err={error:.3f} v={hold_v:.2f}V"
            )

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool):
        self.spinner._stop()
        self.intake._stop()
        _log.info(
            f"RunIntake DISABLED (interrupted={interrupted})"
            f" -- ran {self._exec_count} execute cycles"
        )
