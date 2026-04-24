# CLAUDE.md - Team 9771 FPRO Robot 2026

## About the Team

- **FRC Team 9771 - FPRO**
- **Location:** Frankfort, Michigan
- **Season:** 2026 (Rebuilt)

### Code Team
- **Brian** - Coding mentor
- **Caleb** - 9th grade
- **Seb** - 8th grade
- **Toby** - 6th grade

## The Game: REBUILT (2026)

Two 3-robot alliances compete to **score Fuel into the Hub**, **cross field obstacles**, and **climb the Tower**.

**Fuel** -- 5.9 in (15 cm) high-density foam balls. Human players feed Fuel onto the field through the Chute and Outpost. Robots collect Fuel from the Neutral Zone and score it into their alliance's Hub (1 pt each in both auto and teleop).

**Hub** -- each alliance has one Hub. During teleop the Hubs alternate between Active and Inactive across four 25-second Shifts. The alliance that scores more Fuel in Auto has its Hub go Inactive first (Shifts 1 & 3 inactive, Shifts 2 & 4 active). Fuel scored into an Inactive Hub is worth 0 match points. Both Hubs are Active during Auto, the Transition, and Endgame.

**Tower** -- a central climbing structure with three rungs (Low 27 in, Mid 45 in, High 63 in). Climbing earns Tower points:
- Level 1 (off carpet): 10 pts teleop / 15 pts auto (max 2 robots in auto)
- Level 2 (bumpers above Low Rung): 20 pts
- Level 3 (bumpers above Mid Rung): 30 pts
A robot may only score one Tower level during teleop.

**Obstacles** -- Bump (6.5 in tall, drive over) and Trench (40.25 in tall, drive under) divide the field.

**Match timeline (2 min 40 sec total):**
| Phase | Duration | Notes |
|-------|----------|-------|
| Auto | 20 sec | Both Hubs active |
| Transition | 10 sec | Both Hubs active |
| Shifts 1-4 | 4 x 25 sec | Hubs alternate active/inactive |
| Endgame | 30 sec | Both Hubs active |

**Ranking Points (RP):**
- Win: 3 RP, Tie: 1 RP
- Energized: score >= 100 Fuel (1 RP)
- Supercharged: score >= 360 Fuel (1 RP)
- Traversal: earn >= 50 Tower points (1 RP)

**Key vocabulary:** Fuel, Hub (Active/Inactive), Tower, Rung (Low/Mid/High), Shift, Bump, Trench, Outpost, Chute, Neutral Zone, Alliance Wall, Energized, Supercharged, Traversal

