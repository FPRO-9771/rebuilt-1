# Auto Sequence Debugging

**Status:** In progress (2026-03-19)

---

## Problem

Robot functions firing at unexpected times during auto -- actions don't line up with where event markers are placed in PathPlanner paths.

## Root Cause Found

`PathPlannerPath.fromPathFile()` was called inside `autonomousInit`, taking ~3.9 seconds of file I/O on the roboRIO. By the time the path command started executing, PathPlanner's internal timer was already ~4 seconds ahead. It immediately fired all event markers it thought it had "passed" -- so IntakeStart, IntakeStop, and ShooterStart all triggered in the same cycle. IntakeStop killed the spinner the instant IntakeStart turned it on.

## Fix Applied

Moved path loading to construction time (during `robotInit`, before the match). All paths are now pre-loaded into `AutonModes._cached_paths` so `autonomousInit` just does a dict lookup -- no file I/O.

**Changed files:**
- `autonomous/auton_modes.py` -- added `_ALL_PATH_NAMES` list and `_cached_paths` dict; `follow_path()` uses cache
- `constants/debug.py` -- added `"auto_sequence_logging"` flag
- `robot.py` -- added `AUTO PERIODIC` and `AUTO EXIT` logging in `autonomousPeriodic`/`autonomousExit`
- `robot_container.py` -- wrapped each `EventTrigger` binding with a logging `InstantCommand`
- `commands/coordinate_aim.py` -- added `AUTO SEQ` logging at initialize/end
- `commands/shoot_when_ready.py` -- added `AUTO SEQ` logging at initialize/end/speed-reached

## Debug Logging

Toggle with `DEBUG["auto_sequence_logging"]` in `constants/debug.py` (currently `True`).

All auto debug lines are prefixed for easy grep:

| Prefix | Source | What it shows |
|--------|--------|---------------|
| `AUTO EVENT:` | `robot_container.py` | PathPlanner event marker fired |
| `AUTO SEQ:` | `coordinate_aim.py`, `shoot_when_ready.py`, `auton_modes.py` | Command lifecycle (init/end/milestones) |
| `AUTO PERIODIC [N]:` | `robot.py` | Heartbeat every ~1s, plus finished detection |
| `AUTO EXIT:` | `robot.py` | Total cycle count when auto ends |

## TODO

- [ ] Add timestamps to `AUTO EVENT` log lines so they can be compared directly against PathPlanner waypoint positions/expected timing
- [ ] Re-run Auto Blue Right with the path pre-loading fix and verify event markers fire at the correct times
- [ ] Check other paths (Auto Blue Left, Auto Blue Center, Red paths) for similar issues
- [ ] Once timing is confirmed correct, set `auto_sequence_logging` to `False` for competition
