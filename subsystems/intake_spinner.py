"""
Intake spinner subsystem.
Powered by a KrakenX60 motor that spins to pull Fuel into the robot.
"""

from commands2 import Subsystem, Command

from hardware import create_motor
from constants import MOTOR_IDS, CON_INTAKE_SPINNER


class IntakeSpinner(Subsystem):
    """Intake spinner for pulling Fuel into the robot. Uses voltage control."""

    def __init__(self):
        super().__init__()
        self.motor = create_motor(MOTOR_IDS["intake_spinner"])

    # --- Sensor reads (public) ---

    def get_velocity(self) -> float:
        """Get current spinner velocity in rotations per second."""
        return self.motor.get_velocity()

    # --- Motor control (internal) ---

    def _set_voltage(self, volts: float) -> None:
        """Apply voltage with safety clamping."""
        max_v = CON_INTAKE_SPINNER["max_voltage"]
        clamped = max(-max_v, min(volts, max_v))
        self.motor.set_voltage(clamped)

    def _stop(self) -> None:
        """Stop the spinner."""
        self.motor.stop()

    # --- Commands (public) ---

    def run_at_voltage(self, voltage: float) -> Command:
        """Returns command to run at fixed voltage."""
        return self._RunAtVoltageCommand(self, voltage)

    # --- Inner command classes ---

    class _RunAtVoltageCommand(Command):
        """Run intake spinner at fixed voltage."""

        def __init__(self, spinner: "IntakeSpinner", voltage: float):
            super().__init__()
            self.spinner = spinner
            self.voltage = voltage
            self.addRequirements(spinner)

        def execute(self):
            self.spinner._set_voltage(self.voltage)

        def end(self, interrupted: bool):
            self.spinner._stop()
