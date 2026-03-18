"""
Tests for RunIntake command (spin wheels + hold arm in place).
"""

from subsystems.intake import Intake
from subsystems.intake_spinner import IntakeSpinner
from commands.run_intake import RunIntake
from tests.conftest import TEST_CON_INTAKE, TEST_CON_INTAKE_SPINNER


def test_initialize_snapshots_current_position():
    """Hold target is captured from arm position at command start."""
    intake = Intake()
    spinner = IntakeSpinner()
    intake.motor_left.simulate_position(-1.0)
    intake.motor_right.simulate_position(-1.0)

    cmd = RunIntake(intake, spinner)
    cmd.initialize()

    assert cmd._hold_target == -1.0


def test_spinner_runs_at_spin_voltage():
    """Spinner motor receives the configured spin voltage every cycle."""
    intake = Intake()
    spinner = IntakeSpinner()
    cmd = RunIntake(intake, spinner)

    cmd.initialize()
    cmd.execute()

    assert spinner.motor.get_last_voltage() == TEST_CON_INTAKE_SPINNER["spin_voltage"]


def test_hold_no_correction_within_deadband():
    """Arm gets 0V when drift is within the deadband."""
    intake = Intake()
    spinner = IntakeSpinner()
    cmd = RunIntake(intake, spinner)

    # Start at -1.0, drift slightly
    intake.motor_left.simulate_position(-1.0)
    intake.motor_right.simulate_position(-1.0)
    cmd.initialize()

    # Simulate small drift within deadband
    half_deadband = TEST_CON_INTAKE["hold_deadband"] / 2
    intake.motor_left.simulate_position(-1.0 + half_deadband)
    intake.motor_right.simulate_position(-1.0 + half_deadband)
    cmd.execute()

    assert intake.motor_left.get_last_voltage() == 0
    assert intake.motor_right.get_last_voltage() == 0


def test_hold_corrects_when_drift_exceeds_deadband():
    """Arm gets correction voltage when drift exceeds the deadband."""
    intake = Intake()
    spinner = IntakeSpinner()
    cmd = RunIntake(intake, spinner)

    intake.motor_left.simulate_position(-1.0)
    intake.motor_right.simulate_position(-1.0)
    cmd.initialize()

    # Simulate drift beyond deadband (arm drifted up from -1.0 toward 0)
    drift = TEST_CON_INTAKE["hold_deadband"] * 2
    intake.motor_left.simulate_position(-1.0 + drift)
    intake.motor_right.simulate_position(-1.0 + drift)
    cmd.execute()

    voltage = intake.motor_left.get_last_voltage()
    # Error is negative (target below current), so correction should be negative
    assert voltage < 0


def test_hold_correction_clamped_to_max():
    """Correction voltage never exceeds hold_max_voltage."""
    intake = Intake()
    spinner = IntakeSpinner()
    cmd = RunIntake(intake, spinner)

    intake.motor_left.simulate_position(-1.0)
    intake.motor_right.simulate_position(-1.0)
    cmd.initialize()

    # Simulate huge drift that would exceed max voltage
    intake.motor_left.simulate_position(0.0)
    intake.motor_right.simulate_position(0.0)
    cmd.execute()

    max_v = TEST_CON_INTAKE["hold_max_voltage"]
    voltage = intake.motor_left.get_last_voltage()
    assert abs(voltage) <= max_v


def test_end_stops_both_subsystems():
    """Both spinner and arm motors stop when command ends."""
    intake = Intake()
    spinner = IntakeSpinner()
    cmd = RunIntake(intake, spinner)

    cmd.initialize()
    cmd.execute()
    cmd.end(interrupted=False)

    assert spinner.motor.get_last_voltage() == 0
    assert intake.motor_left.get_last_voltage() == 0
    assert intake.motor_right.get_last_voltage() == 0


def test_end_on_interrupt_stops_both():
    """Both subsystems stop even when command is interrupted."""
    intake = Intake()
    spinner = IntakeSpinner()
    cmd = RunIntake(intake, spinner)

    cmd.initialize()
    cmd.execute()
    cmd.end(interrupted=True)

    assert spinner.motor.get_last_voltage() == 0
    assert intake.motor_left.get_last_voltage() == 0
    assert intake.motor_right.get_last_voltage() == 0


def test_is_not_finished():
    """Command never auto-finishes (hold until released)."""
    intake = Intake()
    spinner = IntakeSpinner()
    cmd = RunIntake(intake, spinner)

    cmd.initialize()
    assert cmd.isFinished() is False
