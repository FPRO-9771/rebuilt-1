"""
Intake lever arm subsystem.
Two motors (left and right) drive the intake up and down.
The right motor is inverted so both motors work together.
Uses closed-loop position control for go-to-position commands.
"""

from commands2 import SubsystemBase, Command

from hardware import create_motor
from constants import MOTOR_IDS, CON_INTAKE
from utils.logger import get_logger

_log = get_logger("intake")

_SLOT0 = {
    "kP": CON_INTAKE["slot0_kP"],
    "kI": CON_INTAKE["slot0_kI"],
    "kD": CON_INTAKE["slot0_kD"],
    "kS": CON_INTAKE["slot0_kS"],
    "kV": CON_INTAKE["slot0_kV"],
    "kA": CON_INTAKE["slot0_kA"],
    "kG": CON_INTAKE["slot0_kG"],
}


class Intake(SubsystemBase):
    """Intake lever arm with two motors spinning opposite directions."""

    def __init__(self):
        super().__init__()
        self.motor_left = create_motor(
            MOTOR_IDS["intake_left"],
            inverted=CON_INTAKE["inverted"],
            brake=True,
            slot0=_SLOT0,
        )
        self.motor_right = create_motor(
            MOTOR_IDS["intake_right"],
            inverted=not CON_INTAKE["inverted"],
            brake=True,
            slot0=_SLOT0,
        )

    # --- Sensor reads (public) ---

    def get_position(self) -> float:
        """Get current position in rotations (from left motor)."""
        return self.motor_left.get_position()

    def is_at_position(self, target: float) -> bool:
        """Check if intake is within tolerance of target position."""
        return abs(self.get_position() - target) <= CON_INTAKE["position_tolerance"]

    # --- Motor control (internal) ---

    def _set_position(self, position: float) -> None:
        """Move both motors to position, clamped to limits."""
        lo = min(CON_INTAKE["up_position"], CON_INTAKE["down_position"])
        hi = max(CON_INTAKE["up_position"], CON_INTAKE["down_position"])
        clamped = max(lo, min(position, hi))
        self.motor_left.set_position(clamped)
        self.motor_right.set_position(clamped)

    def _set_voltage(self, volts: float) -> None:
        """Apply voltage to both motors with safety clamping."""
        max_v = CON_INTAKE["max_voltage"]
        clamped = max(-max_v, min(volts, max_v))
        self.motor_left.set_voltage(clamped)
        self.motor_right.set_voltage(clamped)

    def _stop(self) -> None:
        """Stop both motors."""
        self.motor_left.stop()
        self.motor_right.stop()

    # --- Commands (public) ---

    def go_to_position(self, position: float) -> Command:
        """Returns command to hold intake at a position. Never auto-finishes."""
        return self._GoToPositionCommand(self, position)

    def go_up(self) -> Command:
        """Returns command to raise intake to fully up position."""
        return self.go_to_position(CON_INTAKE["up_position"])

    def go_down(self) -> Command:
        """Returns command to lower intake to fully down position."""
        return self.go_to_position(CON_INTAKE["down_position"])

    def stop_command(self) -> Command:
        """Returns command to stop the intake."""
        return self.runOnce(lambda: self._stop())

    # --- Inner command classes ---

    class _GoToPositionCommand(Command):
        """Hold intake at target position -- never auto-finishes."""

        def __init__(self, intake: "Intake", position: float):
            super().__init__()
            self.intake = intake
            self.position = position
            self.addRequirements(intake)

        def execute(self):
            self.intake._set_position(self.position)

        def isFinished(self) -> bool:
            return False

        def end(self, interrupted: bool):
            self.intake._stop()
