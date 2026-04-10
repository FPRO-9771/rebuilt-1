"""
Tests for RunIntake command (spin wheels + hold arm in place).
"""

from subsystems.intake import Intake
from subsystems.intake_spinner import IntakeSpinner
from commands.run_intake import RunIntake
from tests.conftest import TEST_CON_INTAKE, TEST_CON_INTAKE_SPINNER


# --- Helpers ---

def _run_cycles(cmd, n, spinner=None, velocity=None):
    """Run n execute cycles, optionally setting spinner velocity each cycle."""
    for _ in range(n):
        if spinner is not None and velocity is not None:
            spinner.motor.simulate_velocity(velocity)
        cmd.execute()


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
    """Correction voltage never exceeds spin_hold_max_voltage."""
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

    max_v = TEST_CON_INTAKE["spin_hold_max_voltage"]
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


# --- Un-jam tests ---


def test_no_unjam_during_spinup():
    """Stall detection does not trigger during the spinup grace period."""
    intake = Intake()
    spinner = IntakeSpinner()
    cmd = RunIntake(intake, spinner)
    cmd.initialize()

    # Run through spinup cycles with zero velocity -- should NOT trigger unjam
    spinup = TEST_CON_INTAKE_SPINNER["unjam_spinup_cycles"]
    _run_cycles(cmd, spinup, spinner, velocity=0.0)

    # Should still be sending normal spin voltage (not reversed)
    assert cmd._unjamming is False
    assert spinner.motor.get_last_voltage() == TEST_CON_INTAKE_SPINNER["spin_voltage"]


def test_unjam_triggers_after_spinup():
    """Stall detected after spinup grace period triggers unjam reversal."""
    intake = Intake()
    spinner = IntakeSpinner()
    cmd = RunIntake(intake, spinner)
    cmd.initialize()

    spinup = TEST_CON_INTAKE_SPINNER["unjam_spinup_cycles"]
    threshold = TEST_CON_INTAKE_SPINNER["unjam_velocity_threshold"]

    # Get past spinup with normal velocity
    _run_cycles(cmd, spinup, spinner, velocity=threshold + 1.0)

    # Now stall -- velocity drops below threshold
    spinner.motor.simulate_velocity(0.0)
    cmd.execute()  # detects stall, sets _unjamming (normal voltage already sent this cycle)

    assert cmd._unjamming is True

    # Next cycle applies the reverse voltage
    cmd.execute()
    expected_v = -(TEST_CON_INTAKE_SPINNER["spin_voltage"]
                   * TEST_CON_INTAKE_SPINNER["unjam_speed_multiplier"])
    assert spinner.motor.get_last_voltage() == expected_v


def test_unjam_resumes_after_duration():
    """After unjam_duration_cycles, command resumes normal spin."""
    intake = Intake()
    spinner = IntakeSpinner()
    cmd = RunIntake(intake, spinner)
    cmd.initialize()

    spinup = TEST_CON_INTAKE_SPINNER["unjam_spinup_cycles"]
    duration = TEST_CON_INTAKE_SPINNER["unjam_duration_cycles"]

    # Get past spinup, then trigger unjam
    _run_cycles(cmd, spinup, spinner, velocity=5.0)
    spinner.motor.simulate_velocity(0.0)
    cmd.execute()  # triggers unjam
    assert cmd._unjamming is True

    # Run through unjam duration (last cycle clears flag but still sends reverse)
    _run_cycles(cmd, duration, spinner, velocity=0.0)
    assert cmd._unjamming is False

    # Next cycle resumes normal spin
    spinner.motor.simulate_velocity(5.0)
    cmd.execute()
    assert spinner.motor.get_last_voltage() == TEST_CON_INTAKE_SPINNER["spin_voltage"]


def test_unjam_resets_spinup_grace():
    """After unjam completes, spinup grace period resets to avoid re-triggering."""
    intake = Intake()
    spinner = IntakeSpinner()
    cmd = RunIntake(intake, spinner)
    cmd.initialize()

    spinup = TEST_CON_INTAKE_SPINNER["unjam_spinup_cycles"]
    duration = TEST_CON_INTAKE_SPINNER["unjam_duration_cycles"]

    # Get past spinup, trigger and complete unjam
    _run_cycles(cmd, spinup, spinner, velocity=5.0)
    spinner.motor.simulate_velocity(0.0)
    cmd.execute()  # triggers unjam
    _run_cycles(cmd, duration, spinner, velocity=0.0)  # completes unjam

    # exec_count was reset -- so we're back in spinup grace, zero velocity should NOT re-trigger
    assert cmd._unjamming is False
    spinner.motor.simulate_velocity(0.0)
    cmd.execute()
    assert cmd._unjamming is False


def test_no_unjam_when_velocity_above_threshold():
    """Normal operation -- spinner at speed should never trigger unjam."""
    intake = Intake()
    spinner = IntakeSpinner()
    cmd = RunIntake(intake, spinner)
    cmd.initialize()

    # Run well past spinup with healthy velocity
    spinup = TEST_CON_INTAKE_SPINNER["unjam_spinup_cycles"]
    _run_cycles(cmd, spinup + 20, spinner, velocity=5.0)

    assert cmd._unjamming is False
    assert spinner.motor.get_last_voltage() == TEST_CON_INTAKE_SPINNER["spin_voltage"]
