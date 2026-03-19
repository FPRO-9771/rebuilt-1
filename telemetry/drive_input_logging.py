"""
Drive input pipeline debug logging.
Shows raw stick values, post-curve values, and final velocities
to help tune exponents and deadband for driver feel.

Toggle with DEBUG["drive_input_logging"] in constants/debug.py.
This flag is independent of DEBUG["verbose"] -- you can see drive
input logs without turning on all other debug output.
"""

from wpilib import SmartDashboard

from constants.debug import DEBUG
from utils.logger import get_logger

_log = get_logger("drive_input")

# Throttle console logs to every Nth call to avoid flooding.
_LOG_EVERY_N = 10
_cycle = 0


def _enabled():
    """Check if drive input logging is active."""
    return DEBUG["verbose"] or DEBUG["drive_input_logging"]


def _emit(msg):
    """Log at the right level depending on which flag is on.

    When drive_input_logging is on (but verbose is off), use INFO so
    the message appears without requiring DEBUG level globally.
    When verbose is on, use DEBUG to keep it with other debug output.
    """
    if DEBUG["verbose"]:
        _log.debug(msg)
    else:
        _log.info(msg)


def log_drive_inputs(raw_ly, raw_lx, raw_rx,
                     curved_ly, curved_lx, curved_rx,
                     vel_x, vel_y, rot,
                     speed_scale, drive_exp, rot_exp):
    """Log the full drive input pipeline to console + SmartDashboard.

    SmartDashboard values update every cycle for responsive graphs.
    Console messages are throttled and skip idle stick positions.
    """
    if not _enabled():
        return

    global _cycle
    _cycle += 1

    # SmartDashboard -- every cycle so the dashboard stays responsive
    SmartDashboard.putNumber("DriveInput/Raw LY", round(raw_ly, 4))
    SmartDashboard.putNumber("DriveInput/Raw LX", round(raw_lx, 4))
    SmartDashboard.putNumber("DriveInput/Raw RX", round(raw_rx, 4))
    SmartDashboard.putNumber("DriveInput/Curved LY", round(curved_ly, 4))
    SmartDashboard.putNumber("DriveInput/Curved LX", round(curved_lx, 4))
    SmartDashboard.putNumber("DriveInput/Curved RX", round(curved_rx, 4))
    SmartDashboard.putNumber("DriveInput/Vel X (mps)", round(vel_x, 3))
    SmartDashboard.putNumber("DriveInput/Vel Y (mps)", round(vel_y, 3))
    SmartDashboard.putNumber("DriveInput/Rot (radps)", round(rot, 3))
    SmartDashboard.putNumber("DriveInput/Speed Scale", round(speed_scale, 3))
    SmartDashboard.putNumber("DriveInput/Drive Exponent", drive_exp)
    SmartDashboard.putNumber("DriveInput/Rotation Exponent", rot_exp)

    # Console -- throttled
    if _cycle % _LOG_EVERY_N != 0:
        return
    # Only log when sticks are active (skip idle spam)
    if abs(raw_ly) < 0.05 and abs(raw_lx) < 0.05 and abs(raw_rx) < 0.05:
        return
    _emit(
        f"raw({raw_ly:+.3f},{raw_lx:+.3f},{raw_rx:+.3f}) "
        f"curved({curved_ly:+.4f},{curved_lx:+.4f},{curved_rx:+.4f}) "
        f"vel({vel_x:+.2f},{vel_y:+.2f},{rot:+.3f}) "
        f"scale={speed_scale:.2f} exp=({drive_exp},{rot_exp})"
    )
