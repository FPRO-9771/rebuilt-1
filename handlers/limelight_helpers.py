"""
LimelightHelpers -- NetworkTables-based helper for Limelight MegaTag2.

Provides static methods to read MegaTag2 bot-pose data and set robot
orientation, using the same NetworkTables keys as the official
LimelightHelpers (Java/C++).

NT table name must match the Limelight's configured name
(e.g. "limelight-shooter").
"""

from dataclasses import dataclass, field
from typing import Optional

import ntcore
from wpimath.geometry import Pose2d, Rotation2d
from wpimath.units import degreesToRadians


@dataclass
class PoseEstimate:
    """Result from MegaTag2 bot-pose estimation."""
    pose: Pose2d
    timestamp_seconds: float = 0.0
    latency: float = 0.0
    tag_count: int = 0
    tag_span: float = 0.0
    avg_tag_dist: float = 0.0
    avg_tag_area: float = 0.0
    raw_data: list = field(default_factory=list)


def _get_table(limelight_name: str) -> ntcore.NetworkTable:
    return ntcore.NetworkTableInstance.getDefault().getTable(limelight_name)


def get_bot_pose_estimate_wpi_blue_megatag2(
    limelight_name: str = "limelight",
) -> Optional[PoseEstimate]:
    """
    Read MegaTag2 bot-pose from NetworkTables (WPILib Blue origin).

    Returns None if no data is available or no tags are visible.
    """
    table = _get_table(limelight_name)
    data = table.getEntry("botpose_orb_wpiblue").getDoubleArray([])
    if len(data) < 11:
        return None

    x = data[0]
    y = data[1]
    yaw_deg = data[5]
    latency_ms = data[6]
    tag_count = int(data[7])
    tag_span = data[8]
    avg_tag_dist = data[9]
    avg_tag_area = data[10]

    if tag_count < 1:
        return None

    pose = Pose2d(x, y, Rotation2d(degreesToRadians(yaw_deg)))
    # NT timestamp is FPGA microseconds converted to seconds minus latency
    timestamp = (
        table.getEntry("botpose_orb_wpiblue")
        .getLastChange() / 1_000_000.0
        - latency_ms / 1000.0
    )

    return PoseEstimate(
        pose=pose,
        timestamp_seconds=timestamp,
        latency=latency_ms,
        tag_count=tag_count,
        tag_span=tag_span,
        avg_tag_dist=avg_tag_dist,
        avg_tag_area=avg_tag_area,
        raw_data=list(data),
    )


def set_robot_orientation(
    limelight_name: str,
    yaw_degrees: float,
    yaw_rate: float = 0.0,
    pitch_degrees: float = 0.0,
    pitch_rate: float = 0.0,
    roll_degrees: float = 0.0,
    roll_rate: float = 0.0,
) -> None:
    """
    Send robot orientation to the Limelight for MegaTag2.

    Must be called every loop so the Limelight can fuse IMU heading
    with its AprilTag detections.
    """
    table = _get_table(limelight_name)
    table.getEntry("robot_orientation_set").setDoubleArray([
        yaw_degrees,
        yaw_rate,
        pitch_degrees,
        pitch_rate,
        roll_degrees,
        roll_rate,
    ])


def get_tv(limelight_name: str = "limelight") -> bool:
    """Return True if the Limelight has a valid target (tv == 1)."""
    table = _get_table(limelight_name)
    return table.getEntry("tv").getDouble(0.0) >= 1.0


def get_tag_count(limelight_name: str = "limelight") -> int:
    """Return number of tags visible from the latest MegaTag2 result."""
    table = _get_table(limelight_name)
    data = table.getEntry("botpose_orb_wpiblue").getDoubleArray([])
    if len(data) >= 8:
        return int(data[7])
    return 0
