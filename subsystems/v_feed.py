"""
Vertical feed subsystem.
Powered by a KrakenX60 motor for moving Fuel vertically.
"""

from typing import Callable
from commands2 import SubsystemBase, Command

from hardware import create_motor
from constants import MOTOR_IDS, CON_V_FEED


class VFeed(SubsystemBase):
    """Vertical feed for transporting Fuel. Uses voltage control."""

    def __init__(self):
        super().__init__()
        self.motor = create_motor(MOTOR_IDS["v_feed"])

    # --- Sensor reads (public) ---

    def get_velocity(self) -> float:
        """Get current feed velocity in rotations per second."""
        return self.motor.get_velocity()

    # --- Motor control (internal) ---

    def _set_voltage(self, volts: float) -> None:
        """Apply voltage with safety clamping."""
        max_v = CON_V_FEED["max_voltage"]
        clamped = max(-max_v, min(volts, max_v))
        self.motor.set_voltage(clamped)

    def _stop(self) -> None:
        """Stop the feed."""
        self.motor.stop()

    # --- Commands (public) ---

    def manual(self, speed_supplier: Callable[[], float]) -> Command:
        """Returns command for joystick control."""
        return self._ManualCommand(self, speed_supplier)

    def run_at_voltage(self, voltage: float) -> Command:
        """Returns command to run at fixed voltage."""
        return self._RunAtVoltageCommand(self, voltage)

    def stop_command(self) -> Command:
        """Returns command to stop the feed."""
        return self.runOnce(lambda: self._stop())

    # --- Inner command classes ---

    class _ManualCommand(Command):
        """Joystick control of vertical feed."""

        def __init__(self, feed: "VFeed", speed_supplier: Callable[[], float]):
            super().__init__()
            self.feed = feed
            self.speed_supplier = speed_supplier
            self.addRequirements(feed)

        def execute(self):
            speed = self.speed_supplier()
            voltage = speed * CON_V_FEED["max_voltage"]
            self.feed._set_voltage(voltage)

        def end(self, interrupted: bool):
            self.feed._stop()

    class _RunAtVoltageCommand(Command):
        """Run vertical feed at fixed voltage."""

        def __init__(self, feed: "VFeed", voltage: float):
            super().__init__()
            self.feed = feed
            self.voltage = voltage
            self.addRequirements(feed)

        def execute(self):
            self.feed._set_voltage(self.voltage)

        def end(self, interrupted: bool):
            self.feed._stop()
