"""
Per-cycle debug logging for drivetrain.vision_pose_correct().

Toggle with DEBUG["vision_pose_correct_logging"] in constants/debug.py.
Rate-limited by VISION_POSE_LOG_PERIOD_LOOPS in constants/vision.py
(default 10 loops = ~5 Hz at a 50 Hz robot loop).

Each emitted line shows BOTH the MT1 and MT2 bot-pose estimate for
one camera, regardless of which mode the soft correction is using.
The active source is marked in the line prefix:
    [mt2]      -- mt2 is active and fed its measurement this loop
    [mt1]      -- mt1 is active and fed its measurement this loop
    [mt2-REJ]  -- mt2 is active but had no tags (rejected, not fed)
    [mt1-REJ]  -- mt1 is active but had < min tags (rejected, not fed)

Showing both sources every cycle is the whole point of this logger:
it lets the team A/B the two estimates against odom in the same run,
on the same tags, so they can decide which one to trust on a given
field setup. Leave this logger ON during test sessions and OFF for
real matches -- zero extra NetworkTables bandwidth when off.
"""

from constants.debug import DEBUG
from constants.vision import (
    CON_VISION,
    VISION_MT1_MIN_TAGS,
    VISION_POSE_CORRECT_MODE,
    VISION_POSE_LOG_PERIOD_LOOPS,
)
from handlers.limelight_helpers import (
    get_bot_pose_estimate_wpi_blue_megatag1,
    get_bot_pose_estimate_wpi_blue_megatag2,
)
from utils.logger import get_logger

_log = get_logger("vpc")

_loop_counter = 0


def _enabled() -> bool:
    return DEBUG["vision_pose_correct_logging"]


def maybe_log_vision_correct(odom_pose) -> None:
    """
    Emit one debug block per camera, rate-limited.

    The drivetrain calls this once per soft-correction loop. We only
    actually touch NetworkTables on the log cycle (every
    VISION_POSE_LOG_PERIOD_LOOPS calls), so steady-state cost with
    logging off is a single boolean check.
    """
    global _loop_counter
    if not _enabled():
        return
    _loop_counter += 1
    if _loop_counter < VISION_POSE_LOG_PERIOD_LOOPS:
        return
    _loop_counter = 0

    for cam_key, cam in CON_VISION["cameras"].items():
        _log_one_camera(cam_key, cam["nt_name"], odom_pose)


def _format_pose(pose) -> str:
    return (
        f"({pose.x:.2f},{pose.y:.2f},"
        f"{pose.rotation().degrees():.1f})"
    )


def _log_one_camera(cam_key, nt_name, odom_pose) -> None:
    mt1 = get_bot_pose_estimate_wpi_blue_megatag1(nt_name)
    mt2 = get_bot_pose_estimate_wpi_blue_megatag2(nt_name)

    if mt1 is None and mt2 is None:
        _log.info(f"VPC {cam_key}: no tags")
        return

    # Figure out which source is active and whether it would have fed
    # a measurement this loop. Must mirror the logic in
    # CommandSwerveDrivetrain._read_vision_estimate_for_mode so the log
    # line and the actual estimator input stay in sync.
    mode = VISION_POSE_CORRECT_MODE
    if mode == "mt1":
        active = mt1
        rejected = mt1 is None or mt1.tag_count < VISION_MT1_MIN_TAGS
    else:
        active = mt2
        rejected = mt2 is None or mt2.tag_count < 1

    prefix = f"[{mode}-REJ]" if rejected else f"[{mode}]"

    # Tag metadata -- both sources see the same tags, so display
    # whichever is available.
    ref = mt1 if mt1 is not None else mt2

    mt1_str = _format_pose(mt1.pose) if mt1 is not None else "n/a"
    mt2_str = _format_pose(mt2.pose) if mt2 is not None else "n/a"

    if rejected or active is None:
        dxy_str = "dxy=rejected"
    else:
        dx = active.pose.x - odom_pose.x
        dy = active.pose.y - odom_pose.y
        dxy_str = f"dxy=({dx:+.2f},{dy:+.2f})"

    _log.info(
        f"VPC {cam_key} {prefix} | tags={ref.tag_count} ids={ref.tag_ids} "
        f"avg_dist={ref.avg_tag_dist:.2f}m "
        f"avg_area={ref.avg_tag_area:.3f} "
        f"lat={ref.latency:.0f}ms | "
        f"mt2={mt2_str} mt1={mt1_str} | "
        f"odom={_format_pose(odom_pose)} {dxy_str}"
    )
