"""
Vision system abstraction.
Provides testable interface for Limelight camera data.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict
import math


@dataclass
class VisionTarget:
    """Standardized vision target data."""
    tag_id: int
    tx: float           # Horizontal offset (degrees, negative = left)
    ty: float           # Vertical offset (degrees)
    distance: float     # Distance to target (meters)
    yaw: float          # Target rotation
    is_valid: bool = True


class VisionProvider(ABC):
    """Abstract interface for vision systems."""

    @abstractmethod
    def get_target(self, tag_id: Optional[int] = None) -> Optional[VisionTarget]:
        """Get vision data for a specific tag or closest tag."""
        pass

    @abstractmethod
    def has_target(self, tag_id: Optional[int] = None) -> bool:
        """Check if a target is visible."""
        pass


class LimelightVisionProvider(VisionProvider):
    """
    Real Limelight implementation using limelight-python.
    Discovers the Limelight on the network and reads AprilTag fiducial data.

    Requires: pip install limelight-python
    """

    def __init__(self):
        self._camera = None
        self._limelight_lib = None
        self._results_lib = None

        try:
            import limelight
            import limelightresults
            self._limelight_lib = limelight
            self._results_lib = limelightresults

            discovered = limelight.discover_limelights()
            if discovered:
                self._camera = limelight.Limelight(discovered[0])
                self._camera.enable_websocket()
        except (ImportError, Exception):
            # Graceful fallback — no camera available
            self._camera = None

    def get_target(self, tag_id: Optional[int] = None) -> Optional[VisionTarget]:
        """Get target data from Limelight fiducial results."""
        if not self._camera or not self._results_lib:
            return None

        try:
            result = self._camera.get_latest_results()
            parsed = self._results_lib.parse_results(result)
        except Exception:
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


class MockVisionProvider(VisionProvider):
    """Mock implementation for testing."""

    def __init__(self):
        self._targets: Dict[int, VisionTarget] = {}
        self._default_target: Optional[VisionTarget] = None
        self._query_history: list[Optional[int]] = []

    def get_target(self, tag_id: Optional[int] = None) -> Optional[VisionTarget]:
        self._query_history.append(tag_id)
        if tag_id and tag_id in self._targets:
            return self._targets[tag_id]
        return self._default_target

    def has_target(self, tag_id: Optional[int] = None) -> bool:
        return self.get_target(tag_id) is not None

    # --- Test helpers ---

    def set_target(self, target: VisionTarget) -> None:
        """Set a specific target to be returned."""
        self._targets[target.tag_id] = target
        if self._default_target is None:
            self._default_target = target

    def set_default_target(self, target: Optional[VisionTarget]) -> None:
        """Set the default target (returned when no tag_id specified)."""
        self._default_target = target

    def simulate_target_left(self, tag_id: int, offset_degrees: float = 10, distance: float = 2.0) -> None:
        """Simulate a target to the left of center."""
        self.set_target(VisionTarget(
            tag_id=tag_id,
            tx=-abs(offset_degrees),
            ty=0,
            distance=distance,
            yaw=0,
        ))

    def simulate_target_right(self, tag_id: int, offset_degrees: float = 10, distance: float = 2.0) -> None:
        """Simulate a target to the right of center."""
        self.set_target(VisionTarget(
            tag_id=tag_id,
            tx=abs(offset_degrees),
            ty=0,
            distance=distance,
            yaw=0,
        ))

    def simulate_target_centered(self, tag_id: int, distance: float = 1.0) -> None:
        """Simulate a perfectly centered target."""
        self.set_target(VisionTarget(
            tag_id=tag_id,
            tx=0,
            ty=0,
            distance=distance,
            yaw=0,
        ))

    def simulate_no_target(self) -> None:
        """Simulate no visible targets."""
        self._targets.clear()
        self._default_target = None

    def clear_history(self) -> None:
        self._query_history.clear()
