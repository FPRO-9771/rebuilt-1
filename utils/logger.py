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

from constants.debug import DEBUG


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

    level = logging.DEBUG if DEBUG["verbose"] else logging.INFO
    logger.setLevel(level)
    logger.propagate = False  # prevent root logger from duplicating output

    # Console handler — all messages go to stdout (Rio log)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(logging.Formatter(
        "[%(name)s] %(levelname)s: %(message)s"
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
