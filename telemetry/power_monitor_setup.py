"""
Builds the group -> motor-reader map for PowerMonitor from live subsystems.

Kept separate from power_monitor.py so PowerMonitor stays generic and the
subsystem-coupling logic lives in one easy-to-edit place.
"""

from typing import List, Callable

from telemetry.power_monitor import PowerMonitor, MotorHandle
from telemetry.power_csv import make_csv_writer, resolve_log_dir
from utils.logger import get_logger

_log = get_logger("power_monitor")


def _abstraction_reader(motor) -> Callable[[], float]:
    """Reader for hardware.MotorController instances."""
    return lambda m=motor: m.get_supply_current()


def _phoenix_reader(talon) -> Callable[[], float]:
    """Reader for raw Phoenix 6 TalonFX (drivetrain swerve modules)."""
    return lambda m=talon: m.get_supply_current().value


def _drivetrain_motors(drivetrain) -> List[MotorHandle]:
    """Pull the 4 drive + 4 steer TalonFX handles out of the swerve modules.

    Returns an empty list if the Phoenix 6 API can't be read -- we warn but
    don't crash, since power monitoring is a diagnostic aid, not match-critical.
    """
    positions = ("fl", "fr", "bl", "br")
    handles: List[MotorHandle] = []
    try:
        for i, pos in enumerate(positions):
            module = drivetrain.get_module(i)
            handles.append((f"{pos}_drive", _phoenix_reader(module.drive_motor)))
            handles.append((f"{pos}_steer", _phoenix_reader(module.steer_motor)))
    except Exception as e:
        _log.warning(f"drivetrain motor handles unavailable: {e}")
        return []
    return handles


def build_power_monitor(drivetrain, intake, intake_spinner,
                        h_feed, v_feed, turret, launcher) -> PowerMonitor:
    """Construct a PowerMonitor with the 9771 2026 subsystem grouping."""
    groups = {
        "drivetrain": _drivetrain_motors(drivetrain),
        "intake_arms": [
            ("intake_left", _abstraction_reader(intake.motor_left)),
            ("intake_right", _abstraction_reader(intake.motor_right)),
        ],
        "intake_spinner": [
            ("intake_spinner", _abstraction_reader(intake_spinner.motor)),
        ],
        "shooting": [
            ("h_feed", _abstraction_reader(h_feed.motor)),
            ("v_feed", _abstraction_reader(v_feed.motor)),
            ("turret", _abstraction_reader(turret.motor)),
            ("launcher", _abstraction_reader(launcher.motor)),
        ],
    }
    return PowerMonitor(groups, csv_writer=make_csv_writer(resolve_log_dir()))
