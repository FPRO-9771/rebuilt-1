# Autonomous System

**Team 9771 FPRO - 2026**

This doc covers how autonomous routines work, how paths are selected, and how robot.py runs them.

> **When to read this:** You're building or editing auto routines.

---

## Table of Contents

1. [Structure](#1-structure)
2. [Autonomous Constants](#2-autonomous-constants)
3. [Autonomous Mode Factory](#3-autonomous-mode-factory)
4. [Autonomous Mode Selector](#4-autonomous-mode-selector)
5. [Path Selection via Match Setup](#5-path-selection-via-match-setup)
6. [Using in Robot.py](#6-using-in-robotpy)

---

## 1. Structure

The autonomous system has three concerns:

- **Routines** -- `AutonModes` provides factory methods that return commands. Currently: `do_nothing()` (safe default) and `follow_path(path_name)` (PathPlanner path following).
- **Constants** -- Field-position data in `autonomous/auton_constants.py`: AprilTag IDs, drive paths, vision calibration, and driving behavior settings. These are placeholder values awaiting 2026 field calibration.
- **Selection** -- Each starting pose in `constants/match.py` has an `auto_path` field. The drive team selects a pose on the Elastic dashboard before the match, and `robot.py` reads the path name from that pose at auto start.

---

## 2. Autonomous Constants

```python
# autonomous/auton_constants.py

# AprilTag IDs for each starting position (TODO: update for 2026)
APRILTAG_IDS = {
    "blue_left": {"score": 1, "intake": 2},
    "blue_center": {"score": 3},
    # etc.
}

# Drive paths: list of (vx, vy, omega, duration) tuples
DRIVE_PATHS = {
    "exit_zone": [
        (2.0, 0, 0, 1.5),  # Drive forward at 2 m/s for 1.5 seconds
    ],
    # etc.
}
```

> **Note:** These constants are placeholder scaffolding. The actual auto paths are PathPlanner `.path` files loaded by name. The `DRIVE_PATHS` dict is not currently used by any auto routine.

---

## 3. Autonomous Mode Factory

```python
# autonomous/auton_modes.py

from commands2 import Command, WaitCommand
from pathplannerlib.auto import AutoBuilder
from pathplannerlib.path import PathPlannerPath

class AutonModes:
    def __init__(self, drivetrain=None, conveyor=None, vision=None):
        self.drivetrain = drivetrain
        self.conveyor = conveyor
        self.vision = vision

    def do_nothing(self) -> Command:
        """Auto that does nothing -- safe default."""
        return WaitCommand(15.0)

    def follow_path(self, path_name: str) -> Command:
        """Follow a PathPlanner path by name."""
        try:
            path = PathPlannerPath.fromPathFile(path_name)
            return AutoBuilder.followPath(path)
        except Exception as e:
            _log.error(f"Failed to load path '{path_name}': {e}")
            return WaitCommand(15.0)
```

Key points:
- `do_nothing()` returns a 15-second wait -- safe fallback if no path is configured.
- `follow_path()` loads a PathPlanner `.path` file by name and returns an `AutoBuilder.followPath()` command. If the path file fails to load, it falls back to a 15-second wait and logs an error.

---

## 4. Autonomous Mode Selector

`autonomous/auton_mode_selector.py` provides a `create_auton_chooser()` function that builds a SmartDashboard/Shuffleboard `SendableChooser` for picking auto routines from the dashboard.

```python
# autonomous/auton_mode_selector.py

def create_auton_chooser(auton_modes) -> SendableChooser:
    chooser = SendableChooser()
    chooser.setDefaultOption("Do Nothing", lambda: auton_modes.do_nothing())
    # TODO: Add more options as auto routines are implemented
    SmartDashboard.putData("Auto Mode", chooser)
    return chooser
```

Key design detail: the chooser stores **factory lambdas**, not command instances. Commands carry state and must be created fresh each auto period -- storing a lambda like `lambda: auton_modes.do_nothing()` ensures a new command is built every time the selected option is retrieved.

The function takes an `AutonModes` instance (with subsystems already injected) and publishes the chooser to SmartDashboard under the key `"Auto Mode"`.

**Current status: not wired up.** The import in `autonomous/__init__.py` is commented out, and nothing in `robot_container.py` or `robot.py` calls `create_auton_chooser()`. The existing auto system selects paths via the starting pose's `auto_path` field instead (see section 5). When the team is ready for a standalone auto chooser -- separate from pose selection -- this module is the scaffold to build on.

---

## 5. Path Selection via Match Setup

There is no auto chooser widget wired up yet (`robot_container.py` has a `# TODO: Set up auto mode selector`; see section 4 for the scaffold). Instead, the auto path is tied to the starting pose.

Each pose in `constants/match.py` has an `auto_path` field:

```python
# constants/match.py (excerpt)

"poses": [
    {
        "name": "Center",
        "default": True,
        "start_x": 13.0,
        "start_y": 4.0,
        "start_heading": 180.0,
        "auto_path": "TEST PATH FPRO",  # PathPlanner path name
    },
    {
        "name": "Left",
        "start_x": 0.0,
        "start_y": 0.0,
        "start_heading": 180.0,
        "auto_path": "",  # Empty = no auto path
    },
]
```

The drive team selects a starting pose on the Elastic dashboard before the match. The `auto_path` value from that pose determines which PathPlanner path runs in auto. An empty string means no auto path (robot does nothing).

---

## 6. Using in Robot.py

`robot.py` handles autonomous directly without using `AutonModes`. It reads the path name from the selected pose and loads it inline:

```python
# robot.py (actual implementation)

def autonomousInit(self):
    """Called when autonomous mode starts."""
    self._apply_selected_pose()
    pose = self.container.match_setup.get_pose()
    path_name = pose.get("auto_path", "")

    if not path_name:
        _log.warning("No auto path configured for selected pose")
        return

    try:
        path = PathPlannerPath.fromPathFile(path_name)
        self.auto_command = AutoBuilder.followPath(path)
        self.auto_command.schedule()
        _log.info(f"Auto started: {path_name}")
    except Exception as e:
        _log.error(f"Failed to load auto path '{path_name}': {e}")

def autonomousExit(self):
    """Called when autonomous mode ends."""
    if self.auto_command:
        self.auto_command.cancel()
```

The flow:
1. `_apply_selected_pose()` resets drivetrain odometry to the pose's field coordinates.
2. `get_pose()` returns the selected pose dict (alliance from DS + pose name from Elastic).
3. If `auto_path` is non-empty, it loads the PathPlanner path file and schedules it.
4. If the path fails to load, it logs an error and the robot does nothing.
5. `autonomousExit()` cancels any running auto command.

> **Note:** `robot.py` currently loads PathPlanner paths directly rather than going through `AutonModes`. The `AutonModes` class exists and has the same `follow_path()` logic, but is not wired up yet. A future step could add an auto mode chooser in `RobotContainer` that uses `AutonModes` for more complex routines.

---

**See also:**
- [Commands & Controls](commands-and-controls.md) - Command composition patterns used in auto routines
- [Vision](vision.md) - Using Limelight for vision-based alignment in auto
- [Testing & Simulation](testing-and-simulation.md) - Testing auto routines with physics simulation
- [Match Setup](match-setup.md) - Pre-match alliance/pose selection and how `auto_path` is configured
