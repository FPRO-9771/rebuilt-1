# Auto Sequence Debugging

**Status:** Refactored (2026-03-20) -- switched from EventTrigger to NamedCommands

---

## Background

### Original Problem (2026-03-19)

Robot functions fired at unexpected times during auto -- all event markers triggered in the same cycle. Root cause: `PathPlannerPath.fromPathFile()` called inside `autonomousInit` took ~3.9 seconds of file I/O on the roboRIO. PathPlanner's internal timer skipped ahead and fired all markers it thought it had "passed."

### Fix: Pre-loading (2026-03-19)

Moved path loading to construction time (during `robotInit`). File I/O happens before the match, not during auto.

### Refactor: NamedCommands (2026-03-20)

Replaced the `EventTrigger` approach with PathPlanner `NamedCommands`. The old EventTrigger bindings were global -- commands scheduled by event markers were orphaned when auto ended (they kept running into teleop). The new approach:

1. **`autonomous/named_commands.py`** registers all commands with `NamedCommands.registerCommand()`
2. **`.path` files** have event markers that reference named commands (not `"command": null`)
3. **`.auto` files** are simple `sequential(path)` -- all actions are on the path's event markers
4. **`auton_modes.py`** uses `AutoBuilder.buildAuto()` to load `.auto` files
5. When the path ends, `EventScheduler.end()` cancels all still-running event commands -- clean lifecycle

---

## Architecture Overview

```
robot_container.py
  |-- register_named_commands()     <-- registers all 8 named commands
  |-- AutonModes()                  <-- pre-loads .auto files

robot.py autonomousInit()
  |-- auton_modes.get_auto_command() <-- returns cached PathPlannerAuto
  |-- auto_command.schedule()        <-- starts path following

PathPlanner (during path execution)
  |-- reaches event marker position  <-- fires named command
  |-- path ends                      <-- EventScheduler.end() cancels all
```

### Named Commands

| Name | Command | Requires |
|------|---------|----------|
| IntakeDown | `intake.go_down()` | intake |
| IntakeUp | `intake.go_up()` | intake |
| IntakeStart | `intake_spinner.run_at_voltage()` | intake_spinner |
| IntakeStop | `intake_spinner._stop()` | intake_spinner |
| AimStart | `CoordinateAim` | turret |
| AimStop | `turret._stop()` | turret |
| ShooterStart | `ShootWhenReady` | launcher, hood, h_feed, v_feed |
| ShooterStop | stop all shooter subsystems | launcher, hood, h_feed, v_feed |

---

## Debug Logging

Toggle with `DEBUG["auto_sequence_logging"]` in `constants/debug.py` (currently `True`).

### Log prefixes

| Prefix | Source | What it shows |
|--------|--------|---------------|
| `AUTO SEQ:` | `coordinate_aim.py`, `shoot_when_ready.py`, `auton_modes.py` | Command lifecycle (init/end/milestones) |
| `AUTO PERIODIC [N]:` | `robot.py` | Heartbeat every ~1s, plus finished detection |
| `AUTO EXIT:` | `robot.py` | Total cycle count when auto ends |

> **Note:** The old `AUTO EVENT:` prefix from `robot_container.py` is gone -- the `_log_event` wrapper was removed with EventTrigger. Command start/stop is now logged by each command's own `initialize()` and `end()` methods.

### What to look for in logs

**Healthy auto sequence:**
```
INFO  named_commands: all named commands registered
INFO  auton_modes: pre-loaded auto 'Auto Blue Right' OK
INFO  robot: autonomousInit: fired
INFO  auton_modes: auto 'Auto Blue Right' selected (cached)
INFO  robot: autonomousInit: scheduling PathPlannerAuto
INFO  coordinate_aim: CoordinateAim ENABLED              <-- AimStart marker fired
INFO  intake: TwoPhaseMove DOWN: target=...              <-- IntakeDown marker fired
INFO  intake_spinner: ...                                <-- IntakeStart marker fired
INFO  intake_spinner: _stop: motor to 0V                 <-- IntakeStop marker fired
INFO  shoot_when_ready: ShootWhenReady ENABLED           <-- ShooterStart marker fired
INFO  shoot_when_ready: Launcher reached speed -- unlocked
INFO  coordinate_aim: CoordinateAim ended (interrupted=True)  <-- AimStop marker or path end
INFO  shoot_when_ready: ShootWhenReady DISABLED (interrupted=True)  <-- path end cleanup
INFO  robot: AUTO EXIT: auto ended after N cycles
```

