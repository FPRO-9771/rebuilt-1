# FRC Robot Code Architecture Guide

**Team 9771 FPRO - Lessons from 2025 (Reefscape) for 2026 (Rebuilt)**

This guide documents how to structure FRC robot code based on what worked (and what we should improve) from the phoenix-v1 codebase.

---

## Architecture Docs

Detailed guides live in `docs/architecture/`. Jump to the one you need:

| Document | When You'd Use It |
|----------|-------------------|
| [Hardware & Subsystems](architecture/hardware-and-subsystems.md) | Adding a new mechanism |
| [Commands & Controls](architecture/commands-and-controls.md) | Wiring buttons/joysticks to actions |
| [Shooter System](architecture/shooter-system.md) | Turret, launcher, hood, orchestrator, distance table |
| [Controls & Manual Overrides](architecture/controls.md) | Binding extraction pattern, operator control map, emergency overrides |
| [Autonomous](architecture/autonomous.md) | Building/editing auto routines |
| [Drivetrain](architecture/drivetrain.md) | Drivetrain config/tuning |
| [Vision](architecture/vision.md) | Limelight for auto, teleop, or any use |
| [Testing & Simulation](architecture/testing-and-simulation.md) | Writing tests, running sim |
| [Telemetry](architecture/telemetry.md) | Live dashboard data (motors, commands, vision) |

---

## 1. Project Layout

The codebase is organized by responsibility, not by file type:

- **`constants/`** — Single source of truth for every configurable value (CAN IDs, voltages, limits, positions). Split into topic files (`ids.py`, `shooter.py`, `conveyor.py`, `controls.py`, `simulation.py`) so you can find what you need fast. Import from the package (`from constants import CON_TURRET`) or from a specific file (`from constants.shooter import CON_TURRET`).
- **`robot_container.py`** — Central hub that creates all subsystems and wires them together. The only place that knows about everything.
- **`hardware/`** — Abstraction layer between subsystem code and real motors/sensors. Subsystems program against the `MotorController` ABC; the factory decides whether to return a real TalonFX or a mock. This is the big improvement over 2025.
- **`subsystems/`** — One file per mechanism. Each subsystem owns its hardware, exposes Commands, and enforces safety limits. Also contains pure-logic helpers like `shooter_lookup.py`.
- **`commands/`** — Multi-subsystem commands that don't belong inside a single subsystem file (e.g., `ShooterOrchestrator` coordinates turret + launcher + hood).
- **`autonomous/`** — Auto routine composition, field-position constants, and dashboard chooser. See [Autonomous](architecture/autonomous.md).
- **`handlers/`** — External system integrations (vision/Limelight). Same abstraction pattern as hardware.
- **`controls/`** — Controller bindings (driver and operator). Keeps button-wiring logic out of `robot_container.py`.
- **`telemetry/`** — Dashboard publishers for motors, commands, and vision. Pushes data to SmartDashboard every cycle.
- **`testing/`** — Physics simulation models and sim runner. Calibrated from real robot measurements.
- **`tests/`** — Automated pytest tests. Convention: one `test_<topic>.py` per subsystem or concern.
- **`generated/`** — Phoenix Tuner X output. Don't edit by hand.

---

## 2. Configuration Management

**Rule: No magic numbers in code. Everything configurable goes in `constants/`.**

### constants/ Package Structure

The `constants/` package is split into topic files so you can find what you need fast:

```
constants/
├── __init__.py        # Re-exports everything (no special imports needed)
├── ids.py             # MOTOR_IDS, SENSOR_IDS
├── shooter.py         # CON_TURRET, CON_LAUNCHER, CON_HOOD, CON_SHOOTER
├── conveyor.py        # CON_CONVEYOR
├── controls.py        # CON_MANUAL, CON_ROBOT
├── simulation.py      # SIM_CALIBRATION, SIM_DT
└── telemetry.py       # CON_TELEMETRY
```

Import from the package — works the same as the old single file:
```python
from constants import MOTOR_IDS, CON_TURRET
```

Or import from a specific file when you want to be explicit:
```python
from constants.shooter import CON_LAUNCHER
```

**From phoenix-v1:** We did this well. All motor IDs, limits, speeds, and positions were centralized. When we changed hardware, we only edited one place.

---

## Quick Reference

### Command Types

