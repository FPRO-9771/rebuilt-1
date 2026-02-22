"""
Motor controller abstraction.
Defines interface and implementations for TalonFX/KrakenX60 and mocks.

Note: KrakenX60 motors use the TalonFX class from Phoenix 6 library.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class MotorController(ABC):
    """Abstract interface for motor controllers."""

    @abstractmethod
    def set_voltage(self, volts: float) -> None:
        """Apply voltage to motor (open-loop control)."""
        pass

    @abstractmethod
    def set_velocity(self, velocity: float, feedforward: float = 0) -> None:
        """Run at velocity using closed-loop control (rotations per second)."""
        pass

    @abstractmethod
    def set_position(self, position: float, feedforward: float = 0) -> None:
        """Move to position using closed-loop control."""
        pass

    @abstractmethod
    def get_position(self) -> float:
        """Get current position in rotations."""
        pass

    @abstractmethod
    def get_velocity(self) -> float:
        """Get current velocity in rotations per second."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the motor."""
        pass


class TalonFXController(MotorController):
    """
    Real TalonFX/KrakenX60 implementation using Phoenix 6.
    """

    def __init__(self, can_id: int, inverted: bool = False):
        from phoenix6.hardware import TalonFX
        from phoenix6.configs import TalonFXConfiguration
        from phoenix6.signals import InvertedValue

        self.motor = TalonFX(can_id)
        self._last_voltage = 0.0

        # Configure inversion if needed
        if inverted:
            config = TalonFXConfiguration()
            config.motor_output.inverted = InvertedValue.CLOCKWISE_POSITIVE
            self.motor.configurator.apply(config)

    def set_voltage(self, volts: float) -> None:
        from phoenix6.controls import VoltageOut

        self._last_voltage = volts
        self.motor.set_control(VoltageOut(volts))

    def set_velocity(self, velocity: float, feedforward: float = 0) -> None:
        from phoenix6.controls import VelocityVoltage

        self.motor.set_control(
            VelocityVoltage(velocity).with_feed_forward(feedforward)
        )

    def set_position(self, position: float, feedforward: float = 0) -> None:
        from phoenix6.controls import PositionVoltage

        self.motor.set_control(
            PositionVoltage(position).with_feed_forward(feedforward)
        )

    def get_position(self) -> float:
        return self.motor.get_position().value

    def get_velocity(self) -> float:
        return self.motor.get_velocity().value

    def stop(self) -> None:
        self.set_voltage(0)


class MockMotorController(MotorController):
    """
    Mock implementation for testing.
    Tracks commands and allows simulation of sensor values.
    """

    def __init__(self, can_id: int, inverted: bool = False):
        self.can_id = can_id
        self.inverted = inverted
        self._position = 0.0
        self._velocity = 0.0
        self._voltage = 0.0
        self.command_history: List[Dict[str, Any]] = []

    def set_voltage(self, volts: float) -> None:
        self._voltage = volts
        self.command_history.append({"type": "voltage", "value": volts})

    def set_velocity(self, velocity: float, feedforward: float = 0) -> None:
        self._velocity = velocity
        self.command_history.append({
            "type": "velocity",
            "value": velocity,
            "ff": feedforward
        })

    def set_position(self, position: float, feedforward: float = 0) -> None:
        self._position = position  # Instant move for basic testing
        self.command_history.append({
            "type": "position",
            "value": position,
            "ff": feedforward
        })

    def get_position(self) -> float:
        return self._position

    def get_velocity(self) -> float:
        return self._velocity

    def stop(self) -> None:
        self.set_voltage(0)

    # --- Test helpers ---

    def simulate_position(self, position: float) -> None:
        """Set position for testing sensor reads."""
        self._position = position

    def simulate_velocity(self, velocity: float) -> None:
        """Set velocity for testing sensor reads."""
        self._velocity = velocity

    def get_last_voltage(self) -> float:
        """Get last commanded voltage for test assertions."""
        return self._voltage

    def clear_history(self) -> None:
        """Clear command history."""
        self.command_history.clear()
