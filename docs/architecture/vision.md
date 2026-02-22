# Vision System (Limelight)

**Team 9771 FPRO - 2026**

This doc covers using Limelight cameras for AprilTag detection and alignment, including the testable vision abstraction layer.

> **When to read this:** You're working with Limelight vision for auto alignment, teleop assist, or any vision use.

---

## Table of Contents

1. [What Limelight Provides](#1-what-limelight-provides)
2. [How We Used It in 2025](#2-how-we-used-it-in-2025)
3. [Configuration for Vision](#3-configuration-for-vision)
4. [Making Vision Testable (NEW for 2026)](#4-making-vision-testable-new-for-2026)
5. [Testing Vision-Based Commands](#5-testing-vision-based-commands)
6. [Tips for Vision Testing](#6-tips-for-vision-testing)

---

## 1. What Limelight Provides

The Limelight camera detects AprilTags and provides:

| Field | Description |
|-------|-------------|
| `tag_id` | Which AprilTag was detected (e.g., 20 = blue reef left) |
| `tx` | Horizontal offset in degrees (negative = target left of center) |
| `ty` | Vertical offset in degrees |
| `distance` | 3D distance to target in meters |
| `yaw` | Target's rotation relative to camera |
| `pitch`, `roll` | Target's orientation |
| `x_pos`, `y_pos`, `z_pos` | Target position in camera space |

---

## 2. How We Used It in 2025

**LimelightHandler** (`handlers/limelight_handler.py`) wrapped the limelight library:

```python
# handlers/limelight_handler.py (simplified from phoenix-v1)

import math
import limelight
import limelightresults

class LimelightHandler:
    def __init__(self, debug=True):
        # Auto-discover Limelight on network
        discovered = limelight.discover_limelights(debug=debug)
        if discovered:
            self.limelight = limelight.Limelight(discovered[0])
            self.limelight.pipeline_switch(0)  # AprilTag pipeline
            self.limelight.enable_websocket()
        else:
            self.limelight = None
            print("WARNING: No Limelight found!")

    def get_target_data(self, target_tag_id=None):
        """Get processed data for a specific AprilTag or closest one."""
        if not self.limelight:
            return None

        result = self.limelight.get_latest_results()
        parsed = limelightresults.parse_results(result)

        if not parsed or not parsed.fiducialResults:
            return None

        # Find the requested tag, or closest if not specified
        selected = None
        if target_tag_id:
            for tag in parsed.fiducialResults:
                if tag.fiducial_id == target_tag_id:
                    selected = tag
                    break

        if not selected:
            # Find closest tag
            closest_dist = float('inf')
            for tag in parsed.fiducialResults:
                pos = tag.target_pose_camera_space
                dist = math.sqrt(pos[0]**2 + pos[1]**2 + pos[2]**2)
                if dist < closest_dist:
                    closest_dist = dist
                    selected = tag

        if not selected:
            return None

        # Build clean data dict
        pos = selected.target_pose_camera_space
        return {
            'tag_id': selected.fiducial_id,
            'tx': selected.target_x_degrees,      # Horizontal offset
            'ty': selected.target_y_degrees,      # Vertical offset
            'distance': math.sqrt(pos[0]**2 + pos[1]**2 + pos[2]**2),
            'yaw': pos[4],
            'pitch': pos[3],
            'roll': pos[5],
            'x_pos': pos[0],
            'y_pos': pos[1],
            'z_pos': pos[2],
        }
```

**AutonDrive** used the handler to align to AprilTags:

```python
# autonomous/auton_drive.py (simplified from phoenix-v1)

class AutonDrive(SubsystemBase):
    def __init__(self, drivetrain, limelight_handler):
        self.drivetrain = drivetrain
        self.limelight = limelight_handler

    def align_to_tag(self, target_tag_id) -> Command:
        """Align robot to face an AprilTag."""

        class AlignCommand(Command):
            def __init__(self, outer, tag_id):
                super().__init__()
                self.outer = outer
                self.tag_id = tag_id
                self.on_target = False

            def execute(self):
                data = self.outer.limelight.get_target_data(self.tag_id)
                if not data:
                    return  # Lost target

                # Calculate drive corrections from vision data
                # tx > 0 means target is to the right, so rotate right (negative)
                rotation = -data['tx'] * 0.1  # P gain for rotation

                # distance > target means move forward
                speed_x = (data['distance'] - 1.0) * 0.5  # P gain, target 1m

                # Strafe based on tx to center horizontally
                speed_y = -data['tx'] * 0.05

                self.outer.drive_robot(rotation, speed_x, speed_y)

                # Check if on target
                self.on_target = (
                    abs(data['tx']) < 2.0 and      # Within 2 degrees
                    abs(data['distance'] - 1.0) < 0.1  # Within 10cm of target
                )

            def isFinished(self):
                return self.on_target

            def end(self, interrupted):
                self.outer.drive_robot(0, 0, 0)

        return AlignCommand(self, target_tag_id)
```

---

## 3. Configuration for Vision

```python
# autonomous/auton_constants.py

# AprilTag IDs by field position (2025 Reefscape)
APRILTAG_IDS = {
    "blue_left": {"score": 20, "intake": 13, "score2": 19},
    "blue_center": {"score": 21},
    "blue_right": {"score": 22, "intake": 12, "score2": 17},
    "red_left": {"score": 11, "intake": 1, "score2": 6},
    "red_center": {"score": 10},
    "red_right": {"score": 9, "intake": 2, "score2": 8},
}

# Multipliers to calibrate vision data to real-world
# (these may need tuning per-camera mount)
LL_DATA_SETTINGS = {
    "yaw": {"multiplier": 0.115},
    "tx": {"multiplier": 0.222},
    "distance": {},  # No adjustment needed
}

# Driving behavior based on vision
DRIVING = {
    "speed_x": {
        "max": 3.0,
        "multiplier": 0.5,
        "target_tolerance": 0.3,  # meters
    },
    "speed_y": {
        "max": 1.5,
        "multiplier": 0.4,
        "target_tolerance": 0.5,  # degrees tx
    },
    "rotation": {
        "max": 0.8,
        "multiplier": 0.2,
        "target_tolerance": 0.08,  # degrees yaw
    },
}
```

---

## 4. Making Vision Testable (NEW for 2026)

The problem: We couldn't test vision-based commands without a real Limelight and AprilTags.

**Solution: Vision Abstraction Layer**

```python
# handlers/vision.py

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass

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
    """Real Limelight implementation."""

    def __init__(self):
        import limelight
        import limelightresults
        self._ll = limelight
        self._llr = limelightresults

        discovered = limelight.discover_limelights()
        if discovered:
            self._camera = limelight.Limelight(discovered[0])
            self._camera.pipeline_switch(0)
            self._camera.enable_websocket()
        else:
            self._camera = None

    def get_target(self, tag_id: Optional[int] = None) -> Optional[VisionTarget]:
        if not self._camera:
            return None

        result = self._camera.get_latest_results()
        parsed = self._llr.parse_results(result)

        if not parsed or not parsed.fiducialResults:
            return None

        # Find requested tag or closest
        import math
        selected = None
        closest_dist = float('inf')

        for tag in parsed.fiducialResults:
            if tag_id and tag.fiducial_id == tag_id:
                selected = tag
                break
            pos = tag.target_pose_camera_space
            dist = math.sqrt(pos[0]**2 + pos[1]**2 + pos[2]**2)
            if dist < closest_dist:
                closest_dist = dist
                selected = tag

        if not selected:
            return None

        pos = selected.target_pose_camera_space
        return VisionTarget(
            tag_id=selected.fiducial_id,
            tx=selected.target_x_degrees,
            ty=selected.target_y_degrees,
            distance=math.sqrt(pos[0]**2 + pos[1]**2 + pos[2]**2),
            yaw=pos[4],
        )

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
            tx=-abs(offset_degrees),  # Negative = left
            ty=0,
            distance=distance,
            yaw=0,
        ))

    def simulate_target_right(self, tag_id: int, offset_degrees: float = 10, distance: float = 2.0) -> None:
        """Simulate a target to the right of center."""
        self.set_target(VisionTarget(
            tag_id=tag_id,
            tx=abs(offset_degrees),  # Positive = right
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
```

### Factory for Vision Provider

```python
# handlers/__init__.py

from .vision import VisionProvider, LimelightVisionProvider, MockVisionProvider

_use_mock_vision = False
_mock_provider: Optional[MockVisionProvider] = None

def set_mock_vision_mode(enabled: bool) -> None:
    global _use_mock_vision, _mock_provider
    _use_mock_vision = enabled
    if enabled:
        _mock_provider = MockVisionProvider()

def get_vision_provider() -> VisionProvider:
    if _use_mock_vision:
        return _mock_provider
    return LimelightVisionProvider()

def get_mock_vision() -> MockVisionProvider:
    """Get the mock provider for test setup. Only call after set_mock_vision_mode(True)."""
    if not _mock_provider:
        raise RuntimeError("Mock vision not enabled. Call set_mock_vision_mode(True) first.")
    return _mock_provider
```

### Updated AutonDrive (uses abstraction)

```python
# autonomous/auton_drive.py (updated for testability)

from handlers import get_vision_provider

class AutonDrive(SubsystemBase):
    def __init__(self, drivetrain, vision_provider=None):
        self.drivetrain = drivetrain
        self.vision = vision_provider or get_vision_provider()

    def align_to_tag(self, target_tag_id: int) -> Command:
        class AlignCommand(Command):
            def __init__(self, outer, tag_id):
                super().__init__()
                self.outer = outer
                self.tag_id = tag_id

            def execute(self):
                target = self.outer.vision.get_target(self.tag_id)
                if not target:
                    return

                # tx positive = target right, so rotate right (negative rate)
                rotation = -target.tx * 0.1
                speed_x = (target.distance - 1.0) * 0.5
                speed_y = -target.tx * 0.05

                self.outer.drive_robot(rotation, speed_x, speed_y)

            def isFinished(self):
                target = self.outer.vision.get_target(self.tag_id)
                if not target:
                    return True  # Lost target
                return abs(target.tx) < 2.0 and abs(target.distance - 1.0) < 0.1

            def end(self, interrupted):
                self.outer.drive_robot(0, 0, 0)

        return AlignCommand(self, target_tag_id)
```

---

## 5. Testing Vision-Based Commands

Now the powerful part - testing alignment without hardware:

```python
# tests/test_vision_alignment.py

import pytest
from handlers import set_mock_vision_mode, get_mock_vision
from handlers.vision import VisionTarget
from hardware import set_mock_mode
from autonomous.auton_drive import AutonDrive

@pytest.fixture
def setup_mocks():
    """Enable all mocks for testing."""
    set_mock_mode(True)
    set_mock_vision_mode(True)
    yield
    set_mock_mode(False)
    set_mock_vision_mode(False)

@pytest.fixture
def auton_drive(setup_mocks):
    """Create AutonDrive with mock drivetrain and vision."""
    from subsystems.drivetrain import Drivetrain
    drivetrain = Drivetrain()  # Will use mock motors
    return AutonDrive(drivetrain)


def test_target_left_rotates_left(auton_drive):
    """When target is left of center, robot should rotate left."""
    vision = get_mock_vision()

    # Target is 15 degrees to the LEFT
    vision.simulate_target_left(tag_id=20, offset_degrees=15, distance=2.0)

    cmd = auton_drive.align_to_tag(20)
    cmd.initialize()
    cmd.execute()

    # tx = -15 (left), so rotation should be -(-15) * 0.1 = +1.5 (rotate left/CCW)
    # Check the drivetrain received positive rotation
    assert auton_drive.drivetrain.last_rotation > 0, \
        "Should rotate left (positive) when target is left of center"


def test_target_right_rotates_right(auton_drive):
    """When target is right of center, robot should rotate right."""
    vision = get_mock_vision()

    # Target is 15 degrees to the RIGHT
    vision.simulate_target_right(tag_id=20, offset_degrees=15, distance=2.0)

    cmd = auton_drive.align_to_tag(20)
    cmd.initialize()
    cmd.execute()

    # tx = +15 (right), so rotation should be -(+15) * 0.1 = -1.5 (rotate right/CW)
    assert auton_drive.drivetrain.last_rotation < 0, \
        "Should rotate right (negative) when target is right of center"


def test_far_target_drives_forward(auton_drive):
    """When target is far, robot should drive forward."""
    vision = get_mock_vision()

    # Target is centered but 3 meters away (target is 1m)
    vision.simulate_target_centered(tag_id=20, distance=3.0)

    cmd = auton_drive.align_to_tag(20)
    cmd.initialize()
    cmd.execute()

    # distance=3.0, target=1.0, so speed_x = (3-1)*0.5 = 1.0 (forward)
    assert auton_drive.drivetrain.last_speed_x > 0, \
        "Should drive forward when target is far"


def test_close_target_drives_backward(auton_drive):
    """When target is too close, robot should back up."""
    vision = get_mock_vision()

    # Target is centered but only 0.5 meters away (target is 1m)
    vision.simulate_target_centered(tag_id=20, distance=0.5)

    cmd = auton_drive.align_to_tag(20)
    cmd.initialize()
    cmd.execute()

    # distance=0.5, target=1.0, so speed_x = (0.5-1)*0.5 = -0.25 (backward)
    assert auton_drive.drivetrain.last_speed_x < 0, \
        "Should drive backward when target is too close"


def test_on_target_finishes_command(auton_drive):
    """Command should finish when aligned."""
    vision = get_mock_vision()

    # Target is perfectly centered at target distance
    vision.simulate_target_centered(tag_id=20, distance=1.0)

    cmd = auton_drive.align_to_tag(20)
    cmd.initialize()
    cmd.execute()

    assert cmd.isFinished(), "Should finish when on target"


def test_lost_target_finishes_command(auton_drive):
    """Command should finish if target is lost."""
    vision = get_mock_vision()

    # Start with a target
    vision.simulate_target_centered(tag_id=20, distance=2.0)

    cmd = auton_drive.align_to_tag(20)
    cmd.initialize()
    cmd.execute()

    assert not cmd.isFinished(), "Should not be finished yet"

    # Lose the target
    vision.simulate_no_target()

    assert cmd.isFinished(), "Should finish when target lost"


def test_strafe_correction_for_offset_target(auton_drive):
    """Robot should strafe to center on target."""
    vision = get_mock_vision()

    # Target is 10 degrees to the right
    vision.simulate_target_right(tag_id=20, offset_degrees=10, distance=1.0)

    cmd = auton_drive.align_to_tag(20)
    cmd.initialize()
    cmd.execute()

    # tx = +10, so speed_y = -10 * 0.05 = -0.5 (strafe left to center)
    assert auton_drive.drivetrain.last_speed_y < 0, \
        "Should strafe left when target is to the right"
```

### Testing Complex Auto Sequences with Vision

```python
# tests/test_auto_with_vision.py

def test_two_piece_auto_sequence(setup_mocks):
    """Test full autonomous with vision alignment."""
    vision = get_mock_vision()
    arm = Arm()
    intake = Intake()
    drivetrain = Drivetrain()
    auton_drive = AutonDrive(drivetrain)

    auton_modes = AutonModes(drivetrain, arm, intake, auton_drive)

    # Setup: scoring tag visible and centered
    vision.simulate_target_centered(tag_id=20, distance=1.0)

    cmd = auton_modes.two_piece("blue_left")
    cmd.initialize()

    # Run a few cycles
    for _ in range(10):
        cmd.execute()
        if cmd.isFinished():
            break

    # Verify arm moved to score position
    assert arm.motor.command_history, "Arm should have received commands"

    # Verify intake ran
    assert intake.motor.command_history, "Intake should have received commands"
```

---

## 6. Tips for Vision Testing

1. **Test edge cases:**
   - Target at extreme angles (+/-30 degrees)
   - Target very close (< 0.5m) or far (> 5m)
   - Target lost mid-alignment
   - Wrong tag detected

2. **Verify directions:**
   - Left target -> rotate left, strafe right
   - Right target -> rotate right, strafe left
   - Far target -> drive forward
   - Close target -> drive backward

3. **Test tolerances:**
   - Just inside tolerance -> command finishes
   - Just outside tolerance -> command continues

4. **Simulate real sequences:**
   - Target starts off-center, gradually gets centered as commands run
   - Multiple targets visible, verify correct one selected

---

**See also:**
- [Hardware & Subsystems](hardware-and-subsystems.md) - Hardware abstraction that makes vision testable
- [Autonomous](autonomous.md) - Using vision alignment in auto routines
- [Testing & Simulation](testing-and-simulation.md) - Full physics simulation with vision
