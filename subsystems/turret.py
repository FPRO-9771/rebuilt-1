"""
Turret subsystem.
Rotating turret powered by a KrakenX60 motor with soft position limits.
"""

from typing import Callable
from commands2 import SubsystemBase, Command

from hardware import create_motor
from constants import MOTOR_IDS, CON_TURRET


class Turret(SubsystemBase):
    """
    Rotating turret for aiming the shooter.
    Uses voltage control with software position limits.
    """

    def __init__(self):
        super().__init__()
        self.motor = create_motor(
            MOTOR_IDS["turret"],
            inverted=CON_TURRET["inverted"],
        )

    # --- Sensor reads (public) ---

    def get_position(self) -> float:
        """Get current turret position in rotations."""
        return self.motor.get_position()

    def get_velocity(self) -> float:
        """Get current turret velocity in rotations per second."""
        return self.motor.get_velocity()

    def is_at_position(self, target: float) -> bool:
        """Check if turret is within tolerance of target position."""
        return abs(self.get_position() - target) <= CON_TURRET["position_tolerance"]

    def is_within_limits(self) -> bool:
        """Check if turret is within soft limits."""
        pos = self.get_position()
        return CON_TURRET["min_position"] <= pos <= CON_TURRET["max_position"]

    # --- Motor control (internal) ---

    def _set_voltage(self, volts: float) -> None:
        """Apply voltage with safety clamping and soft limit enforcement."""
        max_v = CON_TURRET["max_voltage"]
        clamped = max(-max_v, min(volts, max_v))

        # Enforce soft limits — block voltage that would push past limits
        pos = self.get_position()
        if pos >= CON_TURRET["max_position"] and clamped > 0:
            clamped = 0
        elif pos <= CON_TURRET["min_position"] and clamped < 0:
            clamped = 0

        self.motor.set_voltage(clamped)

    def _stop(self) -> None:
        """Stop the turret."""
        self.motor.stop()

    # --- Commands (public) ---

    def manual(self, speed_supplier: Callable[[], float]) -> Command:
        """
        Returns command for joystick control.

        Args:
            speed_supplier: Lambda returning -1.0 to 1.0 from joystick
        """
        return self._ManualCommand(self, speed_supplier)

    def hold_position(self) -> Command:
        """Returns command that holds current position via closed-loop."""
        return self._HoldPositionCommand(self)

    def stop_command(self) -> Command:
        """Returns command to stop the turret."""
        return self.runOnce(lambda: self._stop())

    # --- Inner command classes ---

    class _ManualCommand(Command):
        """Joystick control of turret."""

        def __init__(self, turret: "Turret", speed_supplier: Callable[[], float]):
            super().__init__()
            self.turret = turret
            self.speed_supplier = speed_supplier
            self.addRequirements(turret)

        def execute(self):
            speed = self.speed_supplier()
            voltage = speed * CON_TURRET["max_voltage"]
            self.turret._set_voltage(voltage)

        def end(self, interrupted: bool):
            self.turret._stop()

    class _HoldPositionCommand(Command):
        """Hold turret at current position."""

        def __init__(self, turret: "Turret"):
            super().__init__()
            self.turret = turret
            self._target = 0.0
            self.addRequirements(turret)

        def initialize(self):
            self._target = self.turret.get_position()

        def execute(self):
            self.turret.motor.set_position(self._target)

        def end(self, interrupted: bool):
            self.turret._stop()
