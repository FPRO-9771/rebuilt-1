"""
Motor telemetry publisher.
Publishes position and velocity for each motor to SmartDashboard.
"""

import wpilib


class MotorTelemetry:
    """Publishes motor data for all shooter subsystems."""

    def __init__(self, conveyor, turret, launcher, hood):
        self._conveyor = conveyor
        self._turret = turret
        self._launcher = launcher
        self._hood = hood

    def update(self):
        """Publish current motor data to SmartDashboard."""
        sd = wpilib.SmartDashboard
        if self._conveyor is not None:
            sd.putNumber("Motors/Conveyor Velocity", self._conveyor.get_velocity())
        sd.putNumber("Motors/Turret Position", self._turret.get_position())
        sd.putNumber("Motors/Turret Velocity", self._turret.get_velocity())
        sd.putNumber("Motors/Launcher Target RPS", self._launcher._target_rps)
        sd.putNumber("Motors/Launcher Velocity", self._launcher.get_velocity())
        sd.putBoolean("Motors/Launcher At Speed", self._launcher.is_at_speed(self._launcher._target_rps))
        sd.putNumber("Motors/Hood Position", self._hood.get_position())
