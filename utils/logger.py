"""
FRC-aware logging utility.

Wraps Python's logging module with handlers that route messages
to the right places based on severity:

  DEBUG / INFO  -> Console only (Rio log)
  WARNING       -> Console + Driver Station warning
  ERROR+        -> Console + Driver Station error

Usage:
    from utils import get_logger
    logger = get_logger("turret")
    logger.debug("Position zeroed")
    logger.warning("Turret near soft limit")
    logger.error("Motor not responding")
"""

import logging
import sys
import time

from constants.debug import DEBUG


# Elapsed-time tracking for auton logging.
_auton_start_time = None


def reset_auton_timer():
    """Call from autonomousInit to start the elapsed-time clock."""
    global _auton_start_time
    _auton_start_time = time.monotonic()


class _ElapsedFormatter(logging.Formatter):
    """Shows elapsed time since auton started (or wall clock before that)."""

    def format(self, record):
        if _auton_start_time is not None:
            elapsed = time.monotonic() - _auton_start_time
            record.elapsed = f"T+{elapsed:06.2f}s"
        else:
            record.elapsed = ""
        return super().format(record)


class _DriverStationHandler(logging.Handler):
    """Routes WARNING+ to WPILib Driver Station reports."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            import wpilib
            msg = self.format(record)
            if record.levelno >= logging.ERROR:
                wpilib.reportError(msg, False)
            elif record.levelno >= logging.WARNING:
                wpilib.reportWarning(msg, False)
        except ImportError:
            # Not running on a robot — skip DS reporting
            pass


# Loggers that keep INFO level in auton_quiet_mode.
# Everything else is raised to WARNING to reduce noise.
#
# vpc          -- per-cycle vision_pose_correct() debug dump (gated by
#                 DEBUG["vision_pose_correct_logging"], rate-limited).
# vision_reset -- B-button hard-reset breadcrumb trail. Always on so the
#                 driver can see why the escape hatch did or did not fire.
_AUTON_LOGGERS = {
    "robot", "named_commands", "auton_modes",
    "vpc", "vision_reset",
}


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger with FRC-aware handlers.

    Args:
        name: Logger name, typically the subsystem (e.g. "turret")

    Returns:
        Configured logging.Logger instance
    """
    logger = logging.getLogger(f"frc.{name}")

    # Only configure once per logger
    if logger.handlers:
        return logger

    if DEBUG["verbose"]:
        level = logging.DEBUG
    elif DEBUG.get("auton_quiet_mode") and name not in _AUTON_LOGGERS:
        # Allow turret_minion through when turret_angle_logging is on
        if name == "turret_minion" and DEBUG.get("turret_angle_logging"):
            level = logging.INFO
        else:
            level = logging.WARNING
    else:
        level = logging.INFO
    logger.setLevel(level)
    logger.propagate = False  # prevent root logger from duplicating output

    # Console handler — all messages go to stdout (Rio log)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(_ElapsedFormatter(
        "%(elapsed)s [%(name)s] %(levelname)s: %(message)s"
    ))
    logger.addHandler(console)

    # Driver Station handler — WARNING and above
    ds = _DriverStationHandler()
    ds.setLevel(logging.WARNING)
    ds.setFormatter(logging.Formatter(
        "%(name)s: %(message)s"
    ))
    logger.addHandler(ds)

    return logger