**Official resources:**
- [Game & Season page](https://www.firstinspires.org/programs/frc/game-and-season)
- [2026 Game Manual (PDF)](https://firstfrc.blob.core.windows.net/frc2026/Manual/2026GameManual.pdf)
- [Game Data details (WPILib)](https://docs.wpilib.org/en/stable/docs/yearly-overview/2026-game-data.html)
- [Field dimension drawings (PDF)](https://firstfrc.blob.core.windows.net/frc2026/FieldAssets/2026-field-dimension-dwgs.pdf)

## Project Summary

RobotPy (Python) codebase for an FRC competition robot using the WPILib command-based framework with Phoenix 6 motor controllers. This is a starting-point codebase for the 2026 season built on lessons learned from 2025.

**Hardware note:** The robot has **two Limelights** (`limelight-left` at `10.97.71.11` and `limelight-right` at `10.97.71.12`), fixed-mounted off the back of the chassis and pointed left and right respectively. Both feed MegaTag2 pose estimates into the drivetrain every loop via `drivetrain.vision_pose_correct()`. See `docs/architecture/vision.md` for the full flow.

## Code Principles

1. **DRY (Don't Repeat Yourself)** - Configuration lives in `constants/`, not scattered through code
2. **Separation of Concerns** - Hardware abstraction in `hardware/`, subsystems own their mechanisms, commands handle actions
3. **Testable Modules** - All hardware access goes through abstractions that can be mocked for testing
4. **No Magic Numbers** - All values (CAN IDs, voltages, limits) defined in constants
5. **Command Ownership** - Subsystems expose commands; commands always call `addRequirements()`
6. **Small Files** - Keep every module short and focused (under ~100 lines). One interface, class, or concept per file. Split early — the team includes new Python learners who need to read files top-to-bottom

## Testing Rule: Never Hardcode Constants in Tests

Tests must stay green when the team tunes values in `constants/`. **Never use hardcoded numbers that depend on specific constant values.** Instead:

- **Derive expected values from the constants themselves.** For example, use `CON_TURRET_MINION["max_voltage"] * CON_TURRET_MINION["manual_speed_factor"]` — not `0.4`.
- **Compute safe positions from limits.** When a test needs the motor away from soft limits, calculate the midpoint: `(CON_TURRET_MINION["min_position"] + CON_TURRET_MINION["max_position"]) / 2` — not a hardcoded `-10`.
- **Check behavior, not specific numbers, where possible.** Prefer `assert voltage > 0` or `assert voltage != 0` over asserting an exact value, when the test is verifying direction or activity rather than a formula.

This matters because the team frequently adjusts voltages, positions, and speed factors during tuning. A constant change in `constants/` should never require editing test files.

## Logging: Use the Unified Logger

All logging goes through `utils.logger.get_logger()`. **Never use `print()` or raw `logging.getLogger()`.** The unified logger routes messages to both the console and the FRC Driver Station automatically.

**Setup pattern** — at the top of any file that needs logging:

```python
from utils.logger import get_logger

_log = get_logger("subsystem_name")   # e.g. "turret", "launcher", "hardware"
```

**Log levels and where they go:**

| Level | Use for | Destination |
|-------|---------|-------------|
| `_log.debug(...)` | Internal state, parameter values, control flow | Console only |
| `_log.info(...)` | Initialization, configuration, state transitions | Console only |
| `_log.warning(...)` | Unusual conditions (unwired motors, limits) | Console + Driver Station |
| `_log.error(...)` | Failures that affect robot operation | Console + Driver Station |

**Rules:**
- **ASCII only in log strings.** Non-ASCII characters (em dashes `--`, en dashes, smart quotes, etc.) crash the roboRIO. Use only plain ASCII in all `_log` messages, string constants, and comments. Write `--` not `--`, `"` not `"`, `'` not `'`.
- Logger name should match the module/subsystem (e.g. `get_logger("turret_minion")` in `subsystems/turret_minion.py`)
- Use f-strings with relevant values: `_log.debug(f"_set_position: requested={position:.4f} clamped={clamped:.4f}")`
- Verbosity is controlled by `DEBUG["verbose"]` in `constants/debug.py` -- don't add your own level toggling
- WARNING and ERROR appear on the Driver Station during matches, so keep those messages concise and actionable

## IMPORTANT: Read Docs First

**Before reading or modifying ANY code, read the relevant docs below.** The docs are the authoritative reference for how this codebase is structured, what patterns we use, and why. Jumping straight into code without reading the docs first will lead to mistakes -- wrong patterns, duplicated work, or changes that break conventions. Always start here.

**Why this matters:** The docs are kept in sync with code (as of 2026-03-19). Reading the right doc first gives you the architecture, constants, patterns, and current status of each subsystem in one pass -- far faster than exploring the codebase file by file. For any task:

1. **Identify which docs are relevant** from the table below (often 1-3 docs).
2. **Read those docs fully** before opening any source files.
3. **Then read code** only for the specific files the docs point you to.

This approach avoids wasted tool calls and context window. The docs tell you what exists, what's disabled, and where to look.

| Document | Description |
|----------|-------------|
| `docs/2026-robot-code-guide.md` | High-level overview, project structure, config management, quick reference tables, workflow, and lessons learned |
| `docs/architecture/hardware-and-subsystems.md` | Hardware abstraction layer and subsystem design patterns |
| `docs/architecture/commands-and-controls.md` | Command-based architecture and controller bindings |
| `docs/architecture/shooter-system.md` | Shooter subsystems, distance lookup table, and orchestrator |
| `docs/architecture/intake-and-feeding.md` | Intake arm/spinner and H-feed/V-feed subsystems, Fuel path, hopper agitate |
| `docs/architecture/auto-aim.md` | Auto-aim deep dive: pose-based turret aiming, PD controller, movement compensation, debugging (DISABLED) |
| `docs/architecture/controls.md` | Binding extraction pattern, GameController wrapper, operator control map |
| `docs/architecture/match-setup.md` | Pre-match alliance/pose selection, tag priorities, SmartDashboard choosers |
| `docs/architecture/autonomous.md` | Autonomous system: routines, constants, chooser setup |
| `docs/architecture/drivetrain.md` | Swerve drivetrain setup with Phoenix Tuner X |
| `docs/architecture/vision.md` | Vision system (Limelight), abstraction layer, and testing |
| `docs/architecture/testing-and-simulation.md` | Testing with mocks, physics simulation, and calibration |
| `docs/architecture/telemetry.md` | Telemetry dashboard module, published keys, and how to extend |
| `docs/dashboard-setup.md` | How to open Shuffleboard / Glass / Elastic and view live telemetry |
| `docs/drive-team-dashboard.md` | Drive team dashboard: pre-match setup tab and driving tab layout |
| `docs/drive-team-guide.md` | Xbox controller button maps for driver and operator |
| `docs/PYTHON_SETUP.md` | Python installation for Mac and Windows |
| `docs/roborio-deploy.md` | RoboRIO setup, deployment, and troubleshooting |
| `docs/debugging.md` | SSH access, remote logs, and common debugging scenarios |
| `docs/cli-and-tooling.md` | Team CLI (./cli/team.sh), menus, setup commands, how to extend |
| `docs/QUICK-REFERENCE.md` | Printable 1-page cheat sheet for the team (Python, git, deploy) |

## Quick Reference

```bash
# Run tests
python -m pytest tests/ -v

# Run simulation
python -m robotpy sim

# Deploy to robot
python -m robotpy deploy
```
