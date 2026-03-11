"""
Telemetry dashboard module.
Publishes motor, command, vision, and camera stream data to SmartDashboard.

Call setup_telemetry() once during init, then update_telemetry() every cycle.
"""

from telemetry.motor_telemetry import MotorTelemetry
from telemetry.command_telemetry import CommandTelemetry
from telemetry.vision_telemetry import VisionTelemetry
from telemetry.camera_telemetry import setup_camera_streams
from constants.debug import DEBUG

_motor: MotorTelemetry | None = None
_command: CommandTelemetry | None = None
_vision: VisionTelemetry | None = None
_cycle: int = 0

# Publish telemetry every Nth cycle (8 = ~2.5 Hz at 20 Hz loop rate).
# Keeps the robot loop fast on the roboRIO.
_PUBLISH_EVERY_N = 8


def setup_telemetry(conveyor, turret, launcher, hood, vision,
                    h_feed=None, v_feed=None):
    """Create all telemetry publishers. Call once from RobotContainer.

    Args:
        vision: dict of camera_key -> VisionProvider
    """
    global _motor, _command, _vision

    _motor = MotorTelemetry(conveyor, turret, launcher, hood, h_feed, v_feed)
    _command = CommandTelemetry()
    _command.setup()
    _vision = VisionTelemetry(vision)
    setup_camera_streams()


def update_telemetry():
    """Publish telemetry data, staggered so no two hit the same cycle."""
    global _cycle
    _cycle += 1

    # Motor telemetry handles its own match/debug split internally.
    if _motor and _cycle % _PUBLISH_EVERY_N == 0:
        _motor.update()

    # Command and vision telemetry are debug-only.
    if not DEBUG["debug_telemetry"]:
        return
    if _command and _cycle % _PUBLISH_EVERY_N == 3:
        _command.update()
    if _vision and _cycle % _PUBLISH_EVERY_N == 6:
        _vision.update()
