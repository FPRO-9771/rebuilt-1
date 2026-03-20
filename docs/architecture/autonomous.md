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
5. [Path Selection](#5-path-selection)
6. [AutonModes Factory](#6-autonmodes-factory)
7. [Using in Robot.py](#7-using-in-robotpy)
8. [Adding a New Named Command](#8-adding-a-new-named-command)

---

## 1. How It Works

The autonomous system has four layers:

```
PathPlanner GUI          You place event markers on paths
       |
Named Commands           Python code defines what each marker does
       |
.auto files              Simple wrapper: "follow this path"
       |
AutonModes               Pre-loads .auto files, robot.py picks one at match start
```

**The key idea:** The kids control *when* things happen by placing event markers in PathPlanner GUI. The code defines *what* each marker does by registering named commands. Clean separation.

---

## 2. Named Commands

All named commands are registered in one place: `autonomous/named_commands.py`.

```python
# autonomous/named_commands.py

def register_named_commands(intake, intake_spinner, launcher, hood,
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
        ShootWhenReady(launcher, hood, h_feed, v_feed, ...))
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
| `ShooterStart` | Spin up launcher, set hood, feed when at speed (ShootWhenReady) | Interrupted (by ShooterStop or path end) |
| `ShooterStop` | Stop launcher, hood, and feeders | Instant |

> **ShooterStart = ShootWhenReady.** It handles launcher spin-up, hood positioning, feeding when at speed, and auto-unjam -- all in one command. No need for separate feeder commands.

---

## 3. PathPlanner Event Markers

Event markers are placed on `.path` files in the PathPlanner GUI. Each marker has a name and a position along the path (waypointRelativePos). When the robot reaches that position, PathPlanner fires the named command.

### How to add an event marker in PathPlanner GUI

1. Open a `.path` file in PathPlanner
2. Click on the path where you want the marker
3. Add an Event Marker
4. Set the name to one of the named commands (e.g. `IntakeDown`, `ShooterStart`)
5. The dropdown shows all available named commands

### Example: Auto Blue Right path markers

```
Position 0.0  -> AimStart        (start aiming immediately)
Position 0.6  -> IntakeDown      (lower arm as robot approaches Fuel)
Position 1.75 -> IntakeStart     (spin wheels to collect Fuel)
Position 3.5  -> IntakeStop      (stop wheels after collection)
Position 5.0  -> ShooterStart    (spin up and shoot)
Position 5.8  -> AimStop         (stop aiming near end)
```

### Important rules

- **Start commands need matching stops.** If you place `AimStart`, place `AimStop` later. If you place `ShooterStart`, place `ShooterStop` later. If you forget, the path ending will cancel them automatically -- but explicit stops are clearer.
- **Order matters.** Markers fire in order of their position along the path.
- **The path end cancels everything.** When the path finishes, PathPlanner's EventScheduler calls `end()` on all still-running commands. This is clean -- no orphaned commands.

---

## 4. Auto Files

Each `.auto` file in `deploy/pathplanner/autos/` is a simple wrapper that tells PathPlanner which path to follow:

```json
{
  "version": "2025.0",
  "command": {
    "type": "sequential",
    "data": {
      "commands": [
        {
          "type": "path",
          "data": {
            "pathName": "Auto Blue Right"
          }
        }
      ]
    }
  },
  "resetOdom": true
}
```

The `.auto` file just says "follow this path." All the interesting stuff (when to aim, when to shoot, when to intake) is on the path's event markers.

### Current .auto files

| File | Path |
|------|------|
| `Auto Blue Left.auto` | Auto Blue Left |
| `Auto Blue Center.auto` | Auto Blue Center |
| `Auto Blue Right.auto` | Auto Blue Right |
| `Auto Red Left.auto` | Auto Red Left |
| `Auto Red Center.auto` | Auto Red Center |
| `Auto Red Right.auto` | Auto Red Right |
| `Mini Test.auto` | Mini Test |

---

## 5. Path Selection

The drive team selects a starting pose on the Elastic dashboard before the match. The auto routine is derived from the alliance (Blue/Red from Driver Station) and the pose name (Left/Center/Right from Elastic):

```
Alliance="Blue" + Pose="Right" -> loads "Auto Blue Right.auto"
```

A test override chooser (`Auton Override` on SmartDashboard) can override this for testing. Default is "None" (use the derived routine).

---

## 6. AutonModes Factory

```python
# autonomous/auton_modes.py

class AutonModes:
    def __init__(self):
        # Pre-load all .auto files during robotInit (not autonomousInit!)
        # This avoids file I/O during the 20-second auto period.
        for name in _ALL_AUTO_NAMES:
            self._cached_autos[name] = AutoBuilder.buildAuto(name)

    def get_auto_command(self, alliance_name, pose_name):
        auto_name = f"Auto {alliance_name} {pose_name}"
        return self._cached_autos[auto_name]
```

Key points:
- All `.auto` files are pre-loaded at construction time (during `robotInit`) to avoid file I/O during auto.
- `get_auto_command()` does a dict lookup -- instant.
- Falls back to `WaitCommand(15.0)` if a file fails to load.

---

## 7. Using in Robot.py

```python
# robot.py

def autonomousInit(self):
    self._apply_selected_pose()       # Reset odometry to starting position
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
1. `_apply_selected_pose()` resets drivetrain odometry to the selected starting position.
2. Check for test override; otherwise derive the auto name from alliance + pose.
3. Schedule the cached `PathPlannerAuto` command.
4. `autonomousExit()` cancels the auto command (which cancels all event-scheduled commands).

---

## 8. Adding a New Named Command

1. **Write the command** in `commands/` (or use an existing subsystem method).
2. **Register it** in `autonomous/named_commands.py`:
   ```python
   NamedCommands.registerCommand("MyNewCommand", my_subsystem.do_thing())
   ```
3. **Place it on a path** in PathPlanner GUI as an event marker.
4. **Test it** with Mini Test path first.

That's it. The command is now available in the PathPlanner event marker dropdown for all paths.

---

**See also:**
- [Commands & Controls](commands-and-controls.md) - Command composition patterns
- [Shooter System](shooter-system.md) - ShootWhenReady and CoordinateAim details
- [Intake & Feeding](intake-and-feeding.md) - Intake arm and spinner details
- [Match Setup](match-setup.md) - Pre-match alliance/pose selection
- [Testing & Simulation](testing-and-simulation.md) - Testing auto routines with simulation
