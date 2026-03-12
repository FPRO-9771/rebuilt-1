"""
Auto-aim SmartDashboard telemetry.
Publishes target lock status and debug diagnostics.
Called by AutoAim command -- all data passed in as arguments.
"""

from wpilib import SmartDashboard

from constants.debug import DEBUG


def init_auto_aim_keys():
    """Publish diagnostic keys at boot so Elastic can find them immediately."""
    SmartDashboard.putBoolean("AutoAim/OnTarget", False)
    if DEBUG["debug_telemetry"]:
        SmartDashboard.putBoolean("AutoAim/HasTarget", False)
        SmartDashboard.putNumber("AutoAim/LockedTagID", -1)


def publish_auto_aim(cycle, has_target, locked_tag_id, on_target=False):
    """Publish auto-aim telemetry. Rate-limited internally.

    Args:
        cycle: current cycle count (for rate limiting)
        has_target: whether a target is currently visible
        locked_tag_id: ID of the locked tag, or None
        on_target: whether turret is aligned within tolerance
    """
    # Match-critical: on-target only (~5 Hz)
    if cycle % 10 == 1:
        SmartDashboard.putBoolean("AutoAim/OnTarget", on_target)

    # Debug-only: everything else
    if not DEBUG["debug_telemetry"]:
        return
    if cycle % 10 == 1:
        SmartDashboard.putBoolean("AutoAim/HasTarget", has_target)
        SmartDashboard.putNumber(
            "AutoAim/LockedTagID",
            locked_tag_id if locked_tag_id is not None else -1,
        )


def publish_velocity_debug(cycle, vx, vy, lead_deg):
    """Publish velocity compensation debug data. Only when debug enabled."""
    if not DEBUG["debug_telemetry"]:
        return
    if cycle % 10 != 5:
        return
    SmartDashboard.putNumber("AutoAim/RobotVX", vx)
    SmartDashboard.putNumber("AutoAim/RobotVY", vy)
    SmartDashboard.putNumber("AutoAim/LeadDeg", lead_deg)
