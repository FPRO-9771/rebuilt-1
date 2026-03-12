"""
Auto-aim SmartDashboard telemetry.
Publishes target lock status and debug diagnostics.
Called by AutoAim command -- all data passed in as arguments.
"""

from wpilib import SmartDashboard

from constants.debug import DEBUG


def init_auto_aim_keys():
    """Publish diagnostic keys at boot so Elastic can find them immediately."""
    SmartDashboard.putNumberArray("AutoAim/TagPriority", [])
    SmartDashboard.putNumber("AutoAim/LockedTagID", -1)
    SmartDashboard.putBoolean("AutoAim/HasTarget", False)
    SmartDashboard.putNumberArray("AutoAim/VisibleTags", [])


def publish_auto_aim(cycle, has_target, locked_tag_id, tag_priority,
                     visible_tag_ids):
    """Publish auto-aim telemetry. Rate-limited internally.

    Args:
        cycle: current cycle count (for rate limiting)
        has_target: whether a target is currently visible
        locked_tag_id: ID of the locked tag, or None
        tag_priority: ordered list of priority tag IDs
        visible_tag_ids: list of currently visible tag IDs
    """
    # Match-critical: target lock status (~5 Hz)
    if cycle % 10 == 1:
        SmartDashboard.putBoolean("AutoAim/HasTarget", has_target)
        SmartDashboard.putNumber(
            "AutoAim/LockedTagID",
            locked_tag_id if locked_tag_id is not None else -1,
        )

    # Debug-only: priority list and visible tags
    if not DEBUG["debug_telemetry"]:
        return
    if cycle % 10 == 1:
        SmartDashboard.putNumberArray("AutoAim/TagPriority", tag_priority)
    if cycle % 50 == 25:
        SmartDashboard.putNumberArray("AutoAim/VisibleTags", visible_tag_ids)


def publish_velocity_debug(cycle, vx, vy, lead_deg):
    """Publish velocity compensation debug data. Only when debug enabled."""
    if not DEBUG["debug_telemetry"]:
        return
    if cycle % 10 != 5:
        return
    SmartDashboard.putNumber("AutoAim/RobotVX", vx)
    SmartDashboard.putNumber("AutoAim/RobotVY", vy)
    SmartDashboard.putNumber("AutoAim/LeadDeg", lead_deg)
