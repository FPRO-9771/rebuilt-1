# Telemetry Dashboard

Live telemetry published to SmartDashboard every 20ms. Viewable in **Shuffleboard**, **Elastic**, or **Glass** on the driver station laptop.

---

## Module Structure

```
telemetry/
├── __init__.py             # setup_telemetry() and update_telemetry()
├── motor_telemetry.py      # Motor positions and velocities
├── command_telemetry.py    # Active commands and recent event log
└── vision_telemetry.py     # Limelight AprilTag data
```

Each publisher is a small class with an `update()` method that pushes data to `wpilib.SmartDashboard`.

---

## How It's Wired

1. `robot_container.py` calls `setup_telemetry(conveyor, turret, launcher, hood, vision)` at the end of `__init__()` — creates all three publishers and registers command callbacks.
2. `robot.py` calls `update_telemetry()` in `robotPeriodic()` after `CommandScheduler.run()` — publishes all data every cycle in all modes (teleop, auto, disabled).

---

## Published Keys

### Motor Telemetry (`motor_telemetry.py`)

| SmartDashboard Key | Source |
|--------------------|--------|
| `Motors/Conveyor Velocity` | `conveyor.get_velocity()` |
| `Motors/Turret Position` | `turret.get_position()` |
| `Motors/Turret Velocity` | `turret.get_velocity()` |
| `Motors/Launcher Velocity` | `launcher.get_velocity()` |
| `Motors/Hood Position` | `hood.get_position()` |

### Command Telemetry (`command_telemetry.py`)

| SmartDashboard Key | Type | Description |
|--------------------|------|-------------|
| `Commands/Active` | string | Comma-separated list of currently running commands |
| `Commands/Recent` | string | ASCII table of the last 5 command start/end events |

Hooks into `CommandScheduler.onCommandInitialize()` and `onCommandFinish()` callbacks. Filters out noisy internal commands (names starting with `_`, `Instant`, `PerpetualCommand`, `RunCommand`).

### Vision Telemetry (`vision_telemetry.py`)

| SmartDashboard Key | Type | Description |
|--------------------|------|-------------|
| `Vision/Has Target` | boolean | Is any AprilTag visible |
| `Vision/Tag Count` | number | Number of visible tags |
| `Vision/Tags` | string | ASCII table with ID, TX, TY, distance, yaw per tag |

Uses `vision.get_all_targets()` to get all visible tags each cycle.

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
