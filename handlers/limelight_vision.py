"""
Limelight vision provider.
Real hardware implementation using limelightlib-python.

Requires: pip install limelightlib-python
"""

import math
from typing import List, Optional

from utils.logger import get_logger

from .vision import VisionProvider, VisionTarget

_log = get_logger("limelight")


class LimelightVisionProvider(VisionProvider):
    """
    Real Limelight implementation.
    Connects to a specific Limelight by hostname and reads AprilTag fiducial data.
    """

    def __init__(self, host: str):
        self._camera = None
        self._results_lib = None

        try:
            import limelight
            import limelightresults

            self._results_lib = limelightresults

            self._camera = limelight.Limelight(host)
            _log.info(f"Connected to Limelight at {host}")
        except ImportError as e:
            _log.error(f"Limelight library not installed: {e}")
        except Exception as e:
            _log.error(f"Failed to connect to Limelight at {host}: {e}")

    def get_target(self, tag_id: Optional[int] = None) -> Optional[VisionTarget]:
        """Get target data from Limelight fiducial results."""
        if not self._camera or not self._results_lib:
            return None

        try:
            result = self._camera.get_latest_results()
            parsed = self._results_lib.parse_results(result)
        except Exception as e:
            _log.debug(f"get_target failed: {e}")
            return None

        if not parsed or not hasattr(parsed, "fiducialResults"):
            return None

        fiducials = parsed.fiducialResults
        if not fiducials:
            return None

        # Find the requested tag, or pick the closest one
        best = None
        best_distance = float("inf")

        for fid in fiducials:
            fid_id = int(fid.fiducial_id)

            # Compute distance from camera-space position
            if hasattr(fid, "target_pose_camera_space"):
                pose = fid.target_pose_camera_space
                dx = pose[0] if len(pose) > 0 else 0
                dy = pose[1] if len(pose) > 1 else 0
                dz = pose[2] if len(pose) > 2 else 0
                dist = math.sqrt(dx * dx + dy * dy + dz * dz)
            else:
                dist = 0.0

            if tag_id is not None and fid_id != tag_id:
                continue

            if dist < best_distance:
                best_distance = dist
                best = VisionTarget(
                    tag_id=fid_id,
                    tx=fid.target_x_degrees if hasattr(fid, "target_x_degrees") else 0,
                    ty=fid.target_y_degrees if hasattr(fid, "target_y_degrees") else 0,
                    distance=dist,
                    yaw=fid.target_yaw if hasattr(fid, "target_yaw") else 0,
                )

        return best

    def has_target(self, tag_id: Optional[int] = None) -> bool:
        return self.get_target(tag_id) is not None

    def get_all_targets(self) -> List[VisionTarget]:
        """Get all currently visible AprilTag targets."""
        if not self._camera or not self._results_lib:
            return []

        try:
            result = self._camera.get_latest_results()
            parsed = self._results_lib.parse_results(result)
        except Exception as e:
            _log.debug(f"get_all_targets failed: {e}")
            return []

        if not parsed or not hasattr(parsed, "fiducialResults"):
            return []

        targets = []
        for fid in parsed.fiducialResults:
            if hasattr(fid, "target_pose_camera_space"):
                pose = fid.target_pose_camera_space
                dx = pose[0] if len(pose) > 0 else 0
                dy = pose[1] if len(pose) > 1 else 0
                dz = pose[2] if len(pose) > 2 else 0
                dist = math.sqrt(dx * dx + dy * dy + dz * dz)
            else:
                dist = 0.0

            targets.append(VisionTarget(
                tag_id=int(fid.fiducial_id),
                tx=fid.target_x_degrees if hasattr(fid, "target_x_degrees") else 0,
                ty=fid.target_y_degrees if hasattr(fid, "target_y_degrees") else 0,
                distance=dist,
                yaw=fid.target_yaw if hasattr(fid, "target_yaw") else 0,
            ))

        return targets
