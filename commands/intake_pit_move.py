"""
Pit-mode manual jog for the intake arm.

Mechanical locks on the intake arm prevent hand-raising it in the pit, so
the crew needs a way to inch the arm up or down using motor power without
relying on position targets (position zeros are reset when the robot is
power-cycled, so closed-loop moves to up_position are unsafe).

Voltages come from CON_INTAKE["pit_up_voltage"] / ["pit_down_voltage"] and
are intentionally low so the arm creeps.

Bound in operator_controls.py to: Start held + right stick Y outside deadband.
"""

from commands2 import Command

from subsystems.intake import Intake
from constants import CON_INTAKE
from utils.logger import get_logger

_log = get_logger("intake_pit_move")


class IntakePitMove(Command):
    """Jog the intake arm at low voltage based on a stick Y supplier.

    Positive stick Y (down on most controllers) -> jog DOWN.
    Negative stick Y (up on most controllers)   -> jog UP.
    """

    def __init__(self, intake: Intake, stick_y_supplier,
                 deadband: float = 0.1):
        super().__init__()
        self.intake = intake
        self._stick_y = stick_y_supplier
        self._deadband = deadband
        self.addRequirements(intake)

    def initialize(self):
        _log.warning("Pit jog ENABLED -- arm moving at low voltage")

    def execute(self):
        y = self._stick_y()
        if y < -self._deadband:
            volts = CON_INTAKE["pit_up_voltage"]
        elif y > self._deadband:
            volts = CON_INTAKE["pit_down_voltage"]
        else:
            volts = 0.0
        self.intake._set_voltage(volts)

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool):
        self.intake._stop()
        _log.warning(f"Pit jog DISABLED (interrupted={interrupted})")
