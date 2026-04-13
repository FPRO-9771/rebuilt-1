"""
Tests for IntakePitMove command (pit-mode low-voltage jog).
"""

from subsystems.intake import Intake
from commands.intake_pit_move import IntakePitMove
from tests.conftest import TEST_CON_INTAKE


def _make_cmd(stick_y_value):
    intake = Intake()
    cmd = IntakePitMove(intake, lambda: stick_y_value)
    cmd.initialize()
    return intake, cmd


def test_stick_up_applies_pit_up_voltage():
    """Negative stick Y (pushed up) drives the arm up at pit_up_voltage."""
    intake, cmd = _make_cmd(-1.0)
    cmd.execute()
    assert intake.motor_left.get_last_voltage() == TEST_CON_INTAKE["pit_up_voltage"]
    assert intake.motor_right.get_last_voltage() == TEST_CON_INTAKE["pit_up_voltage"]


def test_stick_down_applies_pit_down_voltage():
    """Positive stick Y (pulled down) drives the arm down at pit_down_voltage."""
    intake, cmd = _make_cmd(1.0)
    cmd.execute()
    assert intake.motor_left.get_last_voltage() == TEST_CON_INTAKE["pit_down_voltage"]
    assert intake.motor_right.get_last_voltage() == TEST_CON_INTAKE["pit_down_voltage"]


def test_stick_centered_applies_zero_voltage():
    """Stick inside deadband produces 0V -- holding Start alone does nothing."""
    intake, cmd = _make_cmd(0.0)
    cmd.execute()
    assert intake.motor_left.get_last_voltage() == 0.0
    assert intake.motor_right.get_last_voltage() == 0.0


def test_stick_inside_deadband_applies_zero_voltage():
    """Small stick drift inside the command deadband produces 0V."""
    intake, cmd = _make_cmd(0.05)
    cmd.execute()
    assert intake.motor_left.get_last_voltage() == 0.0


def test_end_stops_motors():
    """end() cuts motor power."""
    intake, cmd = _make_cmd(-1.0)
    cmd.execute()
    cmd.end(interrupted=False)
    assert intake.motor_left.get_last_voltage() == 0.0
    assert intake.motor_right.get_last_voltage() == 0.0


def test_requires_intake_subsystem():
    """Command must declare the intake requirement so it interrupts the position guard."""
    intake = Intake()
    cmd = IntakePitMove(intake, lambda: 0.0)
    assert intake in cmd.getRequirements()


def test_never_finishes():
    """Command runs whileTrue -- should not self-terminate."""
    _, cmd = _make_cmd(-1.0)
    assert cmd.isFinished() is False
