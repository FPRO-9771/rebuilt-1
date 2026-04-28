"""
Motor controller interface.
Defines the contract that all motor controller implementations must follow.

Note: KrakenX60 motors use the TalonFX class from Phoenix 6 library.
"""

from abc import ABC, abstractmethod


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
    def zero_position(self) -> None:
        """Set current position as zero."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the motor."""
        pass

    def get_supply_current(self) -> float:
        """Return supply current draw in amps. Default 0.0 for controllers that
        do not implement it (e.g. mock). Reads the cached Phoenix 6 signal in
        real implementations -- no CAN traffic at read time."""
        return 0.0

    def set_follower(self, leader_id: int, oppose_direction: bool = False) -> None:
        """Follow another motor controller. No-op by default."""
        pass
