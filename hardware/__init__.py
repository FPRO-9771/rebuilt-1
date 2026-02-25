"""
Hardware abstraction layer.
Provides a factory function that returns real or mock hardware based on
mode and wiring status.
"""

from typing import Dict, Any

from .motor_controller import MotorController
from .motor_controller_talon import TalonFXController
from .motor_controller_fxs import TalonFXSController
from .mock_motor_controller import MockMotorController

from utils.logger import get_logger

_log = get_logger("hardware")
_use_mock_hardware = False

# Maps config "type" strings to real hardware classes
_MOTOR_TYPES = {
    "talon_fx": TalonFXController,
    "talon_fxs": TalonFXSController,
}


def set_mock_mode(enabled: bool) -> None:
    """Enable mock hardware for testing."""
    global _use_mock_hardware
    _use_mock_hardware = enabled


def is_mock_mode() -> bool:
    """Check if mock mode is enabled."""
    return _use_mock_hardware


def create_motor(
    config: Dict[str, Any],
    inverted: bool = False,
    slot0: Dict[str, float] | None = None,
) -> MotorController:
    """
    Factory function - returns the right motor controller based on config.

    In mock/sim mode: always returns a MockMotorController.
    On real robot with wired=False: returns a MockMotorController (no-op).
    On real robot with wired=True: returns the real hardware class.

    Args:
        config: Entry from MOTOR_IDS, e.g. {"can_id": 30, "type": "talon_fx", "wired": True}
        inverted: Whether to invert motor direction
        slot0: Optional PID gains for closed-loop control, e.g. {"kP": 12.0, "kI": 0, "kD": 0}

    Returns:
        MotorController instance
    """
    can_id = config["can_id"]
    motor_type = config["type"]
    wired = config.get("wired", True)

    if _use_mock_hardware:
        motor = MockMotorController(can_id, inverted)
    elif not wired:
        _log.warning(f"Motor CAN {can_id} not wired - using no-op controller")
        motor = MockMotorController(can_id, inverted)
    else:
        cls = _MOTOR_TYPES.get(motor_type)
        if cls is None:
            raise ValueError(f"Unknown motor type '{motor_type}' for CAN {can_id}")
        motor = cls(can_id, inverted, slot0=slot0)

    motor.zero_position()
    _log.info(f"Motor CAN {can_id} ({motor_type}) position zeroed")
    return motor
