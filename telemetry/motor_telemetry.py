"""
Motor telemetry publisher.
Publishes position and velocity for each motor to SmartDashboard.
"""

import wpilib

from constants.debug import DEBUG
from constants.shoot_hardware import CON_TURRET_MINION


class MotorTelemetry:
    """Publishes motor data for all shooter subsystems."""

    # Stagger offsets within a 10-cycle (500 ms) period so at most one
    # SmartDashboard put lands per cycle.  AutoAim/OnTarget uses offset 1
    # (in auto_aim_telemetry), so we avoid that here.
    _PERIOD = 10
    _OFF_LAUNCHER = 0
    _OFF_FEEDER = 2
    _OFF_INTAKE = 4
    _OFF_TURRET_CLEAR = 6
    _OFF_DEBUG = 8

    def __init__(self, turret, launcher, h_feed=None,
                 v_feed=None, intake_spinner=None):
        self._turret = turret
        self._launcher = launcher
        self._h_feed = h_feed
        self._v_feed = v_feed
        self._intake_spinner = intake_spinner

    def update(self, cycle):
        """Publish motor data, one key per cycle on staggered offsets."""
        sd = wpilib.SmartDashboard
        slot = cycle % self._PERIOD

        # -- Match-critical (one put per offset) --
        if slot == self._OFF_LAUNCHER:
            sd.putBoolean("Motors/Launcher At Speed",
                          self._launcher.is_at_speed(self._launcher._target_rps))

        elif slot == self._OFF_FEEDER:
            feeder_running = False
            if self._h_feed is not None:
                feeder_running = feeder_running or abs(self._h_feed.get_velocity()) > 0.1
            if self._v_feed is not None:
                feeder_running = feeder_running or abs(self._v_feed.get_velocity()) > 0.1
            if self._h_feed is not None or self._v_feed is not None:
                sd.putBoolean("Motors/Feeder Running", feeder_running)

        elif slot == self._OFF_INTAKE:
            if self._intake_spinner is not None:
                sd.putBoolean("Motors/Intake Running",
                              abs(self._intake_spinner.get_velocity()) > 0.1)

        elif slot == self._OFF_TURRET_CLEAR:
            pos = self._turret.get_position()
            tol = CON_TURRET_MINION["position_tolerance"]
            clear = (pos > CON_TURRET_MINION["min_position"] + tol
                     and pos < CON_TURRET_MINION["max_position"] - tol)
            sd.putBoolean("Motors/Turret Clear", clear)

        elif slot == self._OFF_DEBUG and DEBUG["debug_telemetry"]:
            sd.putNumber("Motors/Turret Position", self._turret.get_position())
            sd.putNumber("Motors/Turret Velocity", self._turret.get_velocity())
            sd.putNumber("Motors/Launcher Target RPS", self._launcher._target_rps)
            sd.putNumber("Motors/Launcher Actual RPS", self._launcher.get_velocity())
