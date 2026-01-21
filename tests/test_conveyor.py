"""
Tests for conveyor subsystem.
"""

import pytest
from subsystems.conveyor import Conveyor
from constants import CON_CONVEYOR


def test_conveyor_voltage_clamping():
    """Verify voltage is clamped to max."""
    conveyor = Conveyor()

    # Try to set voltage way over max
    conveyor._set_voltage(100)
    assert conveyor.motor.get_last_voltage() == CON_CONVEYOR["max_voltage"]

    # Try negative over max
    conveyor._set_voltage(-100)
    assert conveyor.motor.get_last_voltage() == -CON_CONVEYOR["max_voltage"]


def test_conveyor_stop():
    """Verify stop sets voltage to zero."""
    conveyor = Conveyor()

    conveyor._set_voltage(5.0)
    assert conveyor.motor.get_last_voltage() == 5.0

    conveyor._stop()
    assert conveyor.motor.get_last_voltage() == 0


def test_manual_command_scales_input():
    """Verify manual command scales joystick to voltage."""
    conveyor = Conveyor()

    # Simulate joystick at 50%
    cmd = conveyor.manual(lambda: 0.5)
    cmd.initialize()
    cmd.execute()

    expected_voltage = 0.5 * CON_CONVEYOR["max_voltage"]
    assert conveyor.motor.get_last_voltage() == expected_voltage


def test_manual_command_stops_on_end():
    """Verify manual command stops motor when ended."""
    conveyor = Conveyor()

    cmd = conveyor.manual(lambda: 1.0)
    cmd.initialize()
    cmd.execute()

    assert conveyor.motor.get_last_voltage() != 0

    cmd.end(False)
    assert conveyor.motor.get_last_voltage() == 0


def test_run_at_voltage_command():
    """Verify run_at_voltage applies correct voltage."""
    conveyor = Conveyor()

    cmd = conveyor.run_at_voltage(CON_CONVEYOR["intake_voltage"])
    cmd.initialize()
    cmd.execute()

    assert conveyor.motor.get_last_voltage() == CON_CONVEYOR["intake_voltage"]

    cmd.end(False)
    assert conveyor.motor.get_last_voltage() == 0
