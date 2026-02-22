"""
Telemetry dashboard module.
Publishes motor, command, and vision data to SmartDashboard.

Call setup_telemetry() once during init, then update_telemetry() every cycle.
"""

from telemetry.motor_telemetry import MotorTelemetry
from telemetry.command_telemetry import CommandTelemetry
from telemetry.vision_telemetry import VisionTelemetry

_motor: MotorTelemetry | None = None
_command: CommandTelemetry | None = None
_vision: VisionTelemetry | None = None


def setup_telemetry(conveyor, turret, launcher, hood, vision):
    """Create all telemetry publishers. Call once from RobotContainer."""
    global _motor, _command, _vision

    _motor = MotorTelemetry(conveyor, turret, launcher, hood)
    _command = CommandTelemetry()
    _command.setup()
    _vision = VisionTelemetry(vision)


def update_telemetry():
    """Publish all telemetry data. Call every cycle from robotPeriodic()."""
    if _motor:
        _motor.update()
    if _command:
        _command.update()
    if _vision:
        _vision.update()
