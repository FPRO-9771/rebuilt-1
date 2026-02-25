"""
Limelight vision provider.
Real hardware implementation using limelightlib-python.

Requires: pip install limelightlib-python
"""

import math
import time
from typing import List, Optional

from utils.logger import get_logger

from .vision import VisionProvider, VisionTarget

_log = get_logger("limelight")

# Only fetch from the Limelight this often (seconds).
# 10 Hz is plenty for AprilTag tracking and keeps the robot loop fast.
_REFRESH_INTERVAL = 0.05


class LimelightVisionProvider(VisionProvider):
    """
    Real Limelight implementation.
    Connects to a specific Limelight by hostname and reads AprilTag fiducial data.
    """

    def __init__(self, host: str):
        self._camera = None
        self._results_lib = None
        self._host = host
        self._cached_targets: List[VisionTarget] = []
        self._last_fetch = 0.0

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
            self._camera = None
        except Exception as e:
            _log.error(f"Failed to connect to Limelight at {host}: {e}")
            self._camera = None

    def _refresh(self) -> None:
        """Fetch new results from the Limelight if the cache is stale."""
        now = time.monotonic()
        if now - self._last_fetch < _REFRESH_INTERVAL:
            return

        self._last_fetch = now

        if not self._camera or not self._results_lib:
            self._cached_targets = []
            return

        try:
            result = self._camera.get_latest_results()
            parsed = self._results_lib.parse_results(result)
        except Exception as e:
            _log.debug(f"_refresh failed: {e}")
            self._cached_targets = []
            return

        if not parsed or not hasattr(parsed, "fiducialResults"):
            self._cached_targets = []
            return

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

        self._cached_targets = targets

    def get_target(self, tag_id: Optional[int] = None) -> Optional[VisionTarget]:
        """Get target data from cached Limelight fiducial results."""
        self._refresh()

        if not self._cached_targets:
            return None

        if tag_id is not None:
            for t in self._cached_targets:
                if t.tag_id == tag_id:
                    return t
            return None

        # Return closest target
        return min(self._cached_targets, key=lambda t: t.distance)

    def has_target(self, tag_id: Optional[int] = None) -> bool:
        return self.get_target(tag_id) is not None

    def get_all_targets(self) -> List[VisionTarget]:
        """Get all currently visible AprilTag targets."""
        self._refresh()
        return list(self._cached_targets)