**Problem: markers fire all at once (same timestamp)**
- Path loading is happening during autonomousInit instead of robotInit
- Check that `auton_modes.py` says "pre-loaded auto ... OK" during startup, NOT during auto

**Problem: a command never starts**
- Check the event marker name in the `.path` file matches exactly (case-sensitive)
- Check `named_commands.py` registered that name
- Check the marker's `"command"` field is `{"type": "named", "data": {"name": "..."}}` not `null`

**Problem: a command runs into teleop**
- This should NOT happen with the NamedCommands approach -- EventScheduler cancels all commands when the path ends
- If it does happen, check that `autonomousExit()` is calling `auto_command.cancel()`

---

## Debugging Steps for Tomorrow (2026-03-21)

### Step 1: Verify named commands register

Deploy and check the console during robot startup. You should see:

```
INFO  named_commands: all named commands registered
INFO  auton_modes: pre-loaded auto 'Auto Blue Right' OK
INFO  auton_modes: pre-loaded auto 'Auto Blue Center' OK
...
```

If any auto fails to pre-load, check the `.auto` file JSON and the path name it references.

### Step 2: Run Mini Test first

Mini Test has all 8 named commands on it:
- AimStart -> IntakeDown -> IntakeStart -> ShooterStart + IntakeStop -> IntakeUp -> ShooterStop -> AimStop

Watch the console logs. Each command should log its `initialize()` and `end()` at the right times. If a command doesn't fire, check the event marker in PathPlanner GUI.

### Step 3: Check marker timing

Open the Mini Test path in PathPlanner GUI. Note the waypoint positions of each marker. Then run the auto and watch logs. Commands should fire in order:
1. AimStart at position 0.0 (immediately)
2. IntakeDown at position ~0.1
3. IntakeStart at position 1.0
4. ShooterStart at position 2.4
5. IntakeStop at position 2.4
6. IntakeUp at position 2.5
7. ShooterStop at position 3.3
8. AimStop at position 3.5

If markers fire out of order or too early, the pre-loading fix may not be working.

### Step 4: Test a match auto

Once Mini Test works, try Auto Blue Right (or whichever path matches your field setup). Verify:
- Turret starts aiming when AimStart fires
- Intake arm goes down and wheels spin at the right field positions
- Launcher spins up when ShooterStart fires
- Everything stops cleanly when the path ends

### Step 5: Adjust timing in PathPlanner GUI

If a command fires too early or too late, adjust the `waypointRelativePos` in PathPlanner GUI. You do NOT need to change any Python code -- just move the event marker on the path.

### Step 6: Disable logging for competition

Once everything works, set `DEBUG["auto_sequence_logging"]` to `False` in `constants/debug.py` to reduce console noise during matches.

---

## Files Reference

| File | Role |
|------|------|
| `autonomous/named_commands.py` | Registers all 8 named commands |
| `autonomous/auton_modes.py` | Pre-loads .auto files, provides `get_auto_command()` |
| `autonomous/auton_mode_selector.py` | Test override chooser (SmartDashboard) |
| `robot_container.py` | Calls `register_named_commands()` then creates `AutonModes()` |
| `robot.py` | `autonomousInit` schedules the auto, `autonomousExit` cancels it |
| `constants/debug.py` | `DEBUG["auto_sequence_logging"]` toggle |
| `deploy/pathplanner/paths/*.path` | Path files with event markers |
| `deploy/pathplanner/autos/*.auto` | Auto files (simple path wrappers) |

---

**See also:**
- [Autonomous System](../architecture/autonomous.md) - Full architecture guide
- [Shooter System](../architecture/shooter-system.md) - ShootWhenReady details
- [Intake & Feeding](../architecture/intake-and-feeding.md) - Intake command details
