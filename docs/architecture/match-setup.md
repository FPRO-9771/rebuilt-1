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

Before each match, the drive team selects two things on the dashboard:

- **Alliance** -- Red or Blue
- **Starting Pose** -- where the robot starts on the field (Left, Center, Right)

This selection determines:

- Which AprilTags the auto-shooter tracks and in what priority order
- Per-tag aiming offsets for the turret
- The robot's starting position on the field (for odometry and PathPlanner)
- Which autonomous path to run (future)

All of this lives in `constants/match.py` so the team can tune it without touching any logic code.

---

## 2. Configuration (constants/match.py)

The `ALLIANCES` list is the single source of truth. Each alliance is a dict with tag priorities, per-tag offsets, and a list of starting poses:

```python
ALLIANCES = [
    {
        "name": "Red",
        "default": True,           # Pre-selected in SmartDashboard
        "tag_priority": [8, 9, 10, 11],  # Ordered: first visible wins
        "tag_offsets": {
            8:  {"tx_offset": 0.0, "distance_offset": 0.0},
            # ... one entry per tag
        },
        "poses": [
            {
                "name": "Center",
                "default": True,
                "start_x": 0.0,         # Field coordinates (meters)
                "start_y": 0.0,
                "start_heading": 0.0,   # Degrees
                "auto_path": "",        # PathPlanner path name
            },
            # ... Left, Right
        ],
    },
    # ... Blue alliance
]
```

### Tag priority

The `tag_priority` list controls which AprilTag the turret locks onto. The auto-tracker walks the list in order and locks onto the **first visible tag**. This means:

- Tag 8 is checked first. If the camera sees it, the turret locks on.
- If tag 8 is not visible, tag 9 is checked, then 10, then 11.
- Once locked, the turret stays on that tag even if a higher-priority tag briefly appears (stickiness prevents oscillation).

### Tag offsets

Each tag has a `tx_offset` (degrees) and `distance_offset` (meters) to correct for the fact that the tag is not at the exact center of the Hub. These start at zero and get tuned on the real robot.

### Stickiness

`TARGET_LOCK_LOST_CYCLES` (also in `constants/match.py`) controls how long the tracker holds a lock after losing sight of the tag. At 50 Hz, the default of 10 cycles = 200 ms of grace period before the tracker releases and picks a new tag.

---

## 3. SmartDashboard Choosers

`match_setup.py` creates two `SendableChooser` widgets and publishes them to SmartDashboard:

| Chooser | Key | Options |
|---------|-----|---------|
| Alliance | `Alliance` | One per entry in `ALLIANCES` |
| Starting Pose | `Starting Pose` | Union of all pose names across alliances |

The choosers are built dynamically from the `ALLIANCES` config. Adding a new pose or alliance to `constants/match.py` automatically adds it to the dashboard -- no code changes needed.

### How it's created

`RobotContainer.__init__` creates a `MatchSetup` instance:

```python
# robot_container.py
from match_setup import MatchSetup

class RobotContainer:
    def __init__(self):
        self.match_setup = MatchSetup()  # Publishes choosers
        # ...
```

### What it provides

Other code calls these methods on `match_setup`:

| Method | Returns |
|--------|---------|
| `get_alliance()` | The full alliance dict |
| `get_pose_name()` | The selected pose name string |
| `get_pose()` | The full pose dict for the selected alliance + pose |
| `get_tag_priority()` | The ordered tag ID list |
| `get_tag_offsets()` | The per-tag offsets dict |

These are passed as **suppliers** (callables) so the auto-tracker always reads the current selection, even if the kids change it between matches without restarting the robot code.

---

## 4. How It Connects to Targeting

The `AutoTracker` command (turret default command) receives two suppliers:

```python
tracker = AutoTracker(
    turret, vision,
    tag_priority_supplier=match_setup.get_tag_priority,
    tag_offsets_supplier=match_setup.get_tag_offsets,
)
```

Every cycle, the tracker:

1. Calls `tag_priority_supplier()` to get the current priority list
2. If locked on a tag, tries to keep tracking it (stickiness)
3. If no lock, walks the priority list and locks onto the first visible tag
4. Applies the tag's offsets from `tag_offsets_supplier()`

This eliminates the oscillation bug where the old code would flip between two equidistant tags every cycle.

---

## 5. How It Will Connect to Autonomous

Each pose has `start_x`, `start_y`, `start_heading`, and `auto_path` fields. These are placeholders for PathPlanner integration:

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
2. Look for **Alliance** and **Starting Pose** in the sidebar under SmartDashboard
3. Drag both onto your layout -- they appear as dropdown widgets
4. Drag **Match/Is Red Alliance** onto your layout for a big color indicator:
   - Right-click the widget, change to **Boolean Box**
   - Set **True color** to red, **False color** to blue
   - Resize it big so you can see it from across the pit
5. Select the correct alliance and starting pose before each match
6. Save your layout so they're always visible

### In Shuffleboard

1. Connect to the robot
2. The choosers appear under SmartDashboard in the sources panel
3. Drag them onto a tab
4. They display as dropdown menus

### In Simulation

1. Run `python -m robotpy sim`
2. Open the sim GUI -- the choosers appear under SmartDashboard
3. Select values to test different alliance/pose combinations

### Pre-match checklist

1. Verify alliance matches your actual alliance color
2. Verify starting pose matches where the robot is placed
3. Double-check after field reset -- the dashboard remembers the last selection

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

To add tag offsets for a new tag, add an entry to the alliance's `"tag_offsets"` dict and include the tag ID in `"tag_priority"`.

---

**See also:**

- [Controls & Manual Overrides](controls.md) -- how the auto-tracker fits into operator controls
- [Vision System](vision.md) -- AprilTag detection and the vision abstraction layer
- [Autonomous](autonomous.md) -- autonomous routines (will use match setup for paths)
- [Dashboard Setup](../dashboard-setup.md) -- how to open and configure the dashboard
