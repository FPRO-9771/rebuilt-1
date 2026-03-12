"""
Auto-aim debug logging.
Structured log output for the three auto-aim states: lost, holding, driving.
Called by AutoAim command -- all data passed in as arguments.
"""

from constants.debug import DEBUG
from utils.logger import get_logger

_log = get_logger("auto_aim")


def _enabled():
    """Check if auto-aim logging is active."""
    return DEBUG["verbose"] or DEBUG["auto_aim_logging"]


def _emit(msg):
    """Log at the right level depending on which flag is on."""
    if DEBUG["verbose"]:
        _log.debug(msg)
    else:
        _log.info(msg)


def log_lost(cycle, position):
    """Log when target is fully lost (no lock). Every other cycle."""
    if not _enabled() or cycle % 2 != 0:
        return
    _emit(
        f"[AIM] t=-- ftx=0.00 -- no target "
        f"pos={position:.3f}"
    )


def log_hold(cycle, locked_tag_id, filtered_tx, position):
    """Log when turret is on-target and holding still. Every other cycle."""
    if not _enabled() or cycle % 2 != 0:
        return
    _emit(
        f"[AIM] t={locked_tag_id} "
        f"ftx={filtered_tx:.2f} -- within tolerance "
        f"pos={position:.3f}"
    )


def log_drive(cycle, locked_tag_id, target, filtered_tx,
              p_term, d_term, ff_term, raw_voltage, voltage,
              turret_vel, position, vx, vy, lead_deg,
              ball_speed, parallax_deg, lost_count):
    """Log PD control output when actively driving. Every other cycle."""
    if not _enabled() or cycle % 2 != 0:
        return
    sat = "SAT" if abs(raw_voltage) > abs(voltage) else "ok"
    raw_tx = f"{target.tx:.2f}" if target is not None else "--"
    coast = f" coast={lost_count}" if target is None else ""
    _emit(
        f"[AIM] t={locked_tag_id} "
        f"tx={raw_tx} ftx={filtered_tx:.2f} "
        f"P={p_term:.3f} D={d_term:.3f} FF={ff_term:.3f} "
        f"rv={raw_voltage:.3f} v={voltage:.3f} [{sat}]{coast} "
        f"vel={turret_vel:.3f} pos={position:.3f} "
        f"vx={vx:.2f} vy={vy:.2f} ld={lead_deg:.2f} "
        f"bs={ball_speed:.1f} px={parallax_deg:.2f}"
    )
