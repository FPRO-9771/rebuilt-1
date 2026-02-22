"""
Launcher subsystem.
Flywheel launcher powered by a KrakenX60 motor with closed-loop velocity control.
"""

from commands2 import SubsystemBase, Command

from hardware import create_motor
from constants import MOTOR_IDS, CON_LAUNCHER


class Launcher(SubsystemBase):
    """
    Flywheel launcher for shooting game pieces.
    Uses closed-loop velocity control to maintain consistent shot speed.
    """

    def __init__(self):
        super().__init__()
        self.motor = create_motor(
            MOTOR_IDS["launcher"],
            inverted=CON_LAUNCHER["inverted"],
        )

    # --- Sensor reads (public) ---

    def get_velocity(self) -> float:
        """Get current flywheel velocity in rotations per second."""
        return self.motor.get_velocity()

    def is_at_speed(self, target_rps: float) -> bool:
        """Check if flywheel is within tolerance of target speed."""
        return abs(self.get_velocity() - target_rps) <= CON_LAUNCHER["velocity_tolerance"]

    # --- Motor control (internal) ---

    def _set_velocity(self, rps: float) -> None:
        """Set flywheel to target velocity using closed-loop control."""
        self.motor.set_velocity(rps)

    def _set_voltage(self, volts: float) -> None:
        """Apply voltage with safety clamping (open-loop)."""
        max_v = CON_LAUNCHER["max_voltage"]
        clamped = max(-max_v, min(volts, max_v))
        self.motor.set_voltage(clamped)

    def _stop(self) -> None:
        """Stop the launcher."""
        self.motor.stop()

    # --- Commands (public) ---

    def spin_up(self, target_rps: float) -> Command:
        """
        Returns command to spin flywheel to target speed.
        Never finishes — holds speed until canceled.

        Args:
            target_rps: Target velocity in rotations per second
        """
        return self._SpinUpCommand(self, target_rps)

    def run_at_voltage(self, voltage: float) -> Command:
        """
        Returns command to run at fixed voltage (open-loop).

        Args:
            voltage: Voltage to apply
        """
        return self._RunAtVoltageCommand(self, voltage)

    def stop_command(self) -> Command:
        """Returns command to stop the launcher."""
        return self.runOnce(lambda: self._stop())

    # --- Inner command classes ---

    class _SpinUpCommand(Command):
        """Closed-loop velocity control — never auto-finishes."""

        def __init__(self, launcher: "Launcher", target_rps: float):
            super().__init__()
            self.launcher = launcher
            self.target_rps = target_rps
            self.addRequirements(launcher)

        def execute(self):
            self.launcher._set_velocity(self.target_rps)

        def isFinished(self) -> bool:
            return False

        def end(self, interrupted: bool):
            self.launcher._stop()

    class _RunAtVoltageCommand(Command):
        """Open-loop voltage control."""

        def __init__(self, launcher: "Launcher", voltage: float):
            super().__init__()
            self.launcher = launcher
            self.voltage = voltage
            self.addRequirements(launcher)

        def execute(self):
            self.launcher._set_voltage(self.voltage)

        def end(self, interrupted: bool):
            self.launcher._stop()
