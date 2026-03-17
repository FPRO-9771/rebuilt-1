"""
Tests for auto-shoot command.
"""

from subsystems.launcher import Launcher
from subsystems.hood import Hood
from commands.auto_shoot import AutoShoot
from subsystems.shooter_lookup import get_shooter_settings
from calculations.target_state import ShootContext


def _make_context(distance=2.0):
    """Create a ShootContext with the given corrected distance."""
    return ShootContext(
        corrected_distance=distance,
        raw_distance=distance,
        closing_speed_mps=0.0,
        pose_x=0.0,
        pose_y=0.0,
        heading_deg=0.0,
        shooter_x=0.0,
        shooter_y=0.0,
        target_x=5.0,
        target_y=0.0,
        vx=0.0,
        vy=0.0,
    )


def _make_auto_shoot(distance=2.0):
    launcher = Launcher()
    hood = Hood()
    ctx = _make_context(distance)
    cmd = AutoShoot(
        launcher, hood,
        context_supplier=lambda: ctx,
    )
    return cmd, launcher, hood


def test_sets_launcher_from_distance():
    """Launcher RPS matches distance table lookup."""
    cmd, launcher, hood = _make_auto_shoot(distance=2.0)

    cmd.initialize()
    cmd.execute()

    expected_rps, _ = get_shooter_settings(2.0)
    assert launcher.motor._velocity == expected_rps


def test_sets_hood_from_distance():
    """Hood position matches distance table lookup."""
    cmd, launcher, hood = _make_auto_shoot(distance=3.0)

    cmd.initialize()
    cmd.execute()

    _, expected_hood = get_shooter_settings(3.0)
    assert hood.motor._position == expected_hood


def test_uses_supplied_distance():
    """Uses the distance from the supplier for lookup."""
    cmd, launcher, hood = _make_auto_shoot(distance=1.0)

    cmd.initialize()
    cmd.execute()

    expected_rps, _ = get_shooter_settings(1.0)
    assert launcher.motor._velocity == expected_rps


def test_stops_all_on_end():
    """Launcher and hood stop when command ends."""
    cmd, launcher, hood = _make_auto_shoot(distance=2.0)

    cmd.initialize()
    cmd.execute()
    cmd.end(False)

    assert launcher.motor.get_last_voltage() == 0
    assert hood.motor.get_last_voltage() == 0


def test_never_auto_finishes():
    """AutoShoot never auto-finishes."""
    cmd, launcher, hood = _make_auto_shoot()
    cmd.initialize()
    assert cmd.isFinished() is False


def test_dynamic_context_supplier():
    """Context supplier is called each cycle, not just once."""
    launcher = Launcher()
    hood = Hood()

    contexts = [_make_context(1.0), _make_context(3.0)]
    call_count = [0]

    def _changing_context():
        idx = min(call_count[0], len(contexts) - 1)
        call_count[0] += 1
        return contexts[idx]

    cmd = AutoShoot(launcher, hood, context_supplier=_changing_context)
    cmd.initialize()

    cmd.execute()
    rps_first = launcher.motor._velocity

    cmd.execute()
    rps_second = launcher.motor._velocity

    # Distance changed, so RPS should change
    assert rps_first != rps_second