| Type | Finishes When | Use For |
|------|---------------|---------|
| `SequentialCommandGroup` | All commands complete in order | Multi-step sequences |
| `ParallelCommandGroup` | ALL commands complete | Independent parallel actions |
| `ParallelRaceGroup` | ANY command completes | Timeouts, "until" conditions |
| `ParallelDeadlineGroup` | First command completes | Do X while Y happens |
| `WaitCommand(seconds)` | Duration passes | Delays |
| `InstantCommand(lambda)` | Immediately | One-shot actions |

### Button Bindings

| Method | Triggers |
|--------|----------|
| `.onTrue(cmd)` | When pressed |
| `.onFalse(cmd)` | When released |
| `.whileTrue(cmd)` | Runs while held, cancels on release |
| `.whileFalse(cmd)` | Runs while NOT pressed |
| `.toggleOnTrue(cmd)` | Toggle on/off with each press |

### Motor Control Patterns

```python
# Voltage (open loop)
motor.set_voltage(6.0)

# Position (closed loop, needs PID tuning)
motor.set_position(target_rotations)

# Velocity (closed loop)
motor.set_velocity(target_rps)
```

---

## Development Workflow

### Starting a New Mechanism

1. **Add config to `constants/`** (pick the right file, or create a new one and add it to `__init__.py`):
   ```python
   # constants/ids.py
   MOTOR_IDS["new_mechanism"] = 30

   # constants/new_mechanism.py (new file)
   CON_NEW_MECHANISM = {"max_voltage": 8, "tolerance": 2, ...}
   ```

2. **Create subsystem file:** Copy template from [Hardware & Subsystems](architecture/hardware-and-subsystems.md)

3. **Add to `robot_container.py`:**
   ```python
   self.new_mechanism = NewMechanism()
   ```

4. **Write tests first** (or at least alongside)

5. **Add control bindings**

6. **Test in simulation:** `robotpy sim`

7. **Deploy:** `python -m robotpy deploy --skip-tests`

### Git Workflow

- `main` - Stable, competition-ready code
- `develop` - Integration branch
- `feature/[name]` - New features
- `fix/[name]` - Bug fixes

Always branch from `main` for new work. PR to `develop` first, then to `main` before competition.

---

## Lessons Learned from 2025

1. **Configuration centralization works** - Do it from day one
2. **Command composition is powerful** - Draw diagrams before coding complex sequences
3. **Factory pattern for autos** - Always use lambdas in the chooser
4. **Hardware abstraction enables testing** - New for 2026, should have done it earlier
5. **Vision abstraction enables testing** - Mock Limelight data to test alignment logic
6. **Physics simulation catches real bugs** - Test that autos reach expected positions, not just motor signals
7. **Calibrate early, calibrate often** - Robot physics change (battery, wear, carpet); re-calibrate at events
8. **Simulation is valuable** - Use `robotpy sim` early and often
9. **Keep autonomous simple** - Complex autos are hard to debug at competition
10. **Manual overrides matter** - Always have a way to manually control mechanisms
11. **Calibrate vision multipliers early** - The LL_DATA_SETTINGS multipliers need tuning per camera mount
12. **Test direction logic** - Easy to get signs wrong (left vs right, forward vs back)

---

## 2026 Ideas to Explore

A running list of things we want to investigate this season.

### Physical-Input Autonomous Commands

**Goal:** Write autonomous routines using physical measurements instead of voltage/time.

Instead of:
```python
# Voltage-based (what we did in 2025)
self.drivetrain.run_at_voltage(-6.0, duration=1.5)  # Hope this moves ~2 meters
```

We want:
```python
# Physical-input based (goal for 2026)
self.drivetrain.move_distance(-2.0)  # Move back 2 meters
self.drivetrain.rotate_to_heading(90)  # Turn to face 90 degrees
self.arm.move_to_angle(45)  # Move arm to 45 degrees
```

**Why this is better:**
- More intuitive to write and read
- Repeatable regardless of battery voltage
- Easier to tune and debug
- Works with odometry/encoders for accuracy

**Things to figure out:**
- [ ] How to use encoder feedback for distance tracking
- [ ] PID tuning for position-based movement
- [ ] Integration with Phoenix 6 motion magic / position control
- [ ] How to handle "I didn't reach the target" failures

---

*Add more ideas below as we think of them!*
