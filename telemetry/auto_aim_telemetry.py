"""
Auto-aim SmartDashboard telemetry.
Publishes on-target status and debug diagnostics.
Called by CoordinateAim command -- all data passed in as arguments.
"""

from wpilib import SmartDashboard

from constants.debug import DEBUG


def init_auto_aim_keys():
    """Publish diagnostic keys at boot so Elastic can find them immediately."""
    SmartDashboard.putBoolean("AutoAim/OnTarget", False)
    if DEBUG["debug_telemetry"]:
        SmartDashboard.putNumber("AutoAim/ErrorDeg", 0.0)
        SmartDashboard.putNumber("AutoAim/DistanceM", 0.0)


def publish_auto_aim(cycle, on_target, error_deg=0.0, distance_m=0.0):
    """Publish auto-aim telemetry. Rate-limited internally.

    Args:
        cycle: current cycle count (for rate limiting)
        on_target: whether turret is aligned within tolerance
        error_deg: current turret error in degrees
        distance_m: distance to target in meters
    """
    # Match-critical: on-target only (~5 Hz)
    if cycle % 10 == 1:
        SmartDashboard.putBoolean("AutoAim/OnTarget", on_target)

    # Debug-only: everything else
    if not DEBUG["debug_telemetry"]:
        return
    if cycle % 10 == 1:
        SmartDashboard.putNumber("AutoAim/ErrorDeg", error_deg)
        SmartDashboard.putNumber("AutoAim/DistanceM", distance_m)


def publish_velocity_debug(cycle, vx, vy, lead_deg):
    """Publish velocity compensation debug data. Only when debug enabled."""
    if not DEBUG["debug_telemetry"]:
        return
    if cycle % 10 != 5:
        return
    SmartDashboard.putNumber("AutoAim/RobotVX", vx)
    SmartDashboard.putNumber("AutoAim/RobotVY", vy)
    SmartDashboard.putNumber("AutoAim/LeadDeg", lead_deg)


# ---- Aim geometry dashboard (toggleable) ----

def init_aim_dashboard_keys():
    """Publish aim geometry keys at boot so Elastic can find them."""
    if not DEBUG["auto_aim_dashboard"]:
        return
    SmartDashboard.putNumber("AimDash/ShooterToHubM", 0.0)
    SmartDashboard.putNumber("AimDash/BearingToHubDeg", 0.0)


def publish_aim_dashboard(cycle, distance_m, bearing_deg):
    """Publish aim geometry for testing pose estimation and aiming.

    Shows the computed distance from the shooter (with offsets) to the Hub
    and the bearing from robot front to the Hub. Updated at ~2 Hz.

    Toggle with DEBUG["auto_aim_dashboard"] in constants/debug.py.

    Args:
        cycle: current cycle count (for rate limiting)
        distance_m: distance from shooter to Hub (meters, includes offsets)
        bearing_deg: angle from robot front to Hub (degrees, + = left)
    """
    if not DEBUG["auto_aim_dashboard"]:
        return
    if cycle % 25 != 0:
        return
    SmartDashboard.putNumber("AimDash/ShooterToHubM", round(distance_m, 2))
    SmartDashboard.putNumber("AimDash/BearingToHubDeg", round(bearing_deg, 1))
