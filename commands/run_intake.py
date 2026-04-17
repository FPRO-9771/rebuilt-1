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

Un-jam (constants/intake_spinner.py):
  If the spinner velocity drops below unjam_velocity_threshold while
  running, the command reverses the spinner at unjam_speed_multiplier
  times the normal spin voltage for unjam_duration_cycles, then resumes.
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
        self._unjamming = False
        self._unjam_counter = 0
        self.addRequirements(intake, spinner)

    def initialize(self):
        self._hold_target = self.intake.get_position()
        self._exec_count = 0
        self._unjamming = False
        self._unjam_counter = 0
        _log.info(f"RunIntake ENABLED -- holding at {self._hold_target:.4f}")

    def execute(self):
        self._exec_count += 1

        # --- Spinner with un-jam state machine ---
        spin_v = CON_INTAKE_SPINNER["spin_voltage"]

        if self._unjamming:
            # Reverse at multiplied speed to clear jam
            unjam_v = -(spin_v * CON_INTAKE_SPINNER["unjam_speed_multiplier"])
            self.spinner._set_voltage(unjam_v)
            self._unjam_counter -= 1
            if self._unjam_counter <= 0:
                self._unjamming = False
                self._exec_count = 0  # Reset so spinup grace applies after resume
                _log.info("Spinner un-jam complete -- resuming")
        else:
            self.spinner._set_voltage(spin_v)
            # Check for stall after spinup grace period (if auto-unjam enabled)
            if CON_INTAKE_SPINNER["unjam_enabled"] and self._exec_count > CON_INTAKE_SPINNER["unjam_spinup_cycles"]:
                vel = self.spinner.get_velocity()
                if abs(vel) < CON_INTAKE_SPINNER["unjam_velocity_threshold"]:
                    self._unjamming = True
                    self._unjam_counter = CON_INTAKE_SPINNER["unjam_duration_cycles"]
                    _log.warning("Intake spinner stalled -- un-jamming")

        # Log first execute to confirm command is actually running
        if self._exec_count == 1:
            _log.debug(f"RunIntake execute #1: sending {spin_v:.1f}V to spinner")

        # Hold arm at snapshot position while spinner runs.
        # Arm is on hard stops at down position -- only push DOWN (negative voltage).
        if CON_INTAKE["down_hold_enabled"]:
            pos = self.intake.get_position()
            error = self._hold_target - pos
            if abs(error) >= CON_INTAKE["down_hold_deadband"] and error < 0:
                # Arm drifted up past deadband -- fight it back down
                hold_v = CON_INTAKE["down_hold_fight_voltage"]
            else:
                # Constant light hold pushing down
                hold_v = CON_INTAKE["down_hold_voltage"]
            self.intake._set_voltage(hold_v)
        else:
            hold_v = 0.0

        # Log hold state every 10 cycles (~5 Hz)
        if CON_INTAKE["down_hold_enabled"] and self._exec_count % 10 == 0:
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
