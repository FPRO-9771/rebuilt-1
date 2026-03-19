# Vision System (Limelight)

**Team 9771 FPRO - 2026**

This doc covers using Limelight cameras for AprilTag detection, the testable vision abstraction layer, and MegaTag2 odometry.

> **When to read this:** You're working with Limelight vision for odometry, teleop assist, or any vision use.

> **Current status (March 2026):** The vision abstraction layer (VisionProvider,
> LimelightVisionProvider, MockVisionProvider) exists in code but is **not wired
> up** in `robot_container.py`. The factory functions in `handlers/__init__.py`
> are commented out. Right now the team is focused on **Limelight MegaTag2
> odometry** via `handlers/limelight_helpers.py`, which uses NetworkTables
> directly and does not go through the VisionProvider layer.

---

## Table of Contents

1. [What Limelight Provides](#1-what-limelight-provides)
2. [Limelight Network Setup](#2-limelight-network-setup)
3. [MegaTag2 Odometry (Active)](#3-megatag2-odometry-active)
4. [Vision Abstraction Layer (Inactive)](#4-vision-abstraction-layer-inactive)
5. [Vision Configuration](#5-vision-configuration)
6. [Vision Telemetry](#6-vision-telemetry)
7. [Testing Vision-Based Commands](#7-testing-vision-based-commands)
8. [Tips for Vision Testing](#8-tips-for-vision-testing)

---

## 1. What Limelight Provides

The Limelight camera detects AprilTags and provides:

| Field | Description |
|-------|-------------|
| `tag_id` | Which AprilTag was detected |
| `tx` | Horizontal offset in degrees (negative = target left of center) |
| `ty` | Vertical offset in degrees |
| `distance` | 3D distance to target in meters |
| `yaw` | Target's rotation relative to camera |
| `pitch`, `roll` | Target's orientation |
| `x_pos`, `y_pos`, `z_pos` | Target position in camera space |

---

## 2. Limelight Network Setup

| Setting | Value |
|---------|-------|
| IP Address | `10.97.71.11` (static) |
| Subnet Mask | `255.255.255.0` |
| Gateway | `10.97.71.1` |
| Web UI | `http://10.97.71.11:5801` |
| Pipeline 0 | AprilTag detection |

- The Limelight connects via **Ethernet to the radio** (not the roboRIO)
- IP must be **static** -- DHCP is unreliable at competition
- The team number subnet is `10.97.71.x` (from team 9771)
- If you can't reach it by IP, try `ping limelight.local` to find it

---

## 3. MegaTag2 Odometry (Active)

This is the **currently active** Limelight integration. The module
`handlers/limelight_helpers.py` talks to the Limelight over NetworkTables
(not the websocket/polling approach used by `LimelightVisionProvider`).

### What it does

MegaTag2 fuses the robot's gyro heading with AprilTag detections to produce a
field-relative pose estimate. The drivetrain feeds this into WPILib's pose
estimator for odometry corrections.

### Key data types

```python
# handlers/limelight_helpers.py

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
```

### Key functions

| Function | Purpose |
|----------|---------|
| `get_bot_pose_estimate_wpi_blue_megatag2()` | MegaTag2 pose (gyro-fused). Used for continuous odometry updates. |
| `get_bot_pose_estimate_wpi_blue_megatag1()` | MegaTag1 pose (pure AprilTag geometry, no gyro). Better for one-shot pose resets. |
| `set_robot_orientation()` | Send gyro heading to Limelight each loop so MegaTag2 can fuse it. Must be called every cycle. |
| `get_tv()` | Returns True if the Limelight has a valid target. |
| `get_tag_count()` | Number of tags visible in the latest MegaTag2 result. |

### Usage

The NetworkTables table name must match the Limelight's configured name.
For our shooter Limelight the table name is `"limelight-shooter"`:

```python
from handlers.limelight_helpers import (
    set_robot_orientation,
    get_bot_pose_estimate_wpi_blue_megatag2,
)

# Every loop -- feed gyro heading to the Limelight
set_robot_orientation("limelight-shooter", yaw_degrees=gyro_yaw)

# Read MegaTag2 pose estimate
estimate = get_bot_pose_estimate_wpi_blue_megatag2("limelight-shooter")
if estimate and estimate.tag_count >= 1:
    drivetrain.add_vision_measurement(estimate.pose, estimate.timestamp_seconds)
```

---

## 4. Vision Abstraction Layer (Inactive)

> **Note:** This layer exists in code but is **not currently wired up**. The
> factory functions in `handlers/__init__.py` are commented out, and
> `robot_container.py` does not create any VisionProvider instances. The code
> is kept for future use if the team needs vision-based aiming (e.g. aligning
> to targets using tx/ty offsets).

### The problem

We couldn't test vision-based commands without a real Limelight and AprilTags.

### Solution: VisionProvider interface

`handlers/vision.py` defines the abstract contract:

```python
# handlers/vision.py

@dataclass
class VisionTarget:
    """Standardized vision target data."""
    tag_id: int
    tx: float           # Horizontal offset (degrees, negative = left)
    ty: float           # Vertical offset (degrees)
    distance: float     # Distance to target (meters)
    yaw: float          # Target rotation
    is_valid: bool = True
    timestamp: float = 0.0  # time.monotonic() when this data was received


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

    @abstractmethod
    def get_all_targets(self) -> List[VisionTarget]:
        """Get all currently visible targets."""
        pass
```

### Implementations

**LimelightVisionProvider** (`handlers/limelight_vision.py`) -- the real hardware
implementation. Connects to a Limelight by IP address and polls for AprilTag
fiducial data in a background daemon thread so the robot loop is never blocked.
The public methods (`get_target`, `has_target`, `get_all_targets`) return
thread-safe cached data. Also tracks data freshness -- stamps targets with the
`time.monotonic()` when the data actually changed, not the poll time.

**MockVisionProvider** (`handlers/mock_vision.py`) -- the test implementation.
Lets tests simulate targets at specific positions with helpers like
`simulate_target_left()`, `simulate_target_right()`, `simulate_target_centered()`,
and `simulate_no_target()`. Tracks query history for assertions.

### Factory functions (commented out)

The factory functions in `handlers/__init__.py` are commented out. They would
create one provider per camera defined in `CON_VISION`:

```python
# handlers/__init__.py (COMMENTED OUT -- not currently active)

# _use_mock_vision = False
# _mock_providers: dict[str, VisionProvider] | None = None
#
# def set_mock_vision_mode(enabled: bool) -> None: ...
# def get_vision_providers() -> dict[str, VisionProvider]: ...
# def get_mock_vision(camera: str = "shooter") -> "MockVisionProvider": ...
```

To re-enable: uncomment these functions and wire them into `robot_container.py`.

---

## 5. Vision Configuration

Camera configuration lives in `constants/vision.py`:

```python
# constants/vision.py

CON_VISION = {
    "cameras": {
        "shooter": {
            "name": "Limelight Shooter",
            "host": "10.97.71.11",
        },
        # "front": {
        #     "name": "Limelight Front",
        #     "host": "limelight-front",  # TODO: set static IP when connected
        # },
    },
}
```

The `"host"` value is the camera's **static IP address** (not an mDNS hostname).
Only one camera (`shooter`) is currently configured. A second camera (`front`)
is stubbed out for future use.

---

## 6. Vision Telemetry

`telemetry/vision_telemetry.py` publishes per-camera AprilTag data to
SmartDashboard. It expects a dict of VisionProvider instances (one per camera)
and calls `get_all_targets()` on each.

Published keys (per camera):
- `Vision/{Camera}/Has Target` -- boolean
- `Vision/{Camera}/Tag Count` -- number of visible tags
- `Vision/{Camera}/Tag 1` through `Tag 4` -- string with tag ID, tx, ty, distance, yaw

The telemetry rate-limits to every 5 cycles (~3 Hz) to avoid loop overruns.

> **Note:** Because the VisionProvider layer is currently disabled, VisionTelemetry
> is also not active. It will work again when the providers are re-enabled.

---

## 7. Testing Vision-Based Commands

When the VisionProvider layer is re-enabled, you can test alignment commands
without hardware using MockVisionProvider:

```python
# Example test pattern

from handlers.mock_vision import MockVisionProvider
from handlers.vision import VisionTarget

def test_target_left_rotates_left():
    """When target is left of center, robot should rotate left."""
    vision = MockVisionProvider()

    # Target is 15 degrees to the LEFT
    vision.simulate_target_left(tag_id=20, offset_degrees=15, distance=2.0)

    target = vision.get_target(20)
    assert target is not None
    assert target.tx < 0  # negative = left

def test_no_target():
    """No targets visible."""
    vision = MockVisionProvider()
    vision.simulate_no_target()

    assert not vision.has_target()
    assert vision.get_all_targets() == []
```

---

## 8. Tips for Vision Testing

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
- [Testing & Simulation](testing-and-simulation.md) - Full physics simulation with vision
- [Telemetry](telemetry.md) - Dashboard telemetry system
