"""
Limelight vision provider.
Real hardware implementation using limelightlib-python.

All network I/O (connection and polling) runs in a background thread
so the robot loop is never blocked by a slow or missing Limelight.

Requires: pip install limelightlib-python
"""

import math
import threading
import time
from typing import List, Optional

from utils.logger import get_logger

from .vision import VisionProvider, VisionTarget

_log = get_logger("limelight")

# How often the background thread polls for new results (seconds).
_POLL_INTERVAL = 0.05  # 20 Hz


class LimelightVisionProvider(VisionProvider):
    """
    Real Limelight implementation.
    Connects to a specific Limelight by hostname and reads AprilTag fiducial data.
    All network I/O happens in a daemon thread -- public methods return cached data.
    """

    def __init__(self, host: str):
        self._host = host
        self._cached_targets: List[VisionTarget] = []
        self._lock = threading.Lock()
        # Freshness tracking: detect when the Limelight returns a new frame
        # vs the same frame repeated. _last_signature stores (tag_id, tx)
        # tuples from the previous poll; _last_fresh_time is the monotonic
        # time when data actually changed.
        self._last_signature: tuple = ()
        self._last_fresh_time: float = 0.0
        self._stale_count: int = 0  # consecutive polls with unchanged data

        _log.info(f"Initializing Limelight at {host} (background)...")

        thread = threading.Thread(
            target=self._run, args=(host,), daemon=True
        )
        thread.start()

    # ------------------------------------------------------------------
    # Background thread
    # ------------------------------------------------------------------

    def _run(self, host: str):
        """Connect then poll forever. Runs in a daemon thread."""
        camera, results_lib = self._connect(host)
        if camera is None:
            return

        while True:
            try:
                result = camera.get_latest_results()
                parsed = results_lib.parse_results(result)
            except Exception as e:
                _log.debug(f"Poll failed for {host}: {e}")
                with self._lock:
                    self._cached_targets = []
                time.sleep(_POLL_INTERVAL)
                continue

            targets = self._parse_targets(parsed)
            now = time.monotonic()

            # Build a signature from tag IDs and tx values to detect
            # whether this is actually a new frame or the same one
            # repeated by get_latest_results().
            sig = tuple((t.tag_id, round(t.tx, 4)) for t in targets)
            if sig != self._last_signature:
                self._last_signature = sig
                self._last_fresh_time = now
                self._stale_count = 0
                fresh = "NEW"
            else:
                self._stale_count += 1
                fresh = f"stale x{self._stale_count}"
            # Stamp targets with the time data ACTUALLY changed,
            # not the poll time. This makes age= meaningful.
            for t in targets:
                t.timestamp = self._last_fresh_time

            with self._lock:
                self._cached_targets = targets

            # if targets:
            #     tx_vals = " ".join(f"{t.tag_id}:{t.tx:.2f}" for t in targets)
            #     _log.debug(f"[LL] {fresh} {tx_vals}")

            time.sleep(_POLL_INTERVAL)

    @staticmethod
    def _connect(host: str):
        """Blocking connect -- returns (camera, results_lib) or (None, None)."""
        try:
            import limelight
            import limelightresults

            _log.debug("limelightlib-python imported OK")

            camera = limelight.Limelight(host)
            _log.debug(f"Limelight object created for {host}")

            camera.pipeline_switch(0)  # AprilTag detection pipeline
            _log.debug("Pipeline switched to 0 (AprilTag)")

            camera.enable_websocket()
            _log.info(f"Connected to Limelight at {host} -- websocket enabled")
            return camera, limelightresults
        except ImportError as e:
            _log.error(f"Limelight library not installed: {e}")
        except Exception as e:
            _log.error(f"Failed to connect to Limelight at {host}: {e}")
        return None, None

    @staticmethod
    def _parse_targets(parsed) -> List[VisionTarget]:
        """Convert parsed Limelight results into VisionTarget list."""
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

    # ------------------------------------------------------------------
    # Public API (called from the robot loop -- never blocks)
    # ------------------------------------------------------------------

    def get_target(self, tag_id: Optional[int] = None) -> Optional[VisionTarget]:
        """Get target data from cached Limelight fiducial results."""
        with self._lock:
            targets = list(self._cached_targets)

        if not targets:
            return None

        if tag_id is not None:
            for t in targets:
                if t.tag_id == tag_id:
                    return t
            return None

        return min(targets, key=lambda t: t.distance)

    def has_target(self, tag_id: Optional[int] = None) -> bool:
        return self.get_target(tag_id) is not None

    def get_all_targets(self) -> List[VisionTarget]:
        """Get all currently visible AprilTag targets."""
        with self._lock:
            return list(self._cached_targets)
