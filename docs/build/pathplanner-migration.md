# Plan: Migrate Autonomous to PathPlanner Best Practices

## Context

During competition, the team was editing auto code under pressure and ended up with a setup that works but doesn't use PathPlanner correctly:
- Odometry is reset manually in Python (`_apply_selected_pose()`) instead of letting PathPlanner handle it via `resetOdom: true`
- All command sequencing lives in complex `.auto` file command groups (deadline groups, waits) instead of event markers on `.path` files
- `.path` files have **empty** `eventMarkers` arrays (except Mini Test)
- The team wants to add more auto phases (e.g., drive after shooting) and the current structure makes that hard

**Goal:** Migrate to the standard PathPlanner pattern -- multiple focused paths per auto, event markers on paths, simple .auto sequencing, and PathPlanner-managed odometry.

---

## Part 1: Migrate Odometry to PathPlanner

PathPlanner's `resetOdom: true` calls the `reset_pose` callback (already configured in `command_swerve_drivetrain.py:249`) with the first waypoint's position and the `idealStartingState` rotation from the first path. This is the standard approach.

### Files to change

**`deploy/pathplanner/autos/*.auto`** -- Set `"resetOdom": true` in all Blue .auto files and Mini Test.

**`robot.py`** -- Remove `_apply_selected_pose()` method (lines 36-45) and the call to it in `autonomousInit` (line 58). Remove the `Pose2d, Rotation2d` import (line 8) since nothing else uses them.

**`constants/match.py`** -- Remove `start_x`, `start_y`, `start_heading`, `auto_path` from all pose dicts. The path's first waypoint is now the source of truth. Simplify to:
```python
_POSES = [
    {"name": "Center", "default": True},
    {"name": "Left"},
    {"name": "Right"},
]
```
Share `_POSES` between Red and Blue alliances (they have the same pose names). Keep `target_x`, `target_y`, `tag_priority`, `HUB_RESET_POSES`, etc.

**`match_setup.py`** -- Delete the `get_pose()` method (lines 73-90). Its only caller was `_apply_selected_pose()`. Keep `get_alliance()`, `get_pose_name()`, `get_tag_priority()`, `update()`.

---

## Part 2: Multi-Path Auto Structure with Event Markers

### Pattern

Each auto is split into focused paths, one per phase:

```
Auto Blue Right.auto:
  1. path: "BR Pickup"      (drive to fuel, intake event markers)
  2. path: "BR Shoot"       (hold/short move to shooting pos, aim+shoot event markers)
  3. path: "BR Pickup 2"    (future: drive to more fuel)
```

Event markers on each path control what happens during that phase. The .auto just sequences paths.

### New path files to create

For each existing auto, split into phase paths. The kids will need to draw these in the PathPlanner GUI. We set up the scaffolding:

**Blue Right:**
- `BR Pickup.path` -- Waypoints from current Auto Blue Right.path (waypoints 0-4, the outbound pickup leg). Event markers: `IntakeDown` at ~0.1, `IntakeStart` at ~1.5, `IntakeStop` near end.
- `BR Shoot.path` -- Waypoints from current Auto Blue Right.path (waypoints 4-6, the return + shooting position). Event markers: `AimStart` at ~0.0, `ShooterStart` at ~0.5, `ShooterStop` near end, `AimStop` near end.

**Blue Left:** Same pattern, mirrored.
- `BL Pickup.path` + `BL Shoot.path`

**Blue Center:**
- `BC Drive.path` -- Current Auto Blue Center.path waypoints. Event markers: `ManualShootStart` near end (or `AimStart` + `ShooterStart` if switching to auto-aim).
- `BC Shoot.path` -- Short hold path. Event markers: `ManualShootStart` at start, `ShooterStop` near end.

**Mini Test:** Already has event markers on its path. Keep as-is but simplify its .auto.

### .auto file structure (example: Auto Blue Right)

```json
{
  "version": "2025.0",
  "command": {
    "type": "sequential",
    "data": {
      "commands": [
        { "type": "path", "data": { "pathName": "BR Pickup" } },
        { "type": "path", "data": { "pathName": "BR Shoot" } }
      ]
    }
  },
  "resetOdom": true,
  "folder": null,
  "choreoAuto": false
}
```

Clean and simple -- just a sequence of paths. All timing is visual on the paths.

### Important: Splitting the existing paths

The current `Auto Blue Right.path` has 7 waypoints (positions 0-6). We need to split this into two paths where the second path starts where the first ends. PathPlanner handles this cleanly -- the robot's odometry carries over between paths in the same .auto.

**Approach:** We'll create placeholder .path files with the correct starting/ending waypoints extracted from the current paths. The kids then refine them in the PathPlanner GUI. This is better than trying to perfectly split the JSON by hand.

---

## Part 3: Cleanup

### Delete Red .auto and .path files
`auton_modes.py` always loads `"Auto Blue {pose_name}"` and PathPlanner auto-flips for Red. Red files are unused:
- Delete: `Auto Red Left.auto`, `Auto Red Center.auto`, `Auto Red Right.auto`
- Delete: `Auto Red Left.path`, `Auto Red Center.path`, `Auto Red Right.path`
- Delete: `New Path.path` (leftover empty file)

### Update `_ALL_AUTO_NAMES` in `autonomous/auton_modes.py`
Remove Red auto names from the validation list (line 26-29).

### Keep old Blue .path files temporarily
Rename to `_OLD Auto Blue Right.path` etc. so the kids can reference them when drawing the new split paths in the GUI. Delete after paths are finalized.

---

## Part 4: Update Docs

- `docs/architecture/autonomous.md` -- Update to reflect multi-path pattern, resetOdom: true, removed pose constants
- Remove references to `start_x`/`start_y`/`start_heading` from docs

