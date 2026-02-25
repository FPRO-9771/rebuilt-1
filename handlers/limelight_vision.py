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
        self._host = host

        _log.info(f"Initializing Limelight at {host}...")

        try:
            import limelight
            import limelightresults

            _log.debug("limelightlib-python imported OK")
            self._results_lib = limelightresults

            self._camera = limelight.Limelight(host)
            _log.debug(f"Limelight object created for {host}")

            self._camera.pipeline_switch(0)  # AprilTag detection pipeline
            _log.debug("Pipeline switched to 0 (AprilTag)")

            self._camera.enable_websocket()
            _log.info(f"Connected to Limelight at {host} - websocket enabled")
        except ImportError as e:
            _log.error(f"Limelight library not installed: {e}")
        except Exception as e:
            _log.error(f"Failed to connect to Limelight at {host}: {e}")

    def get_target(self, tag_id: Optional[int] = None) -> Optional[VisionTarget]:
        """Get target data from Limelight fiducial results."""
        if not self._camera or not self._results_lib:
            _log.debug("get_target: no camera or results lib - skipping")
            return None

        try:
            result = self._camera.get_latest_results()
            parsed = self._results_lib.parse_results(result)
        except Exception as e:
            _log.warning(f"get_target: failed to read results: {e}")
            return None

        if not parsed or not hasattr(parsed, "fiducialResults"):
            _log.debug("get_target: no parsed results or missing fiducialResults")
            return None

        fiducials = parsed.fiducialResults
        if not fiducials:
            _log.debug("get_target: fiducialResults is empty - no tags visible")
            return None

        _log.debug(
            f"get_target: {len(fiducials)} tag(s) visible - "
            f"IDs: {[int(f.fiducial_id) for f in fiducials]}"
        )

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

        if best:
            _log.debug(
                f"get_target: selected tag {best.tag_id} - "
                f"tx={best.tx:.1f}° dist={best.distance:.2f}m yaw={best.yaw:.1f}°"
            )
        else:
            _log.debug(
                f"get_target: requested tag_id={tag_id} not found among visible tags"
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
