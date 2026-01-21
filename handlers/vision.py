"""
Vision system abstraction.
Provides testable interface for Limelight camera data.

TODO: Implement LimelightVisionProvider when Limelight is set up.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict


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
    Real Limelight implementation.

    TODO: Implement when Limelight is connected.
    Requires: pip install limelight-python
    """

    def __init__(self):
        # TODO: Initialize Limelight connection
        # import limelight
        # discovered = limelight.discover_limelights()
        # self._camera = limelight.Limelight(discovered[0]) if discovered else None
        self._camera = None

    def get_target(self, tag_id: Optional[int] = None) -> Optional[VisionTarget]:
        """Get target data from Limelight."""
        if not self._camera:
            return None

        # TODO: Implement actual Limelight data parsing
        # result = self._camera.get_latest_results()
        # parsed = limelightresults.parse_results(result)
        # ... process and return VisionTarget
        return None

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