---

## Implementation Order

1. **Part 1 first (odometry migration)** -- This is independent of the path restructuring. Change resetOdom, remove `_apply_selected_pose`, clean up constants. Test that the robot starts at the correct position.

2. **Part 3 cleanup (delete Red files)** -- Quick win, reduces clutter.

3. **Part 2 (multi-path + event markers)** -- Start with Mini Test (simplify its .auto). Then Blue Center (simplest real auto). Then Blue Right/Left. For each:
   - Create the new split .path files with placeholder waypoints
   - Add event markers to each path
   - Simplify the .auto to just sequence the paths
   - The kids refine waypoints in PathPlanner GUI

4. **Part 4 (docs)** -- After code changes are verified.

---

## Lessons Learned (from Mini Test testing on 2026-03-26)

These are gotchas we hit while getting Mini Test working on the robot. Keep these in mind when building the remaining autos.

### 1. Event markers MUST have a `command` field -- `null` does NOT work

When you add an event marker in PathPlanner GUI, the `name` field is just a label. PathPlannerLib does **not** look up the command by name automatically. The `command` field in the JSON must explicitly reference the named command:

```json
{
  "name": "IntakeDown",
  "waypointRelativePos": 0.25,
  "endWaypointRelativePos": null,
  "command": {
    "type": "named",
    "data": {
      "name": "IntakeDown"
    }
  }
}
```

If `"command": null`, the marker fires a trigger event but **no command runs**. The robot follows the path fine but nothing happens.

**How to get it right in the GUI:** When adding an event marker, make sure you select the named command from the dropdown in the command section -- don't just type a name in the marker name field and leave the command blank.

### 2. Sequential named commands block each other

In a `.auto` file, if you put two named commands in a **sequential** group, the first one must finish before the second starts. Commands like `AimStart` (CoordinateAim) and `ShooterStart` (ShootWhenReady) run forever -- they never finish on their own. So putting them in sequence means the second one never runs.

**Fix:** Use a **Parallel Deadline Group** in the PathPlanner GUI:
- First command = a **Wait** (e.g., 3.0 seconds) -- this is the "deadline"
- Other commands = AimStart, ShooterStart -- these run in parallel
- When the wait finishes, it kills everything in the group

In the GUI this is called "Parallel Deadline Group" in the command type dropdown.

### 3. Don't edit .auto JSON by hand if you need to use the GUI later

The PathPlanner GUI may rewrite the .auto file structure when you save. If you edit JSON by hand (e.g., to add a deadline group), opening and saving in the GUI can flatten it back to sequential. **Build command groups in the GUI** so they persist when re-saved.

### 4. The working Mini Test pattern

This is the pattern that works and was verified on the robot:

**Mini Test.path** -- event markers for intake (IntakeDown, IntakeStart, IntakeStop) with `command` fields populated.

**Mini Test.auto** -- built in the PathPlanner GUI:
1. Path: "Mini Test" (intake markers fire during path)
2. Parallel Deadline Group: [Wait 3s, AimStart, ShooterStart]

The path handles intake. The deadline group after the path handles stationary aiming + shooting for 3 seconds.

---

## Remaining Work

The following paths still need the `command` field fix (currently have `"command": null`):
- `BR Pickup.path` -- IntakeDown, IntakeStart, IntakeStop markers
- `BR Shoot.path` -- AimStart, ShooterStart, ShooterStop, AimStop markers
- `BL Pickup.path` -- IntakeDown, IntakeStart, IntakeStop markers
- `BL Shoot.path` -- AimStart, ShooterStart, ShooterStop, AimStop markers
- `BC Shoot.path` -- ManualShootStart, ShooterStop markers

These placeholder paths also need waypoints refined in the PathPlanner GUI. The old paths are saved as `_OLD Auto Blue *.path` for reference.

---

## Verification

1. `python -m pytest tests/ -v` -- Existing tests should pass (they don't test auto sequencing)
2. `python -m robotpy sim` -- Run simulation:
   - Verify odometry resets to correct position (check SmartDashboard pose)
   - Verify event markers fire in correct order (check "NAMED CMD" log messages)
   - Verify Red alliance auto-flip works
   - Verify test override chooser still works
3. Check that all .auto files load without errors at startup (watch for "could not validate auto" warnings)

---

## Critical Files

| File | Action |
|------|--------|
| `robot.py` | Remove `_apply_selected_pose()` and its call, remove Pose2d import |
| `constants/match.py` | Remove pose coordinates, simplify to name-only dicts |
| `match_setup.py` | Delete `get_pose()` method |
| `autonomous/auton_modes.py` | Remove Red names from `_ALL_AUTO_NAMES`, add new path names |
| `deploy/pathplanner/autos/Auto Blue Right.auto` | Simplify to sequential paths, resetOdom: true |
| `deploy/pathplanner/autos/Auto Blue Left.auto` | Same |
| `deploy/pathplanner/autos/Auto Blue Center.auto` | Same |
| `deploy/pathplanner/autos/Mini Test.auto` | Simplify, resetOdom: true |
| `deploy/pathplanner/paths/BR Pickup.path` | New: pickup phase with intake markers |
| `deploy/pathplanner/paths/BR Shoot.path` | New: shoot phase with aim/shoot markers |
| `deploy/pathplanner/paths/BL Pickup.path` | New: pickup phase |
| `deploy/pathplanner/paths/BL Shoot.path` | New: shoot phase |
| `deploy/pathplanner/paths/BC Drive.path` | New: drive phase |
| `deploy/pathplanner/paths/BC Shoot.path` | New: shoot phase |
| `autonomous/named_commands.py` | No changes needed -- commands are already correct |
| `docs/architecture/autonomous.md` | Update to reflect new patterns |
