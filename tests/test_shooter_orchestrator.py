"""
Tests for shooter orchestrator command.
"""

from subsystems.turret import Turret
from subsystems.launcher import Launcher
from subsystems.hood import Hood
from subsystems.shooter_lookup import get_shooter_settings
from commands.shooter_orchestrator import ShooterOrchestrator
from handlers.mock_vision import MockVisionProvider
from tests.conftest import (
    TEST_CON_TURRET, TEST_CON_SHOOTER,
    TEST_TAG_PRIORITY, TEST_TAG_OFFSETS,
)

# Midpoint of soft limits -- always safe regardless of constant tuning
_MID_POS = (TEST_CON_TURRET["min_position"] + TEST_CON_TURRET["max_position"]) / 2


def _make_orchestrator():
    """Helper to create orchestrator with all dependencies."""
    turret = Turret()
    turret.motor.simulate_position(_MID_POS)
    launcher = Launcher()
    hood = Hood()
    vision = MockVisionProvider()
    cmd = ShooterOrchestrator(
        turret, launcher, hood, vision,
        tag_priority_supplier=lambda: TEST_TAG_PRIORITY,
        tag_offsets_supplier=lambda: TEST_TAG_OFFSETS,
    )
    return cmd, turret, launcher, hood, vision


def test_target_right_positive_turret_voltage():
    """Target to the right should produce positive turret voltage."""
    cmd, turret, launcher, hood, vision = _make_orchestrator()
    vision.simulate_target_right(tag_id=4, offset_degrees=10, distance=2.0)

    cmd.initialize()
    cmd.execute()

    raw_voltage = 10.0 * TEST_CON_SHOOTER["turret_p_gain"]
    max_auto_v = TEST_CON_SHOOTER["turret_max_auto_voltage"]
    expected_voltage = min(raw_voltage, max_auto_v)
    assert turret.motor.get_last_voltage() == expected_voltage


def test_target_left_negative_turret_voltage():
    """Target to the left should produce negative turret voltage."""
    cmd, turret, launcher, hood, vision = _make_orchestrator()
    vision.simulate_target_left(tag_id=4, offset_degrees=8, distance=2.0)

    cmd.initialize()
    cmd.execute()

    assert turret.motor.get_last_voltage() < 0


def test_correct_launcher_rps_from_distance():
    """Verify launcher gets correct RPS from distance table."""
    cmd, turret, launcher, hood, vision = _make_orchestrator()
    vision.simulate_target_centered(tag_id=4, distance=2.0)

    cmd.initialize()
    cmd.execute()

    expected_rps, _ = get_shooter_settings(2.0)
    assert launcher.motor._velocity == expected_rps


def test_correct_hood_position_from_distance():
    """Verify hood gets correct position from distance table."""
    cmd, turret, launcher, hood, vision = _make_orchestrator()
    vision.simulate_target_centered(tag_id=4, distance=3.0)

    cmd.initialize()
    cmd.execute()

    _, expected_hood = get_shooter_settings(3.0)
    assert hood.motor._position == expected_hood


def test_is_ready_when_all_aligned():
    """Verify is_ready returns True when all components are aligned."""
    cmd, turret, launcher, hood, vision = _make_orchestrator()
    vision.simulate_target_centered(tag_id=4, distance=2.0)

    cmd.initialize()
    cmd.execute()

    # Simulate subsystems reporting they're at target
    rps, hood_pos = get_shooter_settings(2.0)
    launcher.motor.simulate_velocity(rps)
    hood.motor.simulate_position(hood_pos)

    assert cmd.is_ready() is True


def test_is_ready_false_when_turret_not_aligned():
    """Verify is_ready False when turret is far from center."""
    cmd, turret, launcher, hood, vision = _make_orchestrator()
    vision.simulate_target_right(tag_id=4, offset_degrees=20, distance=2.0)

    cmd.initialize()
    cmd.execute()

    rps, hood_pos = get_shooter_settings(2.0)
    launcher.motor.simulate_velocity(rps)
    hood.motor.simulate_position(hood_pos)

    assert cmd.is_ready() is False


def test_is_ready_false_when_launcher_not_at_speed():
    """Verify is_ready False when launcher hasn't spun up."""
    cmd, turret, launcher, hood, vision = _make_orchestrator()
    vision.simulate_target_centered(tag_id=4, distance=2.0)

    cmd.initialize()
    cmd.execute()

    # Launcher not at speed
    launcher.motor.simulate_velocity(0)
    _, hood_pos = get_shooter_settings(2.0)
    hood.motor.simulate_position(hood_pos)

    assert cmd.is_ready() is False


def test_is_ready_false_when_target_lost():
    """Verify is_ready False when no target visible."""
    cmd, turret, launcher, hood, vision = _make_orchestrator()
    vision.simulate_no_target()

    cmd.initialize()
    cmd.execute()

    # Even if subsystems report ready, no target = not ready
    rps, hood_pos = get_shooter_settings(2.0)
    launcher.motor.simulate_velocity(rps)
    hood.motor.simulate_position(hood_pos)

    assert cmd.is_ready() is False


def test_stops_turret_on_target_loss():
    """Verify turret stops when target is lost."""
    cmd, turret, launcher, hood, vision = _make_orchestrator()

    # First: target visible to the right
    vision.simulate_target_right(tag_id=4, offset_degrees=10, distance=2.0)
    cmd.initialize()
    cmd.execute()

    assert turret.motor.get_last_voltage() > 0

    # Now: target disappears
    vision.simulate_no_target()
    cmd.execute()
    # D term fires on first loss cycle (tx jumped from 10 to 0)
    # Run a second cycle so D term also settles to zero
    cmd.execute()

    # Turret should stop (zero voltage) when target is lost
    assert turret.motor.get_last_voltage() == 0


def test_never_auto_finishes():
    """Verify orchestrator never auto-finishes."""
    cmd, turret, launcher, hood, vision = _make_orchestrator()
    vision.simulate_target_centered(tag_id=4)

    cmd.initialize()
    for _ in range(100):
        cmd.execute()
        assert cmd.isFinished() is False


def test_stops_all_on_end():
    """Verify all motors stop when command ends."""
    cmd, turret, launcher, hood, vision = _make_orchestrator()
    vision.simulate_target_right(tag_id=4, offset_degrees=10, distance=3.0)

    cmd.initialize()
    cmd.execute()

    # Motors should be active
    assert turret.motor.get_last_voltage() != 0

    # End the command
    cmd.end(False)

    assert turret.motor.get_last_voltage() == 0
    assert launcher.motor.get_last_voltage() == 0
    assert hood.motor.get_last_voltage() == 0
