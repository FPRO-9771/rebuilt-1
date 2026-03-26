"""
Telemetry dashboard module.
Publishes motor, command, vision, and camera stream data to SmartDashboard.

Call setup_telemetry() once during init, then update_telemetry() every cycle.
"""

from telemetry.motor_telemetry import MotorTelemetry
from telemetry.command_telemetry import CommandTelemetry
from telemetry.vision_telemetry import VisionTelemetry
from telemetry.camera_telemetry import setup_camera_streams
from telemetry.turret_aim_telemetry import TurretAimTelemetry
from constants.debug import DEBUG

_motor: MotorTelemetry | None = None
_command: CommandTelemetry | None = None
_vision: VisionTelemetry | None = None
_turret_aim: TurretAimTelemetry | None = None
_cycle: int = 0

# Match-mode keys publish on a 10-cycle (500 ms) period, each on a
# unique offset so at most one SmartDashboard put lands per cycle.
# Debug-only telemetry uses the same period with its own offsets.
_PERIOD = 10


def setup_telemetry(conveyor, turret, launcher, vision,
                    h_feed=None, v_feed=None, intake_spinner=None,
                    drivetrain=None, alliance_supplier=None):
    """Create all telemetry publishers. Call once from RobotContainer.

    Args:
        vision: dict of camera_key -> VisionProvider
        drivetrain: swerve drivetrain (for turret aim telemetry)
        alliance_supplier: callable returning alliance dict (for turret aim telemetry)
    """
    global _motor, _command, _vision, _turret_aim

    _motor = MotorTelemetry(conveyor, turret, launcher, h_feed, v_feed,
                            intake_spinner)
    _command = CommandTelemetry()
    _command.setup()
    _vision = VisionTelemetry(vision)
    setup_camera_streams()

    if drivetrain and turret and alliance_supplier:
        _turret_aim = TurretAimTelemetry(drivetrain, turret, alliance_supplier)


def update_telemetry():
    """Publish telemetry data, staggered so no two hit the same cycle."""
    global _cycle
    _cycle += 1

    # Motor telemetry staggers each key internally using the cycle count.
    if _motor:
        _motor.update(_cycle)

    # Turret aim telemetry (independently toggleable via DEBUG flag)
    if _turret_aim:
        _turret_aim.update(_cycle)

    # Command and vision telemetry are debug-only.
    if not DEBUG["debug_telemetry"]:
        return
    if _command and _cycle % _PERIOD == 3:
        _command.update()
    if _vision and _cycle % _PERIOD == 7:
        _vision.update()
