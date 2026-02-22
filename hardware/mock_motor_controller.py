"""
Mock motor controller for testing.
Tracks commands and simulates sensor values without real hardware.
"""

from typing import List, Dict, Any

from .motor_controller import MotorController


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
