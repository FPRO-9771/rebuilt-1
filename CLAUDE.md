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

## Project Summary

RobotPy (Python) codebase for an FRC competition robot using the WPILib command-based framework with Phoenix 6 motor controllers. This is a starting-point codebase for the 2026 season built on lessons learned from 2025.

## Code Principles

1. **DRY (Don't Repeat Yourself)** - Configuration lives in `constants/`, not scattered through code
2. **Separation of Concerns** - Hardware abstraction in `hardware/`, subsystems own their mechanisms, commands handle actions
3. **Testable Modules** - All hardware access goes through abstractions that can be mocked for testing
4. **No Magic Numbers** - All values (CAN IDs, voltages, limits) defined in constants
5. **Command Ownership** - Subsystems expose commands; commands always call `addRequirements()`
6. **Small Files** - Keep every module short and focused (under ~100 lines). One interface, class, or concept per file. Split early — the team includes new Python learners who need to read files top-to-bottom

## Testing Rule: Never Hardcode Constants in Tests

Tests must stay green when the team tunes values in `constants/`. **Never use hardcoded numbers that depend on specific constant values.** Instead:

- **Derive expected values from the constants themselves.** For example, use `CON_TURRET["max_voltage"] * CON_TURRET["manual_speed_factor"]` — not `0.4`.
- **Compute safe positions from limits.** When a test needs the motor away from soft limits, calculate the midpoint: `(CON_TURRET["min_position"] + CON_TURRET["max_position"]) / 2` — not a hardcoded `-10`.
- **Check behavior, not specific numbers, where possible.** Prefer `assert voltage > 0` or `assert voltage != 0` over asserting an exact value, when the test is verifying direction or activity rather than a formula.

This matters because the team frequently adjusts voltages, positions, and speed factors during tuning. A constant change in `constants/` should never require editing test files.

## Logging: Use the Unified Logger

All logging goes through `utils.logger.get_logger()`. **Never use `print()` or raw `logging.getLogger()`.** The unified logger routes messages to both the console and the FRC Driver Station automatically.

**Setup pattern** — at the top of any file that needs logging:

```python
from utils.logger import get_logger

_log = get_logger("subsystem_name")   # e.g. "hood", "turret", "hardware"
```

**Log levels and where they go:**

| Level | Use for | Destination |
|-------|---------|-------------|
| `_log.debug(...)` | Internal state, parameter values, control flow | Console only |
| `_log.info(...)` | Initialization, configuration, state transitions | Console only |
| `_log.warning(...)` | Unusual conditions (unwired motors, limits) | Console + Driver Station |
| `_log.error(...)` | Failures that affect robot operation | Console + Driver Station |

**Rules:**
- Logger name should match the module/subsystem (e.g. `get_logger("hood")` in `subsystems/hood.py`)
- Use f-strings with relevant values: `_log.debug(f"_set_position: requested={position:.4f} clamped={clamped:.4f}")`
- Verbosity is controlled by `DEBUG["verbose"]` in `constants/debug.py` — don't add your own level toggling
- WARNING and ERROR appear on the Driver Station during matches, so keep those messages concise and actionable

## IMPORTANT: Read Docs First

**Before reading or modifying ANY code, read the relevant docs below.** The docs are the authoritative reference for how this codebase is structured, what patterns we use, and why. Jumping straight into code without reading the docs first will lead to mistakes — wrong patterns, duplicated work, or changes that break conventions. Always start here.

| Document | Description |
|----------|-------------|
| `docs/2026-robot-code-guide.md` | High-level overview, project structure, config management, quick reference tables, workflow, and lessons learned |
| `docs/architecture/hardware-and-subsystems.md` | Hardware abstraction layer and subsystem design patterns |
| `docs/architecture/commands-and-controls.md` | Command-based architecture and controller bindings |
| `docs/architecture/shooter-system.md` | Shooter subsystems, distance lookup table, and orchestrator |
| `docs/architecture/controls.md` | Binding extraction pattern, operator control map, manual overrides |
| `docs/architecture/autonomous.md` | Autonomous system: routines, constants, chooser setup |
| `docs/architecture/drivetrain.md` | Swerve drivetrain setup with Phoenix Tuner X |
| `docs/architecture/vision.md` | Vision system (Limelight), abstraction layer, and testing |
| `docs/architecture/testing-and-simulation.md` | Testing with mocks, physics simulation, and calibration |
| `docs/architecture/telemetry.md` | Telemetry dashboard module, published keys, and how to extend |
| `docs/dashboard-setup.md` | How to open Shuffleboard / Glass / Elastic and view live telemetry |
| `docs/drive-team-guide.md` | Xbox controller button maps for driver and operator |
| `docs/PYTHON_SETUP.md` | Python installation for Mac and Windows |
| `docs/roborio-deploy.md` | RoboRIO setup, deployment, and troubleshooting |

## Quick Reference

```bash
# Run tests
python -m pytest tests/ -v

# Run simulation
python -m robotpy sim

# Deploy to robot
python -m robotpy deploy
```
