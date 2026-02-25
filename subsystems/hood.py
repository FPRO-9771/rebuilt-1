"""
Hood subsystem.
Adjustable hood powered by a WCP motor via TalonFXS for angle control.
"""

from commands2 import SubsystemBase, Command

from hardware import create_motor
from constants import MOTOR_IDS, CON_HOOD
from utils.logger import get_logger

_log = get_logger("hood")


class Hood(SubsystemBase):
    """
    Adjustable hood for controlling shot angle.
    Uses closed-loop position control with position limits.
    """

    def __init__(self):
        super().__init__()
        self.motor = create_motor(
            MOTOR_IDS["hood"],
            inverted=CON_HOOD["inverted"],
            slot0={
                "kP": CON_HOOD["slot0_kP"],
                "kI": CON_HOOD["slot0_kI"],
                "kD": CON_HOOD["slot0_kD"],
                "kS": CON_HOOD["slot0_kS"],
                "kV": CON_HOOD["slot0_kV"],
                "kA": CON_HOOD["slot0_kA"],
                "kG": CON_HOOD["slot0_kG"],
            },
        )

    # --- Sensor reads (public) ---

    def get_position(self) -> float:
        """Get current hood position in rotations."""
        return self.motor.get_position()

    def is_at_position(self, target: float) -> bool:
        """Check if hood is within tolerance of target position."""
        return abs(self.get_position() - target) <= CON_HOOD["position_tolerance"]

    # --- Motor control (internal) ---

    def _set_position(self, position: float) -> None:
        """Move hood to position, clamped to min/max limits."""
        clamped = max(CON_HOOD["min_position"], min(position, CON_HOOD["max_position"]))
        _log.debug(
            f"_set_position: requested={position:.4f} clamped={clamped:.4f} "
            f"current={self.get_position():.4f}"
        )
        self.motor.set_position(clamped)

    def _set_voltage(self, volts: float) -> None:
        """Apply voltage with safety clamping."""
        max_v = CON_HOOD["max_voltage"]
        clamped = max(-max_v, min(volts, max_v))
        _log.debug(f"_set_voltage: requested={volts:.3f} clamped={clamped:.3f}")
        self.motor.set_voltage(clamped)

    def _stop(self) -> None:
        """Stop the hood."""
        _log.debug("_stop called")
        self.motor.stop()

    # --- Commands (public) ---

    def go_to_position(self, position: float) -> Command:
        """
        Returns command to move hood to position.
        Never finishes — holds position until canceled.

        Args:
            position: Target position in rotations
        """
        return self._GoToPositionCommand(self, position)

    def stop_command(self) -> Command:
        """Returns command to stop the hood."""
        return self.runOnce(lambda: self._stop())

    # --- Inner command classes ---

    class _GoToPositionCommand(Command):
        """Hold hood at target position — never auto-finishes."""

        def __init__(self, hood: "Hood", position: float):
            super().__init__()
            self.hood = hood
            self.position = position
            self.addRequirements(hood)

        def execute(self):
            self.hood._set_position(self.position)

        def isFinished(self) -> bool:
            return False

        def end(self, interrupted: bool):
            self.hood._stop()
