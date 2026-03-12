# Telemetry Dashboard

Live telemetry published to SmartDashboard every 20ms. Viewable in **Shuffleboard**, **Elastic**, or **Glass** on the driver station laptop.

---

## Module Structure

```
telemetry/
├── __init__.py             # setup_telemetry() and update_telemetry()
├── motor_telemetry.py      # Motor positions and velocities
├── command_telemetry.py    # Active commands and recent event log
├── vision_telemetry.py     # Per-camera Limelight AprilTag data
└── camera_telemetry.py     # CameraServer MJPEG stream registration
```

Each publisher is a small class with an `update()` method that pushes data to `wpilib.SmartDashboard`.

---

## How It's Wired

1. `robot_container.py` calls `setup_telemetry(conveyor, turret, launcher, hood, vision)` at the end of `__init__()` — creates all publishers, registers command callbacks, and sets up camera streams. The `vision` argument is a dict of `{camera_key: VisionProvider}` (e.g., `{"shooter": ..., "front": ...}`).
2. `robot.py` calls `update_telemetry()` in `robotPeriodic()` after `CommandScheduler.run()` — publishes all data every cycle in all modes (teleop, auto, disabled).

---

## Published Keys

### Motor Telemetry (`motor_telemetry.py`)

| SmartDashboard Key | Source |
|--------------------|--------|
| `Motors/Conveyor Velocity` | `conveyor.get_velocity()` |
| `Motors/Turret Position` | `turret.get_position()` |
| `Motors/Turret Velocity` | `turret.get_velocity()` |
| `Motors/Launcher Target RPS` | `launcher._target_rps` |
| `Motors/Launcher Actual RPS` | `launcher.get_velocity()` |
| `Motors/Launcher At Speed` | `launcher.is_at_speed(target_rps)` |
| `Motors/Hood Position` | `hood.get_position()` |

### Command Telemetry (`command_telemetry.py`)

| SmartDashboard Key | Type | Description |
|--------------------|------|-------------|
| `Commands/Active` | string | Comma-separated list of currently running commands |
| `Commands/Recent` | string | ASCII table of the last 5 command start/end events |

Hooks into `CommandScheduler.onCommandInitialize()` and `onCommandFinish()` callbacks. Filters out noisy internal commands (names starting with `_`, `Instant`, `PerpetualCommand`, `RunCommand`).

### Match Setup (`match_setup.py`)

Published every cycle by `MatchSetup.update()`.

| SmartDashboard Key | Type | Description |
|--------------------|------|-------------|
| `Match/Is Red Alliance` | boolean | True = Red alliance, False = Blue alliance |

**How to use in Elastic (big alliance color indicator):**

1. Drag `Match/Is Red Alliance` onto your layout
2. Right-click the widget and change it to **Boolean Box**
3. In the widget properties, set **True color** to red and **False color** to blue
4. Resize it big so the kids can see it from across the pit

### Drive Mode & Pose (`controls/driver_controls.py`, `telemetry/swerve_telemetry.py`)

| SmartDashboard Key | Type | Description |
|--------------------|------|-------------|
| `Drive/Robot Centric` | boolean | True = robot-centric, False = field-centric |
| `Drive/Pose X (m)` | number | Robot X position on the field (meters) |
| `Drive/Pose Y (m)` | number | Robot Y position on the field (meters) |
| `Drive/Heading (deg)` | number | Robot heading in degrees |

### Shooter / Auto-Aim Targeting

AutoAim publishes its own telemetry keys (`Shooter/AutoAim`, `Shooter/AutoAim/HasTarget`, `Shooter/AutoAim/LockedTag`, plus debug-only velocity/lead keys). See the [Auto-Aim System](auto-aim.md#9-debugging-guide) doc for the full key list, console log format, and debugging walkthrough.

### Vision Telemetry (`vision_telemetry.py`)

Published per camera -- keys are prefixed with the camera name (e.g., `Vision/Shooter/`, `Vision/Front/`).

| SmartDashboard Key | Type | Description |
|--------------------|------|-------------|
| `Vision/{Camera}/Has Target` | boolean | Is any AprilTag visible |
| `Vision/{Camera}/Tag Count` | number | Number of visible tags |
| `Vision/{Camera}/Tag 1` | string | First tag: ID, tx, ty, distance, yaw |
| `Vision/{Camera}/Tag 2` | string | Second tag (empty if fewer than 2 visible) |
| `Vision/{Camera}/Tag 3` | string | Third tag (empty if fewer than 3 visible) |
| `Vision/{Camera}/Tag 4` | string | Fourth tag (empty if fewer than 4 visible) |

`{Camera}` is `Shooter` or `Front`. Loops over all cameras defined in `CON_VISION` and calls `get_all_targets()` on each. Up to 4 tags are shown; unused slots publish empty strings.

### Camera Streams (`camera_telemetry.py`)

Registers each Limelight's MJPEG stream with `CameraServer` so dashboard apps can display live video. Called once during `setup_telemetry()` — no per-cycle update needed. Camera hostnames come from `constants/vision.py`.

---

## Configuration

`constants/telemetry.py` contains:

```python
CON_TELEMETRY = {
    "max_recent_commands": 5,  # Number of events in the Recent table
}
```

---

## Adding Telemetry for a New Subsystem

1. Add `putNumber` / `putString` calls in the appropriate publisher's `update()` method (or create a new publisher if it's a distinct concern).
2. Pass the new subsystem into `setup_telemetry()` in `telemetry/__init__.py`.
3. Update the `setup_telemetry()` call in `robot_container.py`.

---

## Testing

Tests in `tests/test_telemetry.py` mock `wpilib.SmartDashboard` and verify that all expected keys are published with correct values. Command tests also mock `CommandScheduler` to avoid needing HAL initialization.
