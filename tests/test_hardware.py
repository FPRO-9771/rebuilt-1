"""
Tests for hardware abstraction layer.
"""

from hardware import create_motor, create_motor_fxs
from hardware.mock_motor_controller import MockMotorController


def test_set_velocity_records_in_mock():
    """Verify set_velocity() records in command history."""
    motor = create_motor(99)

    motor.set_velocity(50.0)
    assert motor._velocity == 50.0
    assert len(motor.command_history) == 1
    assert motor.command_history[0] == {
        "type": "velocity",
        "value": 50.0,
        "ff": 0,
    }


def test_set_velocity_with_feedforward():
    """Verify set_velocity() records feedforward."""
    motor = create_motor(99)

    motor.set_velocity(30.0, feedforward=1.5)
    assert motor.command_history[0]["ff"] == 1.5


def test_create_motor_fxs_returns_mock():
    """Verify create_motor_fxs() returns mock in mock mode."""
    motor = create_motor_fxs(99)
    assert isinstance(motor, MockMotorController)


def test_create_motor_fxs_supports_inverted():
    """Verify create_motor_fxs() passes inverted flag."""
    motor = create_motor_fxs(99, inverted=True)
    assert isinstance(motor, MockMotorController)
    assert motor.inverted is True
