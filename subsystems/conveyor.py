"""
Conveyor belt subsystem.
Powered by a KrakenX60 motor for moving game pieces.
"""

from typing import Callable
from commands2 import SubsystemBase, Command

from hardware import create_motor
from constants import MOTOR_IDS, CON_CONVEYOR


class Conveyor(SubsystemBase):
    """
    Conveyor belt for transporting game pieces.
    Uses voltage control for simple forward/reverse operation.
    """

    def __init__(self):
        super().__init__()
        self.motor = create_motor(MOTOR_IDS["conveyor"])

    # --- Sensor reads (public) ---

    def get_velocity(self) -> float:
        """Get current belt velocity in rotations per second."""
        return self.motor.get_velocity()

    # --- Motor control (internal) ---

    def _set_voltage(self, volts: float) -> None:
        """Apply voltage with safety clamping."""
        max_v = CON_CONVEYOR["max_voltage"]
        clamped = max(-max_v, min(volts, max_v))
        self.motor.set_voltage(clamped)

    def _stop(self) -> None:
        """Stop the conveyor."""
        self.motor.stop()

    # --- Commands (public) ---

    def manual(self, speed_supplier: Callable[[], float]) -> Command:
        """
        Returns command for joystick control.

        Args:
            speed_supplier: Lambda returning -1.0 to 1.0 from joystick
        """
        return self._ManualCommand(self, speed_supplier)

    def run_at_voltage(self, voltage: float) -> Command:
        """
        Returns command to run at fixed voltage.

        Args:
            voltage: Voltage to apply (positive = forward, negative = reverse)
        """
        return self._RunAtVoltageCommand(self, voltage)

    def stop_command(self) -> Command:
        """Returns command to stop the conveyor."""
        return self.runOnce(lambda: self._stop())

    # --- Inner command classes ---

    class _ManualCommand(Command):
        """Joystick control of conveyor."""

        def __init__(self, conveyor: "Conveyor", speed_supplier: Callable[[], float]):
            super().__init__()
            self.conveyor = conveyor
            self.speed_supplier = speed_supplier
            self.addRequirements(conveyor)

        def execute(self):
            speed = self.speed_supplier()
            voltage = speed * CON_CONVEYOR["max_voltage"]
            self.conveyor._set_voltage(voltage)

        def end(self, interrupted: bool):
            self.conveyor._stop()

    class _RunAtVoltageCommand(Command):
        """Run conveyor at fixed voltage."""

        def __init__(self, conveyor: "Conveyor", voltage: float):
            super().__init__()
            self.conveyor = conveyor
            self.voltage = voltage
            self.addRequirements(conveyor)

        def execute(self):
            self.conveyor._set_voltage(self.voltage)

        def end(self, interrupted: bool):
            self.conveyor._stop()
