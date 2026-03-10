"""
Tests for FindTarget command.
"""

from subsystems.turret import Turret
from commands.find_target import FindTarget
from handlers.mock_vision import MockVisionProvider
from tests.conftest import TEST_CON_TURRET, TEST_TAG_PRIORITY

_MID_POS = (TEST_CON_TURRET["min_position"] + TEST_CON_TURRET["max_position"]) / 2


def _make_find_target(initial_direction=1.0, tag_priority=None):
    turret = Turret()
    turret.motor.simulate_position(_MID_POS)
    vision = MockVisionProvider()
    priority = tag_priority if tag_priority is not None else TEST_TAG_PRIORITY
    cmd = FindTarget(
        turret, vision,
        tag_priority_supplier=lambda: priority,
        initial_direction=initial_direction,
    )
    return cmd, turret, vision


def test_sweeps_positive_direction():
    """Default sweep applies positive voltage."""
    cmd, turret, vision = _make_find_target(initial_direction=1.0)
    cmd.initialize()
    cmd.execute()

    expected = TEST_CON_TURRET["search_voltage"]
    assert turret.motor.get_last_voltage() == expected


def test_sweeps_negative_direction():
    """Negative initial direction applies negative voltage."""
    cmd, turret, vision = _make_find_target(initial_direction=-1.0)
    cmd.initialize()
    cmd.execute()

    expected = -TEST_CON_TURRET["search_voltage"]
    assert turret.motor.get_last_voltage() == expected


def test_finishes_when_target_found():
    """Command ends when a priority tag becomes visible."""
    cmd, turret, vision = _make_find_target()
    cmd.initialize()

    # No target -- should keep sweeping
    cmd.execute()
    assert not cmd.isFinished()

    # Target appears
    vision.simulate_target_centered(tag_id=TEST_TAG_PRIORITY[0], distance=2.0)
    cmd.execute()
    assert cmd.isFinished()
    assert cmd.found_target() is True


def test_ignores_non_priority_tags():
    """Tags not in the priority list don't count as found."""
    cmd, turret, vision = _make_find_target(tag_priority=[4])
    cmd.initialize()

    # Tag 99 is visible but not in priority list
    vision.simulate_target_centered(tag_id=99, distance=2.0)
    cmd.execute()
    assert not cmd.isFinished()
    assert cmd.found_target() is False


def test_brakes_at_soft_limit():
    """Hitting a soft limit triggers braking voltage in the opposite direction."""
    cmd, turret, vision = _make_find_target(initial_direction=1.0)
    cmd.initialize()

    # Place turret at the max soft limit
    max_pos = TEST_CON_TURRET["max_position"]
    tol = TEST_CON_TURRET["position_tolerance"]
    turret.motor.simulate_position(max_pos - tol)

    cmd.execute()  # Should detect limit and start braking

    # Brake voltage should oppose the sweep direction (negative)
    brake_v = TEST_CON_TURRET["search_brake_voltage"]
    assert turret.motor.get_last_voltage() == -brake_v


def test_reverses_after_braking():
    """After braking for the configured cycles, sweep reverses direction."""
    cmd, turret, vision = _make_find_target(initial_direction=1.0)
    cmd.initialize()

    # Hit the max limit
    max_pos = TEST_CON_TURRET["max_position"]
    tol = TEST_CON_TURRET["position_tolerance"]
    turret.motor.simulate_position(max_pos - tol)

    # First execute triggers braking (sets brake_counter=0)
    cmd.execute()

    # Run through brake cycles until reversal completes
    brake_cycles = TEST_CON_TURRET["search_brake_cycles"]
    for _ in range(brake_cycles):
        cmd.execute()

    # Move turret to middle so next execute does a normal sweep
    turret.motor.simulate_position(_MID_POS)
    cmd.execute()

    # Should now be sweeping in the negative direction
    expected = -TEST_CON_TURRET["search_voltage"]
    assert turret.motor.get_last_voltage() == expected


def test_finishes_after_two_reversals():
    """Exhausting both directions ends the command with found=False."""
    cmd, turret, vision = _make_find_target(initial_direction=1.0)
    cmd.initialize()

    max_pos = TEST_CON_TURRET["max_position"]
    min_pos = TEST_CON_TURRET["min_position"]
    tol = TEST_CON_TURRET["position_tolerance"]
    brake_cycles = TEST_CON_TURRET["search_brake_cycles"]

    # First reversal: hit max limit
    turret.motor.simulate_position(max_pos - tol)
    for _ in range(brake_cycles + 1):
        cmd.execute()
    assert not cmd.isFinished()

    # Second reversal: hit min limit
    turret.motor.simulate_position(min_pos + tol)
    for _ in range(brake_cycles + 1):
        cmd.execute()
    assert cmd.isFinished()
    assert cmd.found_target() is False


def test_stops_turret_on_end():
    """Turret stops when command ends."""
    cmd, turret, vision = _make_find_target()
    cmd.initialize()
    cmd.execute()
    assert turret.motor.get_last_voltage() != 0

    cmd.end(False)
    assert turret.motor.get_last_voltage() == 0


def test_finds_target_during_reverse_sweep():
    """Target found while sweeping in reverse direction still works."""
    cmd, turret, vision = _make_find_target(initial_direction=1.0)
    cmd.initialize()

    # Hit the max limit and brake through to reverse
    max_pos = TEST_CON_TURRET["max_position"]
    tol = TEST_CON_TURRET["position_tolerance"]
    brake_cycles = TEST_CON_TURRET["search_brake_cycles"]

    turret.motor.simulate_position(max_pos - tol)
    for _ in range(brake_cycles + 1):
        cmd.execute()

    # Now sweeping negative -- target appears
    turret.motor.simulate_position(_MID_POS)
    vision.simulate_target_centered(tag_id=TEST_TAG_PRIORITY[0], distance=2.0)
    cmd.execute()

    assert cmd.isFinished()
    assert cmd.found_target() is True


def test_found_target_while_braking():
    """If a target appears mid-brake, command ends immediately."""
    cmd, turret, vision = _make_find_target(initial_direction=1.0)
    cmd.initialize()

    # Hit the max limit to start braking
    max_pos = TEST_CON_TURRET["max_position"]
    tol = TEST_CON_TURRET["position_tolerance"]
    turret.motor.simulate_position(max_pos - tol)
    cmd.execute()  # Start braking

    # Target appears during brake
    vision.simulate_target_centered(tag_id=TEST_TAG_PRIORITY[0], distance=2.0)
    cmd.execute()

    assert cmd.isFinished()
    assert cmd.found_target() is True
