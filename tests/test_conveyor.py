"""
Tests for conveyor subsystem.
"""

from subsystems.conveyor import Conveyor
from tests.conftest import TEST_CON_CONVEYOR


def test_conveyor_voltage_clamping():
    """Verify voltage is clamped to max."""
    conveyor = Conveyor()

    conveyor._set_voltage(100)
    assert conveyor.motor.get_last_voltage() == TEST_CON_CONVEYOR["max_voltage"]

    conveyor._set_voltage(-100)
    assert conveyor.motor.get_last_voltage() == -TEST_CON_CONVEYOR["max_voltage"]


def test_conveyor_stop():
    """Verify stop sets voltage to zero."""
    conveyor = Conveyor()
    max_v = TEST_CON_CONVEYOR["max_voltage"]

    conveyor._set_voltage(max_v * 0.5)
    assert conveyor.motor.get_last_voltage() == max_v * 0.5

    conveyor._stop()
    assert conveyor.motor.get_last_voltage() == 0


def test_manual_command_scales_input():
    """Verify manual command scales joystick to voltage."""
    conveyor = Conveyor()

    cmd = conveyor.manual(lambda: 0.5)
    cmd.initialize()
    cmd.execute()

    expected_voltage = 0.5 * TEST_CON_CONVEYOR["max_voltage"]
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
    intake_v = TEST_CON_CONVEYOR["intake_voltage"]

    cmd = conveyor.run_at_voltage(intake_v)
    cmd.initialize()
    cmd.execute()

    assert conveyor.motor.get_last_voltage() == intake_v

    cmd.end(False)
    assert conveyor.motor.get_last_voltage() == 0
