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

## Documentation Library

**Read these docs before diving into code.** They are kept up to date and are the authoritative reference.

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

## Quick Reference

```bash
# Run tests
python -m pytest tests/ -v

# Run simulation
python -m robotpy sim

# Deploy to robot
python -m robotpy deploy
```
