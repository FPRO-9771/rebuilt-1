"""
Shoot-when-ready command -- hold to engage.
Spins up launcher immediately from pose-based distance. Once the
launcher reaches speed for the first time, feeders run whenever the
turret is on target. If the H feed stalls (velocity near zero),
reverses it briefly to un-jam, then resumes. Release to stop everything.
"""

from typing import Callable

from commands2 import Command
from subsystems.launcher import Launcher
from subsystems.h_feed import HFeed
from subsystems.v_feed import VFeed
from subsystems.shooter_lookup import get_shooter_settings
from commands.reverse_feeds import reverse_all_feeds, stop_all_feeds
from constants import CON_H_FEED, CON_V_FEED
from constants.shoot_auto_shoot import CON_AUTO_SHOOT
from constants.debug import DEBUG
from telemetry.auto_aim_logging import log_shoot
from utils.logger import get_logger

_log = get_logger("shoot_when_ready")


class ShootWhenReady(Command):
    """Spins launcher; once at speed, feeds whenever turret is on target."""

    def __init__(
        self,
        launcher: Launcher,
        h_feed: HFeed,
        v_feed: VFeed,
        context_supplier: Callable,
        on_target_supplier: Callable[[], bool],
        conveyor=None,
    ):
        super().__init__()
        self.launcher = launcher
        self.h_feed = h_feed
        self.v_feed = v_feed
        self.conveyor = conveyor
        self._context_supplier = context_supplier
        self._on_target_supplier = on_target_supplier
        self._reached_speed = False
        self._feeding = False
        self._off_target_count = 0
        self._unjamming = False
        self._unjam_counter = 0
        self._cycle_count = 0
        self._feed_cycle_count = 0
        requirements = [launcher, h_feed, v_feed]
        if conveyor is not None:
            requirements.append(conveyor)
        self.addRequirements(*requirements)

    def initialize(self):
        self._reached_speed = False
        self._feeding = False
        self._off_target_count = 0
        self._unjamming = False
        self._unjam_counter = 0
        self._cycle_count = 0
        self._feed_cycle_count = 0
        _log.info("ShootWhenReady ENABLED")
        if DEBUG["auto_sequence_logging"]:
            _log.info("AUTO SEQ: ShootWhenReady initialize -- spinning up launcher")

    def execute(self):
        # Always spin up launcher
        ctx = self._context_supplier()
        rps = get_shooter_settings(ctx.corrected_distance)
        self.launcher._set_velocity(rps)

        # One-time gate: once launcher reaches speed, it stays unlocked
        at_speed = self.launcher.is_at_speed(rps)
        if at_speed and not self._reached_speed:
            _log.info("Launcher reached speed -- unlocked")
            self._reached_speed = True
            if DEBUG["auto_sequence_logging"]:
                _log.info(f"AUTO SEQ: ShootWhenReady launcher at speed after {self._cycle_count} cycles")

        # After speed gate passed, feed whenever turret is on target.
        # Debounce: start feeding instantly when on-target, but require
        # N consecutive off-target cycles before stopping (prevents stutter).
        on_target = self._on_target_supplier()
        ready = self._reached_speed and on_target
        debounce = CON_AUTO_SHOOT["feed_off_target_debounce"]

        if ready:
            self._off_target_count = 0
            if not self._feeding:
                _log.debug("On target -- feeding")
                self._feeding = True
        else:
            self._off_target_count += 1
            if self._feeding and self._off_target_count >= debounce:
                _log.debug("Off target %d cycles -- stopping feed",
                           self._off_target_count)
                self._feeding = False
                self._feed_cycle_count = 0

        # --- Un-jam state machine ---
        # While feeding, if H feed velocity drops near zero, reverse all
        # feeds briefly to clear the jam, then resume.
        if self._unjamming:
            self._unjam_counter -= 1
            reverse_all_feeds(self.h_feed, self.v_feed, self.conveyor)
            if self._unjam_counter <= 0:
                self._unjamming = False
                _log.info("Un-jam complete -- resuming feed")
        elif self._feeding:
            self._feed_cycle_count += 1
            h_vel = self.h_feed.get_velocity()
            # Skip stall check during spin-up to avoid false unjam triggers
            if self._feed_cycle_count > CON_H_FEED["unjam_spinup_cycles"] and abs(h_vel) < CON_H_FEED["unjam_velocity_threshold"]:
                self._unjamming = True
                self._unjam_counter = CON_H_FEED["unjam_duration_cycles"]
                _log.warning("H feed stalled -- un-jamming")
                reverse_all_feeds(self.h_feed, self.v_feed, self.conveyor)
            else:
                self.h_feed._set_voltage(CON_H_FEED["feed_voltage"])
                self.v_feed._set_voltage(CON_V_FEED["feed_voltage"])
        else:
            stop_all_feeds(self.h_feed, self.v_feed, self.conveyor)

        log_shoot(
            self._cycle_count,
            ctx=ctx,
            rps=rps,
            actual_rps=self.launcher.get_velocity(),
            at_speed=at_speed,
            reached_speed=self._reached_speed,
            on_target=on_target,
            feeding=self._feeding,
        )
        self._cycle_count += 1

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool):
        self.launcher._stop()
        stop_all_feeds(self.h_feed, self.v_feed, self.conveyor)
        _log.info(f"ShootWhenReady DISABLED (interrupted={interrupted})")
        if DEBUG["auto_sequence_logging"]:
            _log.info(f"AUTO SEQ: ShootWhenReady end -- ran {self._cycle_count} cycles, reached_speed={self._reached_speed}")
