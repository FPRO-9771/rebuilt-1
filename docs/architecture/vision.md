# Vision System (Limelight)

**Team 9771 FPRO - 2026**

This doc covers using Limelight cameras for AprilTag detection, the testable vision abstraction layer, and MegaTag2 odometry.

> **When to read this:** You're working with Limelight vision for odometry, teleop assist, or any vision use.

> **Current status (April 2026):** The vision abstraction layer (VisionProvider,
> LimelightVisionProvider, MockVisionProvider) exists in code but is **not wired
> up** in `robot_container.py`. The factory functions in `handlers/__init__.py`
> are commented out. Right now the team uses **two Limelights** (left and right,
> fixed-mounted off the back of the robot) for continuous **MegaTag2 odometry
> corrections**. Both cameras feed the drivetrain pose estimator every robot
> loop via `drivetrain.vision_pose_correct()`, which calls
> `add_vision_measurement()` for every Limelight that currently sees tags.
> The NetworkTables reads go through `handlers/limelight_helpers.py` and do
> not use the VisionProvider layer.

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

The robot has two Limelights, pointed left and right off the back of the
chassis. Both are on static IPs so the web UI is reachable without
hostname lookup at competition.

| Camera | NT Name | IP Address | Web UI |
|--------|---------|------------|--------|
| Left   | `limelight-left`  | `10.97.71.11` (static) | `http://10.97.71.11:5801` |
| Right  | `limelight-right` | `10.97.71.12` (static) | `http://10.97.71.12:5801` |

Shared settings:

| Setting | Value |
|---------|-------|
| Subnet Mask | `255.255.255.0` |
| Gateway | `10.97.71.1` |
| Pipeline 0 | AprilTag detection |

- Each Limelight connects via **Ethernet to the radio** (not the roboRIO)
- IP must be **static** -- DHCP is unreliable at competition
- The team number subnet is `10.97.71.x` (from team 9771)
- The **NT Name** in the left column must match the "Hostname" field in
  each Limelight's web UI -- if it doesn't, `drivetrain.vision_pose_correct()`
  will read empty NetworkTables entries and silently do nothing

---

## 3. MegaTag2 Odometry (Active)

This is the **currently active** Limelight integration. The module
`handlers/limelight_helpers.py` talks to each Limelight over NetworkTables
(not the websocket/polling approach used by `LimelightVisionProvider`).

### What it does

MegaTag2 fuses the robot's gyro heading with AprilTag detections to produce
a field-relative pose estimate. The drivetrain feeds each Limelight's
estimate into WPILib's pose estimator every loop, which Kalman-blends the
measurements with wheel odometry to keep the robot's pose accurate
continuously (rather than only on button press).

### Architecture: three methods on the drivetrain

All Limelight access on the drivetrain goes through three methods in
`subsystems/command_swerve_drivetrain.py`. They are the only public /
private names the rest of the code should touch for vision odometry.

