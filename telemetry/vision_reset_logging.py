"""
Breadcrumb logging for the B-button MegaTag1 hard pose reset.

The reset is a driver escape hatch -- when the driver presses B we want
a complete trail of what happened, every time, so a kid on the drive
team can answer "did the reset fire and why or why not?" by reading
the log.

The reset uses **MegaTag1** (pure AprilTag PnP, no gyro fusion) so it
is independent of the gyro -- the only way to escape a gyro-MT2
feedback loop where odom and MT2 have converged on a wrong but
self-consistent pose. It requires LIMELIGHT_RESET_MIN_TAGS visible
tags (default 2) to avoid single-tag PnP ambiguity, and it overrides
the **full** pose including yaw.

This logger is whitelisted in utils/logger.py so it always emits at
INFO level, even with auton_quiet_mode on. There is intentionally no
debug flag to forget to flip.

Lifecycle of one B press:
    log_armed()      -- fires immediately on press
    log_pending()    -- once every PENDING_LOG_PERIOD_LOOPS while waiting
    log_fired() OR log_timeout() -- exactly one of these, ever
"""

from constants.match import LIMELIGHT_RESET_MIN_TAGS
from constants.vision import CON_VISION
from handlers.limelight_helpers import get_bot_pose_estimate_wpi_blue_megatag1
from utils.logger import get_logger

_log = get_logger("vision_reset")

# Rate-limit "still waiting" lines so a 2 s timeout produces ~10 lines,
# not 100. The first pending log fires immediately after a B press
# because log_armed resets the counter to the trigger value.
_PENDING_LOG_PERIOD_LOOPS = 10
_pending_log_counter = 0


def log_armed(timeout_s: float) -> None:
    """Driver pressed B -- one-shot reset is now armed."""
    global _pending_log_counter
    # Force the next pending poll to log immediately so the driver gets
    # an instant readout of camera state on the press loop.
    _pending_log_counter = _PENDING_LOG_PERIOD_LOOPS
    _log.info(
        f"B PRESSED: hard reset armed, will fire on next "
        f"tag-visible loop within {timeout_s:.1f}s"
    )


def log_pending(odom_pose) -> None:
    """
    Called every loop while reset is pending. Polls each camera's MT1
    estimate (since the reset itself uses MT1) and shows whether each
    has enough tags to fire. Rate-limited internally.
    """
    global _pending_log_counter
    _pending_log_counter += 1
    if _pending_log_counter < _PENDING_LOG_PERIOD_LOOPS:
        return
    _pending_log_counter = 0

    parts = []
    for key, cam in CON_VISION["cameras"].items():
        mt1 = get_bot_pose_estimate_wpi_blue_megatag1(cam["nt_name"])
        if mt1 is None or mt1.tag_count < 1:
            parts.append(f"{key}=no_tags")
        else:
            status = (
                "READY"
                if mt1.tag_count >= LIMELIGHT_RESET_MIN_TAGS
                else f"need_{LIMELIGHT_RESET_MIN_TAGS}+_tags"
            )
            parts.append(
                f"{key}=mt1_tags{mt1.tag_ids}@{mt1.avg_tag_dist:.1f}m({status})"
            )

    _log.info(
        f"PENDING odom=({odom_pose.x:.2f},{odom_pose.y:.2f},"
        f"{odom_pose.rotation().degrees():.0f}) | {' | '.join(parts)}"
    )


def log_fired(cam_key, odom_before, mt2, applied_pose) -> None:
    """Reset successfully fired -- show before/after and which camera won."""
    _log.info(
        f"FIRED via {cam_key}: tags={mt2.tag_count} ids={mt2.tag_ids} "
        f"avg_dist={mt2.avg_tag_dist:.2f}m "
        f"avg_area={mt2.avg_tag_area:.3f} "
        f"lat={mt2.latency:.0f}ms | "
        f"odom_before=({odom_before.x:.2f},{odom_before.y:.2f},"
        f"{odom_before.rotation().degrees():.1f}) | "
        f"vision_raw=({mt2.pose.x:.2f},{mt2.pose.y:.2f},"
        f"{mt2.pose.rotation().degrees():.1f}) | "
        f"applied=({applied_pose.x:.2f},{applied_pose.y:.2f},"
        f"{applied_pose.rotation().degrees():.1f})"
    )


def log_timeout(timeout_s: float) -> None:
    """Reset timed out -- no camera saw any tags within the window."""
    _log.warning(
        f"TIMEOUT after {timeout_s:.1f}s -- no camera saw any tags. "
        f"Reset NOT applied; odometry unchanged."
    )
