"""
Hardware abstraction layer.
Provides factory functions that return real or mock hardware based on mode.
"""

from .motor_controller import MotorController, TalonFXController, MockMotorController
from .motor_controller_fxs import TalonFXSController

_use_mock_hardware = False


def set_mock_mode(enabled: bool) -> None:
    """Enable mock hardware for testing."""
    global _use_mock_hardware
    _use_mock_hardware = enabled


def is_mock_mode() -> bool:
    """Check if mock mode is enabled."""
    return _use_mock_hardware


def create_motor(can_id: int, inverted: bool = False) -> MotorController:
    """
    Factory function - returns real or mock TalonFX motor based on mode.

    Args:
        can_id: CAN bus ID for the motor
        inverted: Whether to invert motor direction

    Returns:
        MotorController instance (real TalonFX or mock)
    """
    if _use_mock_hardware:
        return MockMotorController(can_id, inverted)
    return TalonFXController(can_id, inverted)


def create_motor_fxs(can_id: int, inverted: bool = False) -> MotorController:
    """
    Factory function - returns real or mock TalonFXS motor based on mode.

    Args:
        can_id: CAN bus ID for the motor
        inverted: Whether to invert motor direction

    Returns:
        MotorController instance (real TalonFXS or mock)
    """
    if _use_mock_hardware:
        return MockMotorController(can_id, inverted)
    return TalonFXSController(can_id, inverted)
