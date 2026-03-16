"""
Movement compensation for auto-aim.
Computes aiming corrections for robot motion while shooting.

Two independent corrections:
  - Tracking: compensate for robot velocity so turret stays pointed at target
  - Lead: aim ahead so the ball arrives at the target correctly

Pure math -- no subsystem dependencies, easily testable.
"""

import math

from calculations.velocity_lead import compute_velocity_lead


def compute_movement_correction(vx, vy, distance_m, config):
    """Compute aiming corrections for robot movement.

    Args:
        vx: robot forward velocity (m/s, field-relative)
        vy: robot lateral velocity (m/s, field-relative)
        distance_m: distance to target (meters)
        config: CON_SHOOTER dict with velocity_ff_gain and velocity_lead_enabled

    Returns:
        (tracking_correction_deg, lead_correction_deg) tuple.
        Both are in degrees, to be ADDED to the turret error.
    """
    # Tracking correction: feedforward to keep turret pointed at target
    # while the robot moves laterally. Uses vy (lateral component).
    tracking_correction_deg = vy * config["turret_velocity_ff_gain"]

    # Lead correction: aim ahead so ball arrives on target
    lead_correction_deg = 0.0
    if config["velocity_lead_enabled"] and distance_m > 0.5:
        lead_correction_deg, _ = compute_velocity_lead(vy, distance_m)

    return tracking_correction_deg, lead_correction_deg
