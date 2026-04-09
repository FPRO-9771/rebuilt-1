# Autonomous System

**Team 9771 FPRO - 2026**

This doc covers how autonomous routines work: named commands, PathPlanner event markers, path selection, and how robot.py runs them.

> **When to read this:** You're building or editing auto routines.

---

## Table of Contents

1. [How It Works](#1-how-it-works)
2. [Named Commands](#2-named-commands)
3. [PathPlanner Event Markers](#3-pathplanner-event-markers)
4. [Auto Files](#4-auto-files)
5. [Odometry Reset](#5-odometry-reset)
6. [Path Selection](#6-path-selection)
7. [AutonModes Factory](#7-autonmodes-factory)
8. [Using in Robot.py](#8-using-in-robotpy)
9. [Adding a New Named Command](#9-adding-a-new-named-command)
10. [Adding a New Auto Phase](#10-adding-a-new-auto-phase)

---

## 1. How It Works

The autonomous system has four layers:

```
PathPlanner GUI          You place event markers on paths
       |
Named Commands           Python code defines what each marker does
       |
.auto files              Sequence of paths: "follow pickup, then shoot"
       |
AutonModes               Pre-loads .auto files, robot.py picks one at match start
```

**The key idea:** The kids control *when* things happen by placing event markers in PathPlanner GUI. The code defines *what* each marker does by registering named commands. Clean separation.

### Multi-path pattern

Each auto is split into focused paths, one per phase:

```
Auto Blue Right.auto:
  1. path: "BR Pickup"      (drive to fuel, intake event markers)
  2. path: "BR Shoot"       (return + shoot, aim/shoot event markers)
  3. path: "BR Pickup 2"    (future: drive to more fuel)
```

This makes it easy to add new phases -- just draw a new path and add it to the .auto sequence.

---

## 2. Named Commands

All named commands are registered in one place: `autonomous/named_commands.py`.

```python
# autonomous/named_commands.py

def register_named_commands(intake, intake_spinner, launcher,
                            h_feed, v_feed, turret, context_supplier):
    NamedCommands.registerCommand("IntakeDown", intake.go_down())
    NamedCommands.registerCommand("IntakeUp", intake.go_up())
    NamedCommands.registerCommand("IntakeStart",
        intake_spinner.run_at_voltage(CON_INTAKE_SPINNER["spin_voltage"]))
    NamedCommands.registerCommand("IntakeStop",
        intake_spinner.runOnce(lambda: intake_spinner._stop()))
    NamedCommands.registerCommand("AimStart",
        CoordinateAim(turret, context_supplier, CON_TURRET_MINION))
    NamedCommands.registerCommand("AimStop",
        turret.runOnce(lambda: turret._stop()))
    NamedCommands.registerCommand("ShooterStart",
        ShootWhenReady(launcher, h_feed, v_feed, ...))
    NamedCommands.registerCommand("ShooterStop", ...)
```

Called from `robot_container.py` **before** any .auto files are loaded.

### Available Named Commands

| Name | What It Does | Runs Until |
|------|-------------|------------|
| `IntakeDown` | Lower the intake arm | Arm reaches position |
| `IntakeUp` | Raise the intake arm | Arm reaches position |
| `IntakeStart` | Spin intake wheels to pull in Fuel | Interrupted (by IntakeStop or path end) |
| `IntakeStop` | Stop intake wheels | Instant |
| `AimStart` | Turret auto-aim at Hub (CoordinateAim) | Interrupted (by AimStop or path end) |
| `AimStop` | Stop turret | Instant |
| `ShooterStart` | Spin up launcher, feed when at speed (ShootWhenReady) | Interrupted (by ShooterStop or path end) |
| `ManualShootStart` | Manual shoot at center distance (for center autos) | Interrupted (by ShooterStop or path end) |
| `ShooterStop` | Stop launcher and feeders | Instant |

> **ShooterStart = ShootWhenReady.** It handles launcher spin-up, feeding when at speed, and auto-unjam -- all in one command. No need for separate feeder commands.

---

## 3. PathPlanner Event Markers

Event markers are placed on `.path` files in the PathPlanner GUI. Each marker has a name and a position along the path (waypointRelativePos). When the robot reaches that position, PathPlanner fires the named command.

### How to add an event marker in PathPlanner GUI

1. Open a `.path` file in PathPlanner
2. Click on the path where you want the marker
3. Add an Event Marker
4. Set the name to one of the named commands (e.g. `IntakeDown`, `ShooterStart`)
5. The dropdown shows all available named commands

### Example: BR Pickup path markers

```
Position 0.1  -> IntakeDown      (lower arm at path start)
Position 1.5  -> IntakeStart     (spin wheels approaching Fuel)
Position 3.8  -> IntakeStop      (stop wheels after collection)
```

### Example: BR Shoot path markers

```
Position 0.0  -> AimStart        (start aiming immediately)
Position 0.5  -> ShooterStart    (spin up launcher)
Position 2.0  -> ShooterStop     (stop shooting at path end)
Position 2.0  -> AimStop         (stop aiming at path end)
```

### Important rules

- **Start commands need matching stops.** If you place `AimStart`, place `AimStop` later. If you place `ShooterStart`, place `ShooterStop` later. If you forget, the path ending will cancel them automatically -- but explicit stops are clearer.
- **Order matters.** Markers fire in order of their position along the path.
- **The path end cancels everything.** When the path finishes, PathPlanner's EventScheduler calls `end()` on all still-running commands. This is clean -- no orphaned commands.

---

## 4. Auto Files

Each `.auto` file in `deploy/pathplanner/autos/` sequences one or more paths:

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
  "resetOdom": true
}
```

The `.auto` file says "follow these paths in order." All the interesting stuff (when to aim, when to shoot, when to intake) is on each path's event markers.

### Current .auto files

| File | Paths |
|------|-------|
| `Auto Blue Left.auto` | BL Pickup -> BL Shoot |
| `Auto Blue Center.auto` | BC Drive -> BC Shoot |
| `Auto Blue Right.auto` | BR Pickup -> BR Shoot |
| `Mini Test.auto` | Mini Test |

### Current .path files

| Phase | Path | Event Markers |
|-------|------|---------------|
| BR Pickup | `BR Pickup.path` | IntakeDown, IntakeStart, IntakeStop |
| BR Shoot | `BR Shoot.path` | AimStart, ShooterStart, ShooterStop, AimStop |
| BL Pickup | `BL Pickup.path` | IntakeDown, IntakeStart, IntakeStop |
| BL Shoot | `BL Shoot.path` | AimStart, ShooterStart, ShooterStop, AimStop |
| BC Drive | `BC Drive.path` | (none -- just driving) |
| BC Shoot | `BC Shoot.path` | ManualShootStart, ShooterStop |
| Mini Test | `Mini Test.path` | IntakeDown, IntakeStart, IntakeStop, ShooterStart, IntakeUp, ShooterStop |

> **No Red files.** PathPlanner auto-flips Blue paths for Red alliance. The code always loads `"Auto Blue {pose_name}"`.

---

## 5. Odometry Reset

PathPlanner handles odometry reset automatically. Each `.auto` file has `"resetOdom": true`, which tells PathPlanner to reset the robot's odometry to the first waypoint of the first path when the auto starts.

**No manual pose code needed.** The starting position is defined by the path's first waypoint in the PathPlanner GUI. The `constants/match.py` file does NOT store starting coordinates -- PathPlanner is the source of truth.

The `AutoBuilder.configure()` call in `command_swerve_drivetrain.py` provides the `reset_pose` callback that PathPlanner uses.

---

## 6. Path Selection

The drive team selects a starting pose on the Elastic dashboard before the match. The auto routine is derived from the alliance (Blue/Red from Driver Station) and the pose name (Left/Center/Right from Elastic):

```
Alliance="Blue" + Pose="Right" -> loads "Auto Blue Right.auto"
```

A test override chooser (`Auton Override` on SmartDashboard) can override this for testing. Default is "None" (use the derived routine).

---

## 7. AutonModes Factory

```python
# autonomous/auton_modes.py

class AutonModes:
    def __init__(self):
        # Validate all .auto files during robotInit (not autonomousInit!)
        # This catches missing/broken files early.
        for name in _ALL_AUTO_NAMES:
            AutoBuilder.buildAuto(name)

    def get_auto_command(self, alliance_name, pose_name):
        auto_name = f"Auto Blue {pose_name}"
        return self._load_auto(auto_name)
```

Key points:
- All `.auto` files are validated at construction time (during `robotInit`).
- `get_auto_command()` always loads Blue paths -- PathPlanner flips for Red.
- Commands are built fresh each call (WPILib commands are single-use).
- Falls back to `WaitCommand(15.0)` if a file fails to load.

---

## 8. Using in Robot.py

```python
# robot.py

def autonomousInit(self):
    # Test override takes priority
    test_factory = self.container.test_chooser.getSelected()
    if test_factory is not None:
        self.auto_command = test_factory()
    else:
        alliance_name = self.container.match_setup.get_alliance()["name"]
        pose_name = self.container.match_setup.get_pose_name()
        self.auto_command = self.container.auton_modes.get_auto_command(
            alliance_name, pose_name)
    self.auto_command.schedule()

def autonomousExit(self):
    if self.auto_command:
        self.auto_command.cancel()
```

The flow:
1. PathPlanner resets odometry via `resetOdom: true` in the .auto file.
2. Check for test override; otherwise derive the auto name from alliance + pose.
3. Build a fresh `PathPlannerAuto` command and schedule it.
4. `autonomousExit()` cancels the auto command (which cancels all event-scheduled commands).

---

## 9. Adding a New Named Command

1. **Write the command** in `commands/` (or use an existing subsystem method).
2. **Register it** in `autonomous/named_commands.py`:
   ```python
   NamedCommands.registerCommand("MyNewCommand", my_subsystem.do_thing())
   ```
3. **Place it on a path** in PathPlanner GUI as an event marker.
4. **Test it** with Mini Test path first.

That's it. The command is now available in the PathPlanner event marker dropdown for all paths.

---

## 10. Adding a New Auto Phase

To add a new phase to an existing auto (e.g., a second pickup run after shooting):

1. **Draw a new path** in PathPlanner GUI (e.g., `BR Pickup 2.path`).
   - Start it where the previous path ends.
   - Add event markers for the commands you want.
2. **Add the path** to the `.auto` file's command sequence:
   ```json
   { "type": "path", "data": { "pathName": "BR Pickup 2" } }
   ```
3. **Test in simulation** first (`python -m robotpy sim`).

The odometry carries over between paths in the same .auto -- no special handling needed.

---

**See also:**
- [Commands & Controls](commands-and-controls.md) - Command composition patterns
- [Shooter System](shooter-system.md) - ShootWhenReady and CoordinateAim details
- [Intake & Feeding](intake-and-feeding.md) - Intake arm and spinner details
- [Match Setup](match-setup.md) - Pre-match alliance/pose selection
- [Testing & Simulation](testing-and-simulation.md) - Testing auto routines with simulation
