"""
Movement compensation debug logging.
Shows the full compensation pipeline: inputs, intermediates, and outputs.
One line per cycle with everything needed to debug why a shot missed.

Toggle with DEBUG["compensation_logging"] in constants/debug.py.

Example output:
[COMP] vel=(0.50,1.20) dist=3.00 bearing=45.0 cls=0.50
  | v_tan=0.85 flightT=0.33 leadM=0.28 leadDeg=5.35 gain=1.00 finalLead=5.35
  | rawDist=3.00 corrDist=2.84
"""

import math

from subsystems.shooter_lookup import get_flight_time
from constants.shoot_auto_shoot import CON_AUTO_SHOOT
from constants.debug import DEBUG
from utils.logger import get_logger

_log = get_logger("compensation")


def log_compensation(cycle, vx, vy, raw_distance, bearing_rad,
                     closing_speed, corrected_distance, lead_deg):
    """Log the full compensation pipeline for debugging.

    Recomputes intermediates from the raw inputs so we can see
    every step of the calculation. Called from CoordinateAim
    when compensation_logging is enabled.

    Args:
        cycle: current cycle count (logs every 10th cycle to avoid spam)
        vx: robot forward velocity (m/s, field-relative)
        vy: robot lateral velocity (m/s, field-relative)
        raw_distance: straight-line distance to hub (meters)
        bearing_rad: angle from shooter to hub (radians, field frame)
        closing_speed: rate of closure (m/s, positive = getting closer)
        corrected_distance: distance after closing speed adjustment (meters)
        lead_deg: final lead angle applied to turret error (degrees)
    """
    if not DEBUG["compensation_logging"]:
        return
    # Log every 10th cycle (~5 Hz) to keep console readable
    if cycle % 10 != 0:
        return

    min_dist = CON_AUTO_SHOOT["min_distance"]
    gain = CON_AUTO_SHOOT["velocity_lead_gain"]
    enabled = CON_AUTO_SHOOT["velocity_lead_enabled"]

    # Recompute intermediates for display
    if raw_distance > min_dist and enabled:
        ux = math.cos(bearing_rad)
        uy = math.sin(bearing_rad)
        v_tangential = -vx * uy + vy * ux
        flight_time = get_flight_time(raw_distance)
        lead_m = v_tangential * flight_time
        raw_lead_deg = math.degrees(math.atan2(lead_m, raw_distance))
    else:
        v_tangential = 0.0
        flight_time = 0.0
        lead_m = 0.0
        raw_lead_deg = 0.0

    bearing_deg = math.degrees(bearing_rad)

    _log.info(
        f"[COMP] vel=({vx:.2f},{vy:.2f}) dist={raw_distance:.2f} "
        f"bearing={bearing_deg:.1f} cls={closing_speed:.2f} "
        f"| v_tan={v_tangential:.2f} flightT={flight_time:.3f} "
        f"leadM={lead_m:.3f} leadDeg={raw_lead_deg:.2f} "
        f"gain={gain:.2f} finalLead={lead_deg:.2f} "
        f"| rawDist={raw_distance:.2f} corrDist={corrected_distance:.2f}"
    )
