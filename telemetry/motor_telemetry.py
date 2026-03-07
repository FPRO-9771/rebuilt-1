"""
Motor telemetry publisher.
Publishes position and velocity for each motor to SmartDashboard.
"""

import wpilib


class MotorTelemetry:
    """Publishes motor data for all shooter subsystems."""

    def __init__(self, conveyor, turret, launcher, hood, h_feed=None, v_feed=None):
        self._conveyor = conveyor
        self._turret = turret
        self._launcher = launcher
        self._hood = hood
        self._h_feed = h_feed
        self._v_feed = v_feed

    def update(self):
        """Publish current motor data to SmartDashboard."""
        sd = wpilib.SmartDashboard
        if self._conveyor is not None:
            sd.putNumber("Motors/Conveyor Velocity", self._conveyor.get_velocity())
        sd.putNumber("Motors/Turret Position", self._turret.get_position())
        sd.putNumber("Motors/Turret Velocity", self._turret.get_velocity())
        sd.putNumber("Motors/Launcher Target RPS", self._launcher._target_rps)
        sd.putNumber("Motors/Launcher Actual RPS", self._launcher.get_velocity())
        sd.putBoolean("Motors/Launcher At Speed", self._launcher.is_at_speed(self._launcher._target_rps))
        if self._hood._enabled:
            sd.putNumber("Motors/Hood Position", self._hood.get_position())
        if self._h_feed is not None:
            sd.putNumber("Motors/H Feed Velocity", self._h_feed.get_velocity())
        if self._v_feed is not None:
            sd.putNumber("Motors/V Feed Velocity", self._v_feed.get_velocity())
