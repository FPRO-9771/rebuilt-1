# Match Setup

**Team 9771 FPRO - 2026**

How pre-match alliance and starting pose selection works, and how it feeds into targeting and autonomous.

> **When to read this:** You're adding a new starting pose, changing tag priorities, wiring PathPlanner paths, or setting up SmartDashboard for a match.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Configuration (constants/match.py)](#2-configuration-constantsmatchpy)
3. [SmartDashboard Choosers](#3-smartdashboard-choosers)
4. [How It Connects to Targeting](#4-how-it-connects-to-targeting)
5. [How It Will Connect to Autonomous](#5-how-it-will-connect-to-autonomous)
6. [Setting Up SmartDashboard Before a Match](#6-setting-up-smartdashboard-before-a-match)
7. [Adding a New Pose or Alliance](#7-adding-a-new-pose-or-alliance)

---

## 1. Overview

Before each match, the drive team needs two things configured:

- **Alliance** -- read automatically from the Driver Station (set by FMS during competition, or manually in the DS app during practice)
- **Starting Pose** -- selected on Elastic via a SendableChooser (Left, Center, Right)

This selection determines:

- Which AprilTags the vision system tracks and in what priority order
- The Hub target position for the alliance (field coordinates)
- The robot's starting position on the field (for odometry and PathPlanner)
- Which autonomous path to run (future)

All of this lives in `constants/match.py` so the team can tune it without touching any logic code.

---

## 2. Configuration (constants/match.py)

The `ALLIANCES` dict is the single source of truth. Each alliance is keyed by name ("Red" or "Blue") and contains the Hub target position, tag priorities, and a list of starting poses:

```python
ALLIANCES = {
    "Red": {
        "name": "Red",
        "target_x": 12.0,          # Hub center, field coords (meters)
        "target_y": 4.0,
        "tag_priority": [8, 10, 11],  # Ordered: first visible wins
        "poses": [
            {
                "name": "Center",
                "default": True,
                "start_x": 13.0,        # Field coordinates (meters)
                "start_y": 4.0,
                "start_heading": 180.0, # Degrees
                "auto_path": "TEST PATH FPRO",
            },
            # ... Left, Right
        ],
    },
    "Blue": {
        "name": "Blue",
        "target_x": 4.6,
        "target_y": 4.0,
        "tag_priority": [25, 26, 24, 27],
        "poses": [
            # ... Center (default), Left, Right
        ],
    },
}
```

A `DEFAULT_ALLIANCE` string (e.g., `"Red"`) controls which alliance is used when the Driver Station hasn't connected yet.

### Tag priority

The `tag_priority` list controls which AprilTag the vision system prefers. The list is walked in order -- the **first visible tag** wins. For example, for Red alliance:

- Tag 8 is checked first. If the camera sees it, that tag is used.
- If tag 8 is not visible, tag 10 is checked, then 11.

### Hub target position

Each alliance has `target_x` and `target_y` fields specifying the center of that alliance's Hub on the field in meters. The field origin (0, 0) is the bottom-left corner (blue driver station right corner).

---

## 3. SmartDashboard Choosers

`match_setup.py` creates a `SendableChooser` for starting pose and publishes it to SmartDashboard. Alliance color is read directly from the Driver Station -- there is no alliance chooser.

| Widget | Key | Source |
|--------|-----|--------|
| Starting Pose | `Starting Pose` | SendableChooser with union of all pose names across alliances |
| Is Red Alliance | `Match/Is Red Alliance` | Boolean published by `update()` while disabled |

The pose chooser is built dynamically from the `ALLIANCES` config. Adding a new pose to `constants/match.py` automatically adds it to the dashboard -- no code changes needed.

### How it's created

`RobotContainer.__init__` creates a `MatchSetup` instance:

```python
# robot_container.py
from match_setup import MatchSetup

class RobotContainer:
    def __init__(self):
        self.match_setup = MatchSetup()  # Publishes pose chooser
        # ...
```

### What it provides

Other code calls these methods on `match_setup`:

| Method | Returns |
|--------|---------|
| `get_alliance()` | The full alliance dict (reads DS color live) |
| `get_pose_name()` | The selected pose name string |
| `get_pose()` | The full pose dict for the selected alliance + pose |
| `get_tag_priority()` | The ordered tag ID list for the current alliance |
| `update()` | Publishes alliance indicator while disabled (call periodically) |

These can be passed as **suppliers** (callables) so consumers always read the current selection, even if the alliance changes between matches without restarting the robot code.

---

## 4. How It Connects to Targeting

The tag priority list from `get_tag_priority()` tells the vision system which AprilTags to prefer. The alliance's `target_x` and `target_y` provide the Hub position for pose-based aiming.

```python
# Example: getting targeting info from match setup
tag_priority = match_setup.get_tag_priority()  # e.g. [8, 10, 11]
alliance = match_setup.get_alliance()
hub_x = alliance["target_x"]  # e.g. 12.0
hub_y = alliance["target_y"]  # e.g. 4.0
```

---

## 5. How It Will Connect to Autonomous

Each pose has `start_x`, `start_y`, `start_heading`, and `auto_path` fields. These support PathPlanner integration:

- **Starting position** -- set the robot's initial odometry pose from `get_pose()`
- **Auto path** -- use the `auto_path` name to load a PathPlanner trajectory

```python
# Future autonomous setup (not yet implemented)
pose = match_setup.get_pose()
drivetrain.reset_pose(pose["start_x"], pose["start_y"], pose["start_heading"])
if pose["auto_path"]:
    auto_command = PathPlannerAuto(pose["auto_path"])
```

---

## 6. Setting Up SmartDashboard Before a Match

### In Elastic Dashboard

1. Connect to the robot (see [Dashboard Setup](../dashboard-setup.md))
2. Look for **Starting Pose** in the sidebar under SmartDashboard
3. Drag it onto your layout -- it appears as a dropdown widget
4. Drag **Match/Is Red Alliance** onto your layout for a big color indicator:
   - Right-click the widget, change to **Boolean Box**
   - Set **True color** to red, **False color** to blue
   - Resize it big so you can see it from across the pit
5. Select the correct starting pose before each match
6. Save your layout so they're always visible

### In Shuffleboard

1. Connect to the robot
2. The pose chooser appears under SmartDashboard in the sources panel
3. Drag it onto a tab
4. It displays as a dropdown menu

### In Simulation

1. Run `python -m robotpy sim`
2. Open the sim GUI -- the pose chooser appears under SmartDashboard
3. Select values to test different pose combinations

### Pre-match checklist

1. Verify alliance color in the Driver Station app matches your actual alliance
2. Check the **Is Red Alliance** indicator on Elastic to confirm
3. Verify starting pose matches where the robot is placed
4. Double-check after field reset -- the DS remembers the alliance, and the dashboard remembers the pose

---

## 7. Adding a New Pose or Alliance

To add a new starting pose (e.g., "Far Left"):

1. Open `constants/match.py`
2. Add a new dict to the `"poses"` list in each alliance:

```python
{
    "name": "Far Left",
    "start_x": -2.5,
    "start_y": 1.0,
    "start_heading": 45.0,
    "auto_path": "far_left_auto",
},
```

3. That's it -- the SmartDashboard chooser will include it automatically

To change tag priorities, edit the `"tag_priority"` list in the relevant alliance entry.

---

**See also:**

- [Controls & Manual Overrides](controls.md) -- how operator controls work
- [Vision System](vision.md) -- AprilTag detection and the vision abstraction layer
- [Autonomous](autonomous.md) -- autonomous routines (will use match setup for paths)
- [Dashboard Setup](../dashboard-setup.md) -- how to open and configure the dashboard
