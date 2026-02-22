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
| [Autonomous](architecture/autonomous.md) | Building/editing auto routines |
| [Drivetrain](architecture/drivetrain.md) | Drivetrain config/tuning |
| [Vision](architecture/vision.md) | Limelight for auto, teleop, or any use |
| [Testing & Simulation](architecture/testing-and-simulation.md) | Writing tests, running sim |

---

## 1. Project Structure

Create this directory structure at the start of the season:

```
robot-2026/
├── main.py                    # Entry point (tiny - just starts robot)
├── robot.py                   # Robot lifecycle (TimedRobot subclass)
├── robot_container.py         # Central hub - creates everything, wires it together
├── constants.py               # ALL configuration values
│
├── hardware/                  # NEW: Hardware abstraction layer
│   ├── __init__.py
│   ├── motor_controller.py    # Motor interface + implementations
│   ├── sensors.py             # Encoder, limit switch abstractions
│   └── mock_hardware.py       # Mock implementations for testing
│
├── generated/                 # Phoenix Tuner X output (don't edit by hand)
│   └── tuner_constants.py
│
├── subsystems/                # One file per mechanism
│   ├── __init__.py
│   ├── drivetrain.py
│   └── [mechanism].py         # arm.py, intake.py, etc.
│
├── autonomous/
│   ├── __init__.py
│   ├── auton_modes.py         # High-level auto routines
│   ├── auton_constants.py     # Auto-specific config (AprilTag IDs, paths)
│   └── auton_mode_selector.py # Dashboard chooser
│
├── handlers/                  # External system integrations
│   ├── __init__.py
│   ├── vision.py              # Vision abstraction (Limelight wrapper + mock)
│   └── limelight_handler.py   # Legacy direct Limelight access
│
├── testing/                   # Simulation and test utilities
│   ├── __init__.py
│   ├── physics_sim.py         # Physics models (drivetrain, mechanisms)
│   └── sim_runner.py          # Simulation test runner
│
├── tests/                     # Automated tests
│   ├── __init__.py
│   ├── conftest.py            # Pytest fixtures (mock setup)
│   ├── test_subsystems.py
│   ├── test_commands.py
│   ├── test_vision.py         # Vision alignment tests
│   ├── test_auto_physics.py   # Full auto tests with physics sim
│   └── test_autonomous.py
│
├── calibration/               # Scripts to run on real robot
│   └── measure_drivetrain.py  # Measure max speed, rotation rate
│
└── requirements.txt
```

**From phoenix-v1:** We had this structure but without `hardware/` layer and with minimal tests. Adding the hardware abstraction is the big improvement for 2026.

---

## 2. Configuration Management

**Rule: No magic numbers in code. Everything configurable goes in `constants.py`.**

### constants.py Structure

```python
# constants.py

# =============================================================================
# MOTOR CAN IDS - Single source of truth for all motor IDs
# =============================================================================
MOTOR_IDS = {
    # Drivetrain (configured via tuner_constants.py, listed here for reference)
    # "drive_fl": 11, "steer_fl": 10, etc.

    # Mechanisms
    "arm_main": 20,
    "arm_follower": 21,
    "intake": 22,
    "climber": 23,
}

# =============================================================================
# SENSOR CAN IDS
# =============================================================================
SENSOR_IDS = {
    "pigeon": 40,
    "canrange_front": 41,
    "canrange_rear": 42,
}

# =============================================================================
# MECHANISM CONFIGS - Limits, speeds, positions
# =============================================================================
CON_ARM = {
    "min_angle": 0,
    "max_angle": 180,
    "position_tolerance": 2,  # degrees

    # Named positions
    "stow": 10,
    "intake": 45,
    "score_low": 90,
    "score_high": 135,

    # Motion
    "max_voltage": 10,
    "hold_voltage": 1,
}

CON_INTAKE = {
    "intake_voltage": 8,
    "outtake_voltage": -6,
    "hold_voltage": 2,
}

# =============================================================================
# ROBOT-WIDE SETTINGS
# =============================================================================
CON_ROBOT = {
    "driver_controller_port": 0,
    "operator_controller_port": 1,

    "max_speed_mps": 5.0,           # meters per second
    "max_angular_rate": 3.14,       # radians per second

    "joystick_deadband": 0.1,
}
```

**From phoenix-v1:** We did this well. All motor IDs, limits, speeds, and positions were in `constants.py`. When we changed hardware, we only edited one file.

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

1. **Add config to `constants.py`:**
   ```python
   MOTOR_IDS["new_mechanism"] = 30
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

7. **Deploy:** `robotpy deploy --skip-tests`

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
