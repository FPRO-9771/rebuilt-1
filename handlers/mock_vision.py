"""
Mock vision provider for testing.
Lets tests simulate targets at specific positions without real hardware.
"""

from typing import Dict, Optional

from .vision import VisionProvider, VisionTarget


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
