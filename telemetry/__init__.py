"""
Telemetry dashboard module.
Publishes motor, command, vision, and camera stream data to SmartDashboard.

Call setup_telemetry() once during init, then update_telemetry() every cycle.
"""

from telemetry.motor_telemetry import MotorTelemetry
from telemetry.command_telemetry import CommandTelemetry
from telemetry.vision_telemetry import VisionTelemetry
from telemetry.camera_telemetry import setup_camera_streams

_motor: MotorTelemetry | None = None
_command: CommandTelemetry | None = None
_vision: VisionTelemetry | None = None
_cycle: int = 0

# Publish telemetry every Nth cycle (4 = ~3 Hz at 13 Hz loop rate).
# Keeps the robot loop fast on the roboRIO.
_PUBLISH_EVERY_N = 4


def setup_telemetry(conveyor, turret, launcher, hood, vision):
    """Create all telemetry publishers. Call once from RobotContainer.

    Args:
        vision: dict of camera_key -> VisionProvider
    """
    global _motor, _command, _vision

    _motor = MotorTelemetry(conveyor, turret, launcher, hood)
    _command = CommandTelemetry()
    _command.setup()
    _vision = VisionTelemetry(vision)
    setup_camera_streams()


def update_telemetry():
    """Publish all telemetry data. Call every cycle from robotPeriodic()."""
    global _cycle
    _cycle += 1
    if _cycle % _PUBLISH_EVERY_N != 0:
        return

    if _motor:
        _motor.update()
    if _command:
        _command.update()
    if _vision:
        _vision.update()
