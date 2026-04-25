"""
Intake hopper agitate command.

Oscillates the intake arm between down_position and a point
`up_offset_rotations` above it, with a short brake dwell at each end,
while spinning the intake roller at a slow voltage. The arm motion
shakes Fuel in the hopper to clear jams.

Intended use: run during stationary auto-shooting, NOT while the driver
is actively intaking (which is the normal RunIntake command). Wiring
decisions (when to schedule this) live with the controller bindings --
this command just knows how to agitate.

End behavior: on end(), both motors are stopped (brake mode). The
intake's default command (position guard) takes over on the next
scheduler tick.

Requires: intake, intake_spinner.

Tuning: see constants/intake_hopper_agitate.py.
"""

from commands2 import Command

from subsystems.intake import Intake
from subsystems.intake_spinner import IntakeSpinner
from constants import CON_INTAKE, CON_INTAKE_HOPPER_AGITATE
from utils.logger import get_logger

_log = get_logger("intake_hopper_agitate")


class IntakeHopperAgitate(Command):
    """Oscillate intake arm up/down while spinning rollers slowly to agitate Fuel."""

    def __init__(self, intake: Intake, spinner: IntakeSpinner):
        super().__init__()
        self.intake = intake
        self.spinner = spinner
        self._down_target = 0.0
        self._up_target = 0.0
        self._direction = "up"      # "up" or "down"
        self._dwell_remaining = 0
        self.addRequirements(intake, spinner)

    def initialize(self):
        self._down_target = CON_INTAKE["down_position"]
        self._up_target = (
            self._down_target + CON_INTAKE_HOPPER_AGITATE["up_offset_rotations"]
        )
        # Pick initial direction based on where the arm is, so we don't
        # briefly drive further into a hard stop on startup.
        pos = self.intake.get_position()
        midpoint = (self._up_target + self._down_target) / 2.0
        self._direction = "down" if pos > midpoint else "up"
        self._dwell_remaining = 0
        _log.info(
            f"IntakeHopperAgitate ENABLED: oscillating "
            f"{self._down_target:.3f} <-> {self._up_target:.3f} "
            f"starting {self._direction} from pos={pos:.3f}"
        )

    def execute(self):
        self.spinner._set_voltage(CON_INTAKE_HOPPER_AGITATE["spin_voltage"])

        # Brake dwell between reversals.
        if self._dwell_remaining > 0:
            self.intake._set_voltage(0)
            self._dwell_remaining -= 1
            return

        pos = self.intake.get_position()
        tol = CON_INTAKE_HOPPER_AGITATE["position_tolerance"]
        v = CON_INTAKE_HOPPER_AGITATE["arm_voltage"]
        dwell = CON_INTAKE_HOPPER_AGITATE["dwell_cycles"]

        if self._direction == "up":
            self.intake._set_voltage(+v)
            if pos >= self._up_target - tol:
                self._direction = "down"
                self._dwell_remaining = dwell
                _log.debug(f"agitate reached up at pos={pos:.3f}, dwelling")
        else:
            self.intake._set_voltage(-v)
            if pos <= self._down_target + tol:
                self._direction = "up"
                self._dwell_remaining = dwell
                _log.debug(f"agitate reached down at pos={pos:.3f}, dwelling")

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool):
        self.spinner._stop()
        self.intake._stop()
        _log.info(
            f"IntakeHopperAgitate DISABLED (interrupted={interrupted})"
        )