| Method | Kind | Purpose |
|--------|------|---------|
| `_vision_pose_read_mt1()` | private | Loops over every camera in `CON_VISION`, reads **MegaTag1** (pure AprilTag PnP, no gyro fusion), returns the best `(camera_key, PoseEstimate)` tuple. Skips any camera with fewer than `LIMELIGHT_RESET_MIN_TAGS` tags (default 2) so single-tag PnP ambiguity can never snap odom to a mirrored pose. Best = most tags, tie-broken by larger `avg_tag_area`. Returns `None` if no camera qualifies. |
| `vision_pose_correct()` | public, **soft** | For every Limelight currently seeing tags, calls `add_vision_measurement()` on its bot-pose estimate. Kalman-blended -- safe to call every loop, safe mid-path in auton (no subsystem requirements). This is the one that runs continuously. The source is selectable via `VISION_POSE_CORRECT_MODE` (`"mt2"` = MegaTag2, gyro-fused, accepts single-tag; `"mt1"` = MegaTag1, pure PnP, requires `VISION_POSE_CORRECT_MT1_MIN_TAGS` tags). Honors the `VISION_POSE_CORRECT_ENABLED` kill switch and feeds the per-cycle debug logger -- see [Vision Configuration](#5-vision-configuration). |
| `vision_pose_reset_request()` | public, **hard** | Arms a one-shot flag. `periodic()` services it on the next loop a camera satisfies the MT1 tag-count requirement (up to `LIMELIGHT_RESET_TIMEOUT`). Uses `reset_pose()` to **fully override** the pose -- X, Y, AND yaw -- with the MT1 estimate. Driver escape hatch for when the gyro has drifted and soft correction has converged on a wrong but self-consistent pose. **Bypasses** the `VISION_POSE_CORRECT_ENABLED` kill switch on purpose -- the hard reset stays available even when continuous correction is disabled. The full B-press lifecycle (armed, pending, fired/timeout) is logged unconditionally via `telemetry/vision_reset_logging.py` -- see [B-press breadcrumb logging](#b-press-breadcrumb-logging). |

> **Why MT1 for the hard reset and MT2 for soft correction?** MT2 fuses
> the gyro heading into its position estimate, which lets it disambiguate
> single-tag PnP -- exactly what continuous multi-camera correction needs.
> But that fusion also means MT2 cannot detect or correct gyro errors:
> if the gyro is off, MT2's position is off in a predictable geometric
> way, the soft correction propagates that into odom, and the system
> converges on a wrong-but-stable pose. MT1 is gyro-independent, so it
> is the only way to escape that loop. We pay for that independence by
> requiring 2+ tags (multi-tag PnP eliminates the single-tag ambiguity
> MT2 normally resolves with the gyro).

### Where each is called from

- **`periodic()`** sends `set_robot_orientation()` to every Limelight every
  loop (required so MT2 can disambiguate single-tag PnP), and calls
  `vision_pose_correct()` every `VISION_POSE_CORRECT_PERIOD_LOOPS` loops
  (defined in `constants/vision.py`, default `1` = every loop = ~50 Hz).
  Bump that constant if the driver station reports loop overruns.
- **Driver B button** (`controls/driver_controls.py`) calls
  `vision_pose_reset_request()`.
- **Auton `CorrectOdometry` named command** (`autonomous/named_commands.py`)
  is a `RunCommand(lambda: drivetrain.vision_pose_correct())`. PathPlanner
  point markers feed one measurement; zone markers feed one every loop
  inside the zone.

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

### Low-level functions in `limelight_helpers`

| Function | Purpose |
|----------|---------|
| `get_bot_pose_estimate_wpi_blue_megatag2(nt_name)` | MegaTag2 pose (gyro-fused). Used by `vision_pose_correct` for continuous soft correction. |
| `get_bot_pose_estimate_wpi_blue_megatag1(nt_name)` | MegaTag1 pose (pure AprilTag PnP, no gyro). Used by `_vision_pose_read_mt1` for the B-button hard reset, and by `vision_correct_logging` as an independent sanity check on MT2. |
| `set_robot_orientation(nt_name, ...)` | Send gyro heading to a Limelight each loop so MegaTag2 can fuse it. Must be called every cycle, for every camera. |
| `get_tv(nt_name)` | Returns True if the Limelight has a valid target. |
| `get_tag_count(nt_name)` | Number of tags visible in the latest MegaTag2 result. |

All of these take a NetworkTables table name (`limelight-left` or
`limelight-right`), which must match each Limelight's configured hostname.

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

Camera configuration lives in `constants/vision.py`. The dict defines the
full fleet of Limelights -- everything else (telemetry, camera streams,
the drivetrain vision methods above) iterates over this one source of
truth:

```python
# constants/vision.py

CON_VISION = {
    "cameras": {
        "left": {
            "name": "Limelight Left",
            "nt_name": "limelight-left",
            "host": "10.97.71.11",
        },
        "right": {
            "name": "Limelight Right",
            "nt_name": "limelight-right",
            "host": "10.97.71.12",
        },
    },
}

VISION_POSE_CORRECT_PERIOD_LOOPS = 1
VISION_POSE_CORRECT_ENABLED = True
VISION_POSE_LOG_PERIOD_LOOPS = 10
VISION_POSE_CORRECT_MODE = "mt2"
VISION_POSE_CORRECT_MT1_MIN_TAGS = 2
```

Per-camera fields:

| Field | Meaning |
|-------|---------|
| `name`    | Human-readable label (shown in CameraServer / Elastic dashboard) |
| `nt_name` | NetworkTables table name; must match the Hostname configured in the Limelight's own web UI |
| `host`    | Static IP address; used for the MJPEG stream URL (`http://<host>:5800/stream.mjpg`) and the web UI (`http://<host>:5801`) |

Module-level constants in the same file:

| Constant | Meaning |
|----------|---------|
| `VISION_POSE_CORRECT_PERIOD_LOOPS` | How often `periodic()` runs the continuous soft correction. `1` = every loop (~50 Hz), `2` = every other loop (~25 Hz), etc. Raise it if the driver station reports loop overruns, but start at `1`. |
| `VISION_POSE_CORRECT_ENABLED` | Master kill switch for `vision_pose_correct()`. Set `False` between matches if vision is feeding the estimator garbage and you want to fly on pure wheel odometry. **The B-button hard reset still works** -- it deliberately bypasses this flag. |
| `VISION_POSE_CORRECT_MODE` | Which bot-pose estimate feeds `add_vision_measurement()`. `"mt2"` (default) = MegaTag2, gyro-fused, handles single-tag PnP via gyro disambiguation. `"mt1"` = MegaTag1, pure AprilTag PnP, requires multi-tag visibility. **The B-button hard reset always uses MT1** regardless of this setting -- that is the point of the escape hatch. |
| `VISION_POSE_CORRECT_MT1_MIN_TAGS` | Minimum tags per camera when `MODE == "mt1"`. Default `2`. Cameras with fewer tags are skipped that loop -- no measurement fed to the estimator. Single-tag MT1 has unresolved PnP ambiguity and can snap odom to a mirrored position. |
| `VISION_POSE_LOG_PERIOD_LOOPS` | Rate limit for the per-cycle debug logger -- only used when `DEBUG["vision_pose_correct_logging"]` is on. `10` = ~5 Hz at a 50 Hz loop. |

**Choosing MT1 vs MT2 for soft correction.** MT2 is the common choice
in FRC because single-tag PnP disambiguation via gyro "just works" --
any time a camera sees a tag, it produces a measurement. But MT2 can
show a systematic position bias relative to MT1 on some field setups
(we have observed ~13 cm on our lab tags, where a tape measure confirms
MT1 is the truth). If you see that pattern -- consistent MT2/MT1 offset
on stationary pose, with MT1 matching a physical measurement -- try
flipping `VISION_POSE_CORRECT_MODE = "mt1"` for a match-day test. MT1
gives up single-tag corrections but trades that for bias-free multi-tag
corrections. The debug logger shows both estimates every cycle so you
can A/B them on the same run (see below).

To add a third camera, drop another entry into this dict -- no other code
changes needed.

### Debug logging for soft correction

When you see the Elastic field map disagreeing with reality and need to
figure out which camera is at fault, flip
`DEBUG["vision_pose_correct_logging"]` to `True` in `constants/debug.py`,
redeploy, and tail `/var/log/messages` for `VPC` lines:

```
VPC left  [mt2] | tags=2 ids=[24, 25] avg_dist=2.41m avg_area=0.018 lat=22ms | mt2=(4.62,3.97,1.5) mt1=(4.59,3.95,1.7) | odom=(4.64,4.01,1.4) dxy=(-0.02,-0.04)
VPC right: no tags
```

If `VISION_POSE_CORRECT_MODE = "mt1"` and a camera only sees 1 tag, the
prefix switches to `[mt1-REJ]` and `dxy=rejected` -- the measurement
was not fed to the estimator this loop (single-tag MT1 is too
ambiguous). Both sources are still shown so you can see what MT2 *would*
have reported:

```
VPC right [mt1-REJ] | tags=1 ids=[26] avg_dist=1.94m avg_area=0.469 lat=34ms | mt2=(1.98,4.02,88.8) mt1=(2.11,4.05,88.7) | odom=(1.98,4.02,88.8) dxy=rejected
```

Each line shows, for one camera on one log cycle:
- `[mode]` prefix -- which source is currently active (`mt1`/`mt2`), with `-REJ` if the active source failed its minimum-tag check this loop
- `tags` / `ids` -- how many AprilTags are visible, and which ones
- `avg_dist` / `avg_area` / `lat` -- tag quality fields (further/smaller/older = less trustworthy)
- `mt2` -- the MegaTag2 (gyro-fused) pose
- `mt1` -- the MegaTag1 (pure AprilTag PnP, no gyro) pose
- `odom` -- the current fused pose just before this measurement was added
- `dxy` -- (active.x - odom.x, active.y - odom.y), the jump the Kalman filter is being asked to absorb (or `rejected` if no measurement was fed)

Showing both MT1 and MT2 every cycle is what makes this logger useful
for A/B testing `VISION_POSE_CORRECT_MODE`. Run both modes on the same
field layout, compare the `dxy` column against physical reality, and
pick the one that tracks better.

Logging lives in `telemetry/vision_correct_logging.py` (mirrors the
`auto_aim_logging` pattern). NetworkTables reads only happen **on log
cycles** (~5 Hz), so leaving the flag off costs zero extra bandwidth in
matches.

> **auton_quiet_mode gotcha:** with `DEBUG["auton_quiet_mode"] = True`,
> `utils/logger.py` silently raises non-whitelisted loggers to WARNING
> level. The `vpc` logger is on the whitelist (in `_AUTON_LOGGERS`) so
> these INFO lines actually reach the console. If you add a new logger
> for vision and don't see its INFO output, **add the logger name to
> `_AUTON_LOGGERS`** -- otherwise the messages are dropped before they
> ever leave Python.

### B-press breadcrumb logging

The B-button hard reset is a driver escape hatch, so we log every step
of its lifecycle unconditionally -- there is no debug flag to forget to
flip. The `vision_reset` logger is whitelisted in `_AUTON_LOGGERS`, so
its INFO lines come through even with `auton_quiet_mode` on.

The reset uses **MegaTag1** (no gyro fusion) and requires
`LIMELIGHT_RESET_MIN_TAGS` visible tags (default 2) on at least one
camera. It overrides the **full** pose -- X, Y, AND yaw -- so the
driver's field-centric "forward" direction will visibly jump on a
successful press. That is intentional: the whole point of the hard
reset is to escape gyro drift.

One B press with multi-tag visibility produces this trail:

```
B PRESSED: hard reset armed, will fire on next tag-visible loop within 2.0s
PENDING odom=(1.38,3.88,-85) | left=mt1_tags[26, 25]@2.4m(READY) | right=no_tags
FIRED via left: tags=2 ids=[26, 25] avg_dist=2.45m avg_area=0.268 lat=54ms | odom_before=(1.38,3.88,-84.7) | vision_raw=(1.53,4.03,-87.7) | applied=(1.53,4.03,-87.7)
```

Or, if only single-tag MT1 is available the whole window:

```
B PRESSED: hard reset armed, will fire on next tag-visible loop within 2.0s
PENDING odom=(1.38,3.88,-85) | left=mt1_tags[26]@2.4m(need_2+_tags) | right=no_tags
PENDING odom=(1.38,3.88,-85) | left=mt1_tags[26]@2.4m(need_2+_tags) | right=no_tags
TIMEOUT after 2.0s -- no camera saw any tags. Reset NOT applied; odometry unchanged.
```

`PENDING` lines are rate-limited to ~5 Hz (`_PENDING_LOG_PERIOD_LOOPS`
in `vision_reset_logging.py`), so the 2 s window produces at most a
handful of lines per press. Logging lives in
`telemetry/vision_reset_logging.py`.

**Reading the trail to diagnose "B did nothing":**
- No `B PRESSED` line at all -> the trigger binding never fired. Check the controller mapping in `controls/driver_controls.py`.
- `B PRESSED`, all `PENDING` lines show `need_2+_tags` or `no_tags`, then `TIMEOUT` -> binding works, but the cameras never had multi-tag visibility in the window. Drive somewhere with two or more tags in view of one Limelight and try again.
- `B PRESSED` then `FIRED` with `applied` close to `odom_before` -> reset worked, odometry was already correct. This is the healthy case after gyro is well-calibrated.
- `B PRESSED` then `FIRED` with `applied` materially different from `odom_before` (especially in yaw) -> reset worked AND found a real gyro/odom error. Watch for the same delta to come back over the next few minutes -- if it does, the gyro is drifting and you have a calibration problem to chase, not a vision problem.

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
