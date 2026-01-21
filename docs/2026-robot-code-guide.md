# FRC Robot Code Architecture Guide

**Team 9771 FPRO - Lessons from 2025 (Reefscape) for 2026 (Rebuilt)**

This guide documents how to structure FRC robot code based on what worked (and what we should improve) from the phoenix-v1 codebase.

---

## Table of Contents

1. [Project Structure](#1-project-structure)
2. [Configuration Management](#2-configuration-management)
3. [Hardware Abstraction Layer (NEW)](#3-hardware-abstraction-layer-new)
4. [Subsystem Design](#4-subsystem-design)
5. [Command-Based Architecture](#5-command-based-architecture)
6. [Control Bindings](#6-control-bindings)
7. [Autonomous System](#7-autonomous-system)
8. [Swerve Drivetrain Setup](#8-swerve-drivetrain-setup)
9. [Vision System (Limelight)](#9-vision-system-limelight)
10. [Testing](#10-testing)
11. [Physics Simulation for Testing (NEW)](#11-physics-simulation-for-testing-new)
12. [Development Workflow](#12-development-workflow)

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

## 3. Hardware Abstraction Layer (NEW)

**This is new for 2026.** In phoenix-v1, subsystems directly created and controlled TalonFX motors. This made testing hard because you can't run TalonFX code without hardware.

### The Problem (phoenix-v1 approach)

```python
# subsystems/arm.py (OLD WAY - hard to test)
from phoenix6.hardware import TalonFX
from phoenix6.controls import VoltageOut

class Arm(SubsystemBase):
    def __init__(self):
        self.motor = TalonFX(MOTOR_IDS["arm"])  # Direct hardware dependency

    def set_voltage(self, volts):
        self.motor.set_control(VoltageOut(volts))  # Can't test without hardware
```

### The Solution: Hardware Abstraction

```python
# hardware/motor_controller.py

from abc import ABC, abstractmethod
from typing import Optional
from phoenix6.hardware import TalonFX
from phoenix6.controls import VoltageOut, PositionVoltage

class MotorController(ABC):
    """Abstract interface for motor controllers."""

    @abstractmethod
    def set_voltage(self, volts: float) -> None:
        pass

    @abstractmethod
    def set_position(self, position: float, feedforward: float = 0) -> None:
        pass

    @abstractmethod
    def get_position(self) -> float:
        pass

    @abstractmethod
    def get_velocity(self) -> float:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass


class TalonFXController(MotorController):
    """Real TalonFX implementation."""

    def __init__(self, can_id: int, inverted: bool = False):
        self.motor = TalonFX(can_id)
        if inverted:
            # Configure inversion
            pass
        self._last_voltage = 0.0

    def set_voltage(self, volts: float) -> None:
        self._last_voltage = volts
        self.motor.set_control(VoltageOut(volts))

    def set_position(self, position: float, feedforward: float = 0) -> None:
        self.motor.set_control(PositionVoltage(position).with_feed_forward(feedforward))

    def get_position(self) -> float:
        return self.motor.get_position().value

    def get_velocity(self) -> float:
        return self.motor.get_velocity().value

    def stop(self) -> None:
        self.set_voltage(0)


class MockMotorController(MotorController):
    """Mock implementation for testing."""

    def __init__(self, can_id: int, inverted: bool = False):
        self.can_id = can_id
        self.inverted = inverted
        self._position = 0.0
        self._velocity = 0.0
        self._voltage = 0.0
        self.command_history: list[dict] = []  # Track all commands for verification

    def set_voltage(self, volts: float) -> None:
        self._voltage = volts
        self.command_history.append({"type": "voltage", "value": volts})

    def set_position(self, position: float, feedforward: float = 0) -> None:
        self._position = position  # Instant for testing
        self.command_history.append({"type": "position", "value": position, "ff": feedforward})

    def get_position(self) -> float:
        return self._position

    def get_velocity(self) -> float:
        return self._velocity

    def stop(self) -> None:
        self.set_voltage(0)

    # Test helpers
    def simulate_position(self, position: float) -> None:
        """Set position for testing sensor reads."""
        self._position = position

    def get_last_voltage(self) -> float:
        """Get last commanded voltage for test assertions."""
        return self._voltage

    def clear_history(self) -> None:
        self.command_history.clear()
```

### Factory for Creating Motors

```python
# hardware/__init__.py

from .motor_controller import MotorController, TalonFXController, MockMotorController

_use_mock_hardware = False

def set_mock_mode(enabled: bool) -> None:
    """Enable mock hardware for testing."""
    global _use_mock_hardware
    _use_mock_hardware = enabled

def create_motor(can_id: int, inverted: bool = False) -> MotorController:
    """Factory function - returns real or mock motor based on mode."""
    if _use_mock_hardware:
        return MockMotorController(can_id, inverted)
    return TalonFXController(can_id, inverted)
```

### Updated Subsystem (uses abstraction)

```python
# subsystems/arm.py (NEW WAY - testable)
from commands2 import SubsystemBase, Command
from hardware import create_motor
from constants import MOTOR_IDS, CON_ARM

class Arm(SubsystemBase):
    def __init__(self):
        super().__init__()
        self.motor = create_motor(MOTOR_IDS["arm_main"])
        self.target_position = 0.0

    def set_voltage(self, volts: float) -> None:
        # Apply limits
        clamped = max(-CON_ARM["max_voltage"], min(volts, CON_ARM["max_voltage"]))
        self.motor.set_voltage(clamped)

    def get_position(self) -> float:
        return self.motor.get_position()

    def at_position(self, target: float) -> bool:
        return abs(self.get_position() - target) < CON_ARM["position_tolerance"]
```

### Test Example

```python
# tests/test_arm.py
import pytest
from hardware import set_mock_mode, create_motor
from subsystems.arm import Arm
from constants import CON_ARM

@pytest.fixture
def arm():
    set_mock_mode(True)  # Use mocks
    return Arm()

def test_voltage_clamping(arm):
    """Verify voltage is clamped to max."""
    arm.set_voltage(100)  # Way over max
    assert arm.motor.get_last_voltage() == CON_ARM["max_voltage"]

def test_at_position(arm):
    """Verify position checking works."""
    arm.motor.simulate_position(45.0)
    assert arm.at_position(45.0)
    assert arm.at_position(46.0)  # Within tolerance
    assert not arm.at_position(90.0)  # Outside tolerance

def test_command_sends_correct_voltage(arm):
    """Verify go_to_position command outputs expected voltage."""
    arm.motor.simulate_position(0)
    cmd = arm.go_to_position(90)
    cmd.initialize()
    cmd.execute()

    # Check that voltage was sent in correct direction
    assert arm.motor.get_last_voltage() > 0
```

---

## 4. Subsystem Design

Each mechanism gets its own file in `subsystems/`. A subsystem:
- Owns its hardware (via the abstraction layer)
- Exposes methods that return Commands
- Handles its own safety limits
- Never directly executes actions (commands do that)

### Subsystem Template

```python
# subsystems/[mechanism].py

from commands2 import SubsystemBase, Command
from hardware import create_motor
from constants import MOTOR_IDS, CON_[MECHANISM]

class [Mechanism](SubsystemBase):
    def __init__(self):
        super().__init__()
        self.motor = create_motor(MOTOR_IDS["mechanism_name"])
        self._target = 0.0

    # --- Sensor reads (public) ---

    def get_position(self) -> float:
        return self.motor.get_position()

    def at_target(self) -> bool:
        return abs(self.get_position() - self._target) < CON_[MECHANISM]["tolerance"]

    # --- Motor control (internal) ---

    def _set_voltage(self, volts: float) -> None:
        clamped = max(-CON_[MECHANISM]["max_voltage"],
                      min(volts, CON_[MECHANISM]["max_voltage"]))
        self.motor.set_voltage(clamped)

    def _stop(self) -> None:
        self.motor.stop()

    # --- Commands (public) ---

    def go_to_position(self, position: float) -> Command:
        """Returns command to move to position."""
        return self._GoToPositionCommand(self, position)

    def manual(self, speed_supplier) -> Command:
        """Returns command for joystick control."""
        return self._ManualCommand(self, speed_supplier)

    # --- Inner command classes ---

    class _GoToPositionCommand(Command):
        def __init__(self, mechanism, target):
            super().__init__()
            self.mechanism = mechanism
            self.target = target
            self.addRequirements(mechanism)

        def initialize(self):
            self.mechanism._target = self.target

        def execute(self):
            error = self.target - self.mechanism.get_position()
            voltage = error * 0.1  # Simple P control
            self.mechanism._set_voltage(voltage)

        def isFinished(self):
            return self.mechanism.at_target()

        def end(self, interrupted):
            self.mechanism._stop()

    class _ManualCommand(Command):
        def __init__(self, mechanism, speed_supplier):
            super().__init__()
            self.mechanism = mechanism
            self.speed_supplier = speed_supplier
            self.addRequirements(mechanism)

        def execute(self):
            speed = self.speed_supplier()
            voltage = speed * CON_[MECHANISM]["max_voltage"]
            self.mechanism._set_voltage(voltage)

        def end(self, interrupted):
            self.mechanism._stop()
```

**From phoenix-v1:** Our subsystems followed this pattern. Key things we did right:
- Commands are inner classes that reference parent subsystem
- Always call `addRequirements()`
- `end()` always stops the motor
- Manual control uses a supplier (lambda) for live joystick values

---

## 5. Command-Based Architecture

This is the WPILib pattern for robot control. Understanding it is essential.

### Core Concepts

1. **CommandScheduler** - Runs every 20ms, executes all scheduled commands
2. **Command** - A unit of work with `initialize()`, `execute()`, `isFinished()`, `end()`
3. **Subsystem** - Hardware abstraction that commands "require"
4. **Requirements** - A command declares which subsystems it uses; scheduler prevents conflicts

### Command Lifecycle

```
schedule() → initialize() → execute() [loop] → end() when isFinished() == True
                               ↑______|
```

### Command Composition

This is the powerful (and tricky) part:

```python
from commands2 import (
    SequentialCommandGroup,    # One after another
    ParallelCommandGroup,      # All at once, done when ALL finish
    ParallelRaceGroup,         # All at once, done when ANY finishes
    ParallelDeadlineGroup,     # All at once, done when FIRST (deadline) finishes
    WaitCommand,               # Wait for duration
    InstantCommand,            # Run once immediately
)

# Sequential: A then B then C
sequence = SequentialCommandGroup(
    arm.go_to_position(90),
    intake.run_intake(),
    arm.go_to_position(0),
)

# Parallel: A and B, wait for both
parallel = ParallelCommandGroup(
    arm.go_to_position(90),
    drivetrain.drive_forward(1.0),
)

# Race: A and B, stop when first finishes
race = ParallelRaceGroup(
    intake.run_until_has_piece(),
    WaitCommand(3.0),  # Timeout
)

# Deadline: Run B while A is running, stop B when A finishes
deadline = ParallelDeadlineGroup(
    drivetrain.drive_distance(2.0),  # Deadline (first arg)
    intake.run_intake(),             # Runs until deadline finishes
)
```

**From phoenix-v1:** We used all of these. The key insight: think of autonomous as composing these building blocks. Draw it out on paper first.

---

## 6. Control Bindings

Wire controllers to commands in `robot_container.py`.

### Pattern

```python
# robot_container.py

from commands2.button import CommandXboxController, Trigger

class RobotContainer:
    def __init__(self):
        # Create subsystems
        self.arm = Arm()
        self.intake = Intake()

        # Create controllers
        self.driver = CommandXboxController(CON_ROBOT["driver_controller_port"])
        self.operator = CommandXboxController(CON_ROBOT["operator_controller_port"])

    def configure_bindings(self):
        # --- Driver controls ---
        # Drivetrain default command (always running)
        self.drivetrain.setDefaultCommand(
            self.drivetrain.drive_with_joystick(
                lambda: -self.driver.getLeftY(),
                lambda: -self.driver.getLeftX(),
                lambda: -self.driver.getRightX(),
            )
        )

        # --- Operator controls ---
        # Button press triggers command
        self.operator.a().onTrue(self.arm.go_to_position(CON_ARM["score_low"]))
        self.operator.b().onTrue(self.arm.go_to_position(CON_ARM["score_high"]))

        # While held
        self.operator.rightTrigger(0.1).whileTrue(
            self.intake.run_intake()
        )

        # Manual control with deadband
        deadband = CON_ROBOT["joystick_deadband"]
        Trigger(lambda: abs(self.operator.getLeftY()) > deadband).whileTrue(
            self.arm.manual(lambda: self.operator.getLeftY())
        )
```

### Key Rules

1. **Use lambdas for live values**: `lambda: controller.getLeftY()` - called each cycle
2. **Don't use direct values**: `controller.getLeftY()` without lambda captures value ONCE
3. **Triggers for analog inputs**: Use `Trigger(lambda: ...)` for joysticks with deadband
4. **Button methods**: `.onTrue()`, `.onFalse()`, `.whileTrue()`, `.whileFalse()`, `.toggleOnTrue()`

---

## 7. Autonomous System

### Structure

```
auton_modes.py         - Composes full auto routines
auton_constants.py     - Data: AprilTag IDs, drive paths, timings
auton_mode_selector.py - Creates SmartDashboard chooser
```

### Autonomous Constants

```python
# autonomous/auton_constants.py

# AprilTag IDs for each starting position
APRILTAG_IDS = {
    "blue_left": {"score": 20, "intake": 13},
    "blue_center": {"score": 21, "intake": 14},
    "red_right": {"score": 10, "intake": 3},
    # etc.
}

# Drive paths: list of (vx, vy, omega, duration) tuples
DRIVE_PATHS = {
    "exit_zone": [
        (2.0, 0, 0, 1.0),   # Forward 2 m/s for 1 second
    ],
    "to_intake": [
        (1.5, 0.5, 0, 1.5),  # Forward-left
        (0, 0, 1.5, 0.5),    # Rotate
    ],
}
```

### Autonomous Mode Factory

```python
# autonomous/auton_modes.py

from commands2 import SequentialCommandGroup, ParallelCommandGroup

class AutonModes:
    def __init__(self, drivetrain, arm, intake, limelight):
        self.drivetrain = drivetrain
        self.arm = arm
        self.intake = intake
        self.limelight = limelight

    def simple_score(self, position: str):
        """Score preloaded piece and exit."""
        return SequentialCommandGroup(
            self.arm.go_to_position(CON_ARM["score_high"]),
            self.intake.outtake(),
            self.arm.go_to_position(CON_ARM["stow"]),
            self.drivetrain.follow_path(DRIVE_PATHS["exit_zone"]),
        )

    def two_piece(self, position: str):
        """Score preload, get second piece, score again."""
        tags = APRILTAG_IDS[position]

        return SequentialCommandGroup(
            # Score preload
            self.arm.go_to_position(CON_ARM["score_high"]),
            self.intake.outtake(),

            # Get second piece
            ParallelCommandGroup(
                self.drivetrain.follow_path(DRIVE_PATHS["to_intake"]),
                self.arm.go_to_position(CON_ARM["intake"]),
            ),
            self.intake.run_until_has_piece(),

            # Return and score
            self.drivetrain.align_to_apriltag(tags["score"]),
            self.arm.go_to_position(CON_ARM["score_high"]),
            self.intake.outtake(),
        )
```

### Chooser Setup

```python
# autonomous/auton_mode_selector.py

from wpilib import SmartDashboard, SendableChooser

def create_auton_chooser(auton_modes):
    chooser = SendableChooser()

    # IMPORTANT: Store factories (lambdas), not command instances
    # Commands should be created fresh each auto period
    chooser.setDefaultOption("Simple Score Blue",
                             lambda: auton_modes.simple_score("blue_center"))
    chooser.addOption("Two Piece Blue Left",
                      lambda: auton_modes.two_piece("blue_left"))
    chooser.addOption("Two Piece Red Right",
                      lambda: auton_modes.two_piece("red_right"))

    SmartDashboard.putData("Auto Mode", chooser)
    return chooser
```

### Using in Robot.py

```python
# robot.py

def autonomousInit(self):
    # Get the factory function from chooser
    auto_factory = self.container.auto_chooser.getSelected()

    # Create fresh command instance
    self.auto_command = auto_factory()

    # Schedule it
    self.auto_command.schedule()

def autonomousExit(self):
    if self.auto_command:
        self.auto_command.cancel()
```

**From phoenix-v1:** We learned the hard way to use factories (lambdas) in the chooser. If you store command instances, they carry state between runs and break.

---

## 8. Swerve Drivetrain Setup

### Phoenix Tuner X Workflow

1. **Configure each module in Phoenix Tuner X:**
   - Set CAN IDs for drive motor, steer motor, CANcoder
   - Calibrate CANcoder offset (wheels straight forward)

2. **Use Swerve Generator:**
   - Enter physical dimensions
   - Enter gear ratios
   - Export to `generated/tuner_constants.py`

3. **Don't edit the generated file by hand.** If you need to change something, re-run the generator.

### Drivetrain Wrapper

```python
# subsystems/drivetrain.py

from generated.tuner_constants import TunerConstants
from phoenix6 import swerve
from phoenix6.swerve.requests import FieldCentric, RobotCentric, SwerveDriveBrake

class Drivetrain(TunerConstants.create_drivetrain().__class__):
    """Wrapper around generated swerve drivetrain."""

    def __init__(self):
        super().__init__()
        self.field_centric = FieldCentric()
        self.robot_centric = RobotCentric()
        self.brake = SwerveDriveBrake()

    def drive_with_joystick(self, x_supplier, y_supplier, rot_supplier):
        """Default command for teleop driving."""
        return self.apply_request(lambda: (
            self.field_centric
                .with_velocity_x(x_supplier() * CON_ROBOT["max_speed_mps"])
                .with_velocity_y(y_supplier() * CON_ROBOT["max_speed_mps"])
                .with_rotational_rate(rot_supplier() * CON_ROBOT["max_angular_rate"])
        ))

    def stop(self):
        return self.apply_request(lambda: self.brake)
```

**From phoenix-v1:** The Phoenix 6 swerve implementation worked well. The key is trusting the generated config and not fighting it.

---

## 9. Vision System (Limelight)

We used Limelight cameras extensively in 2025 for AprilTag detection and alignment. This section documents how it worked and how to make it testable.

### What Limelight Provides

The Limelight camera detects AprilTags and provides:

| Field | Description |
|-------|-------------|
| `tag_id` | Which AprilTag was detected (e.g., 20 = blue reef left) |
| `tx` | Horizontal offset in degrees (negative = target left of center) |
| `ty` | Vertical offset in degrees |
| `distance` | 3D distance to target in meters |
| `yaw` | Target's rotation relative to camera |
| `pitch`, `roll` | Target's orientation |
| `x_pos`, `y_pos`, `z_pos` | Target position in camera space |

### How We Used It in 2025 (phoenix-v1)

**LimelightHandler** (`handlers/limelight_handler.py`) wrapped the limelight library:

```python
# handlers/limelight_handler.py (simplified from phoenix-v1)

import math
import limelight
import limelightresults

class LimelightHandler:
    def __init__(self, debug=True):
        # Auto-discover Limelight on network
        discovered = limelight.discover_limelights(debug=debug)
        if discovered:
            self.limelight = limelight.Limelight(discovered[0])
            self.limelight.pipeline_switch(0)  # AprilTag pipeline
            self.limelight.enable_websocket()
        else:
            self.limelight = None
            print("WARNING: No Limelight found!")

    def get_target_data(self, target_tag_id=None):
        """Get processed data for a specific AprilTag or closest one."""
        if not self.limelight:
            return None

        result = self.limelight.get_latest_results()
        parsed = limelightresults.parse_results(result)

        if not parsed or not parsed.fiducialResults:
            return None

        # Find the requested tag, or closest if not specified
        selected = None
        if target_tag_id:
            for tag in parsed.fiducialResults:
                if tag.fiducial_id == target_tag_id:
                    selected = tag
                    break

        if not selected:
            # Find closest tag
            closest_dist = float('inf')
            for tag in parsed.fiducialResults:
                pos = tag.target_pose_camera_space
                dist = math.sqrt(pos[0]**2 + pos[1]**2 + pos[2]**2)
                if dist < closest_dist:
                    closest_dist = dist
                    selected = tag

        if not selected:
            return None

        # Build clean data dict
        pos = selected.target_pose_camera_space
        return {
            'tag_id': selected.fiducial_id,
            'tx': selected.target_x_degrees,      # Horizontal offset
            'ty': selected.target_y_degrees,      # Vertical offset
            'distance': math.sqrt(pos[0]**2 + pos[1]**2 + pos[2]**2),
            'yaw': pos[4],
            'pitch': pos[3],
            'roll': pos[5],
            'x_pos': pos[0],
            'y_pos': pos[1],
            'z_pos': pos[2],
        }
```

**AutonDrive** used the handler to align to AprilTags:

```python
# autonomous/auton_drive.py (simplified from phoenix-v1)

class AutonDrive(SubsystemBase):
    def __init__(self, drivetrain, limelight_handler):
        self.drivetrain = drivetrain
        self.limelight = limelight_handler

    def align_to_tag(self, target_tag_id) -> Command:
        """Align robot to face an AprilTag."""

        class AlignCommand(Command):
            def __init__(self, outer, tag_id):
                super().__init__()
                self.outer = outer
                self.tag_id = tag_id
                self.on_target = False

            def execute(self):
                data = self.outer.limelight.get_target_data(self.tag_id)
                if not data:
                    return  # Lost target

                # Calculate drive corrections from vision data
                # tx > 0 means target is to the right, so rotate right (negative)
                rotation = -data['tx'] * 0.1  # P gain for rotation

                # distance > target means move forward
                speed_x = (data['distance'] - 1.0) * 0.5  # P gain, target 1m

                # Strafe based on tx to center horizontally
                speed_y = -data['tx'] * 0.05

                self.outer.drive_robot(rotation, speed_x, speed_y)

                # Check if on target
                self.on_target = (
                    abs(data['tx']) < 2.0 and      # Within 2 degrees
                    abs(data['distance'] - 1.0) < 0.1  # Within 10cm of target
                )

            def isFinished(self):
                return self.on_target

            def end(self, interrupted):
                self.outer.drive_robot(0, 0, 0)

        return AlignCommand(self, target_tag_id)
```

### Configuration for Vision

```python
# autonomous/auton_constants.py

# AprilTag IDs by field position (2025 Reefscape)
APRILTAG_IDS = {
    "blue_left": {"score": 20, "intake": 13, "score2": 19},
    "blue_center": {"score": 21},
    "blue_right": {"score": 22, "intake": 12, "score2": 17},
    "red_left": {"score": 11, "intake": 1, "score2": 6},
    "red_center": {"score": 10},
    "red_right": {"score": 9, "intake": 2, "score2": 8},
}

# Multipliers to calibrate vision data to real-world
# (these may need tuning per-camera mount)
LL_DATA_SETTINGS = {
    "yaw": {"multiplier": 0.115},
    "tx": {"multiplier": 0.222},
    "distance": {},  # No adjustment needed
}

# Driving behavior based on vision
DRIVING = {
    "speed_x": {
        "max": 3.0,
        "multiplier": 0.5,
        "target_tolerance": 0.3,  # meters
    },
    "speed_y": {
        "max": 1.5,
        "multiplier": 0.4,
        "target_tolerance": 0.5,  # degrees tx
    },
    "rotation": {
        "max": 0.8,
        "multiplier": 0.2,
        "target_tolerance": 0.08,  # degrees yaw
    },
}
```

### Making Vision Testable (NEW for 2026)

The problem: We couldn't test vision-based commands without a real Limelight and AprilTags.

**Solution: Vision Abstraction Layer**

```python
# handlers/vision.py

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class VisionTarget:
    """Standardized vision target data."""
    tag_id: int
    tx: float           # Horizontal offset (degrees, negative = left)
    ty: float           # Vertical offset (degrees)
    distance: float     # Distance to target (meters)
    yaw: float          # Target rotation
    is_valid: bool = True


class VisionProvider(ABC):
    """Abstract interface for vision systems."""

    @abstractmethod
    def get_target(self, tag_id: Optional[int] = None) -> Optional[VisionTarget]:
        """Get vision data for a specific tag or closest tag."""
        pass

    @abstractmethod
    def has_target(self, tag_id: Optional[int] = None) -> bool:
        """Check if a target is visible."""
        pass


class LimelightVisionProvider(VisionProvider):
    """Real Limelight implementation."""

    def __init__(self):
        import limelight
        import limelightresults
        self._ll = limelight
        self._llr = limelightresults

        discovered = limelight.discover_limelights()
        if discovered:
            self._camera = limelight.Limelight(discovered[0])
            self._camera.pipeline_switch(0)
            self._camera.enable_websocket()
        else:
            self._camera = None

    def get_target(self, tag_id: Optional[int] = None) -> Optional[VisionTarget]:
        if not self._camera:
            return None

        result = self._camera.get_latest_results()
        parsed = self._llr.parse_results(result)

        if not parsed or not parsed.fiducialResults:
            return None

        # Find requested tag or closest
        import math
        selected = None
        closest_dist = float('inf')

        for tag in parsed.fiducialResults:
            if tag_id and tag.fiducial_id == tag_id:
                selected = tag
                break
            pos = tag.target_pose_camera_space
            dist = math.sqrt(pos[0]**2 + pos[1]**2 + pos[2]**2)
            if dist < closest_dist:
                closest_dist = dist
                selected = tag

        if not selected:
            return None

        pos = selected.target_pose_camera_space
        return VisionTarget(
            tag_id=selected.fiducial_id,
            tx=selected.target_x_degrees,
            ty=selected.target_y_degrees,
            distance=math.sqrt(pos[0]**2 + pos[1]**2 + pos[2]**2),
            yaw=pos[4],
        )

    def has_target(self, tag_id: Optional[int] = None) -> bool:
        return self.get_target(tag_id) is not None


class MockVisionProvider(VisionProvider):
    """Mock implementation for testing."""

    def __init__(self):
        self._targets: Dict[int, VisionTarget] = {}
        self._default_target: Optional[VisionTarget] = None
        self._query_history: list[Optional[int]] = []

    def get_target(self, tag_id: Optional[int] = None) -> Optional[VisionTarget]:
        self._query_history.append(tag_id)

        if tag_id and tag_id in self._targets:
            return self._targets[tag_id]
        return self._default_target

    def has_target(self, tag_id: Optional[int] = None) -> bool:
        return self.get_target(tag_id) is not None

    # --- Test helpers ---

    def set_target(self, target: VisionTarget) -> None:
        """Set a specific target to be returned."""
        self._targets[target.tag_id] = target
        if self._default_target is None:
            self._default_target = target

    def set_default_target(self, target: Optional[VisionTarget]) -> None:
        """Set the default target (returned when no tag_id specified)."""
        self._default_target = target

    def simulate_target_left(self, tag_id: int, offset_degrees: float = 10, distance: float = 2.0) -> None:
        """Simulate a target to the left of center."""
        self.set_target(VisionTarget(
            tag_id=tag_id,
            tx=-abs(offset_degrees),  # Negative = left
            ty=0,
            distance=distance,
            yaw=0,
        ))

    def simulate_target_right(self, tag_id: int, offset_degrees: float = 10, distance: float = 2.0) -> None:
        """Simulate a target to the right of center."""
        self.set_target(VisionTarget(
            tag_id=tag_id,
            tx=abs(offset_degrees),  # Positive = right
            ty=0,
            distance=distance,
            yaw=0,
        ))

    def simulate_target_centered(self, tag_id: int, distance: float = 1.0) -> None:
        """Simulate a perfectly centered target."""
        self.set_target(VisionTarget(
            tag_id=tag_id,
            tx=0,
            ty=0,
            distance=distance,
            yaw=0,
        ))

    def simulate_no_target(self) -> None:
        """Simulate no visible targets."""
        self._targets.clear()
        self._default_target = None

    def clear_history(self) -> None:
        self._query_history.clear()
```

### Factory for Vision Provider

```python
# handlers/__init__.py

from .vision import VisionProvider, LimelightVisionProvider, MockVisionProvider

_use_mock_vision = False
_mock_provider: Optional[MockVisionProvider] = None

def set_mock_vision_mode(enabled: bool) -> None:
    global _use_mock_vision, _mock_provider
    _use_mock_vision = enabled
    if enabled:
        _mock_provider = MockVisionProvider()

def get_vision_provider() -> VisionProvider:
    if _use_mock_vision:
        return _mock_provider
    return LimelightVisionProvider()

def get_mock_vision() -> MockVisionProvider:
    """Get the mock provider for test setup. Only call after set_mock_vision_mode(True)."""
    if not _mock_provider:
        raise RuntimeError("Mock vision not enabled. Call set_mock_vision_mode(True) first.")
    return _mock_provider
```

### Updated AutonDrive (uses abstraction)

```python
# autonomous/auton_drive.py (updated for testability)

from handlers import get_vision_provider

class AutonDrive(SubsystemBase):
    def __init__(self, drivetrain, vision_provider=None):
        self.drivetrain = drivetrain
        self.vision = vision_provider or get_vision_provider()

    def align_to_tag(self, target_tag_id: int) -> Command:
        class AlignCommand(Command):
            def __init__(self, outer, tag_id):
                super().__init__()
                self.outer = outer
                self.tag_id = tag_id

            def execute(self):
                target = self.outer.vision.get_target(self.tag_id)
                if not target:
                    return

                # tx positive = target right, so rotate right (negative rate)
                rotation = -target.tx * 0.1
                speed_x = (target.distance - 1.0) * 0.5
                speed_y = -target.tx * 0.05

                self.outer.drive_robot(rotation, speed_x, speed_y)

            def isFinished(self):
                target = self.outer.vision.get_target(self.tag_id)
                if not target:
                    return True  # Lost target
                return abs(target.tx) < 2.0 and abs(target.distance - 1.0) < 0.1

            def end(self, interrupted):
                self.outer.drive_robot(0, 0, 0)

        return AlignCommand(self, target_tag_id)
```

### Testing Vision-Based Commands

Now the powerful part - testing alignment without hardware:

```python
# tests/test_vision_alignment.py

import pytest
from handlers import set_mock_vision_mode, get_mock_vision
from handlers.vision import VisionTarget
from hardware import set_mock_mode
from autonomous.auton_drive import AutonDrive

@pytest.fixture
def setup_mocks():
    """Enable all mocks for testing."""
    set_mock_mode(True)
    set_mock_vision_mode(True)
    yield
    set_mock_mode(False)
    set_mock_vision_mode(False)

@pytest.fixture
def auton_drive(setup_mocks):
    """Create AutonDrive with mock drivetrain and vision."""
    from subsystems.drivetrain import Drivetrain
    drivetrain = Drivetrain()  # Will use mock motors
    return AutonDrive(drivetrain)


def test_target_left_rotates_left(auton_drive):
    """When target is left of center, robot should rotate left."""
    vision = get_mock_vision()

    # Target is 15 degrees to the LEFT
    vision.simulate_target_left(tag_id=20, offset_degrees=15, distance=2.0)

    cmd = auton_drive.align_to_tag(20)
    cmd.initialize()
    cmd.execute()

    # tx = -15 (left), so rotation should be -(-15) * 0.1 = +1.5 (rotate left/CCW)
    # Check the drivetrain received positive rotation
    assert auton_drive.drivetrain.last_rotation > 0, \
        "Should rotate left (positive) when target is left of center"


def test_target_right_rotates_right(auton_drive):
    """When target is right of center, robot should rotate right."""
    vision = get_mock_vision()

    # Target is 15 degrees to the RIGHT
    vision.simulate_target_right(tag_id=20, offset_degrees=15, distance=2.0)

    cmd = auton_drive.align_to_tag(20)
    cmd.initialize()
    cmd.execute()

    # tx = +15 (right), so rotation should be -(+15) * 0.1 = -1.5 (rotate right/CW)
    assert auton_drive.drivetrain.last_rotation < 0, \
        "Should rotate right (negative) when target is right of center"


def test_far_target_drives_forward(auton_drive):
    """When target is far, robot should drive forward."""
    vision = get_mock_vision()

    # Target is centered but 3 meters away (target is 1m)
    vision.simulate_target_centered(tag_id=20, distance=3.0)

    cmd = auton_drive.align_to_tag(20)
    cmd.initialize()
    cmd.execute()

    # distance=3.0, target=1.0, so speed_x = (3-1)*0.5 = 1.0 (forward)
    assert auton_drive.drivetrain.last_speed_x > 0, \
        "Should drive forward when target is far"


def test_close_target_drives_backward(auton_drive):
    """When target is too close, robot should back up."""
    vision = get_mock_vision()

    # Target is centered but only 0.5 meters away (target is 1m)
    vision.simulate_target_centered(tag_id=20, distance=0.5)

    cmd = auton_drive.align_to_tag(20)
    cmd.initialize()
    cmd.execute()

    # distance=0.5, target=1.0, so speed_x = (0.5-1)*0.5 = -0.25 (backward)
    assert auton_drive.drivetrain.last_speed_x < 0, \
        "Should drive backward when target is too close"


def test_on_target_finishes_command(auton_drive):
    """Command should finish when aligned."""
    vision = get_mock_vision()

    # Target is perfectly centered at target distance
    vision.simulate_target_centered(tag_id=20, distance=1.0)

    cmd = auton_drive.align_to_tag(20)
    cmd.initialize()
    cmd.execute()

    assert cmd.isFinished(), "Should finish when on target"


def test_lost_target_finishes_command(auton_drive):
    """Command should finish if target is lost."""
    vision = get_mock_vision()

    # Start with a target
    vision.simulate_target_centered(tag_id=20, distance=2.0)

    cmd = auton_drive.align_to_tag(20)
    cmd.initialize()
    cmd.execute()

    assert not cmd.isFinished(), "Should not be finished yet"

    # Lose the target
    vision.simulate_no_target()

    assert cmd.isFinished(), "Should finish when target lost"


def test_strafe_correction_for_offset_target(auton_drive):
    """Robot should strafe to center on target."""
    vision = get_mock_vision()

    # Target is 10 degrees to the right
    vision.simulate_target_right(tag_id=20, offset_degrees=10, distance=1.0)

    cmd = auton_drive.align_to_tag(20)
    cmd.initialize()
    cmd.execute()

    # tx = +10, so speed_y = -10 * 0.05 = -0.5 (strafe left to center)
    assert auton_drive.drivetrain.last_speed_y < 0, \
        "Should strafe left when target is to the right"
```

### Testing Complex Auto Sequences with Vision

```python
# tests/test_auto_with_vision.py

def test_two_piece_auto_sequence(setup_mocks):
    """Test full autonomous with vision alignment."""
    vision = get_mock_vision()
    arm = Arm()
    intake = Intake()
    drivetrain = Drivetrain()
    auton_drive = AutonDrive(drivetrain)

    auton_modes = AutonModes(drivetrain, arm, intake, auton_drive)

    # Setup: scoring tag visible and centered
    vision.simulate_target_centered(tag_id=20, distance=1.0)

    cmd = auton_modes.two_piece("blue_left")
    cmd.initialize()

    # Run a few cycles
    for _ in range(10):
        cmd.execute()
        if cmd.isFinished():
            break

    # Verify arm moved to score position
    assert arm.motor.command_history, "Arm should have received commands"

    # Verify intake ran
    assert intake.motor.command_history, "Intake should have received commands"
```

### Tips for Vision Testing

1. **Test edge cases:**
   - Target at extreme angles (±30°)
   - Target very close (< 0.5m) or far (> 5m)
   - Target lost mid-alignment
   - Wrong tag detected

2. **Verify directions:**
   - Left target → rotate left, strafe right
   - Right target → rotate right, strafe left
   - Far target → drive forward
   - Close target → drive backward

3. **Test tolerances:**
   - Just inside tolerance → command finishes
   - Just outside tolerance → command continues

4. **Simulate real sequences:**
   - Target starts off-center, gradually gets centered as commands run
   - Multiple targets visible, verify correct one selected

---

## 10. Testing

**This is where phoenix-v1 was weak.** We had minimal automated tests. For 2026, we should:

### Test Structure

```
tests/
├── conftest.py           # Pytest fixtures (mock mode setup)
├── test_subsystems.py    # Unit tests for each subsystem
├── test_commands.py      # Test command behavior
├── test_autonomous.py    # Test auto routines
└── test_integration.py   # End-to-end tests
```

### conftest.py (Test Setup)

```python
# tests/conftest.py

import pytest
from hardware import set_mock_mode
from handlers import set_mock_vision_mode

@pytest.fixture(autouse=True)
def mock_hardware():
    """Automatically use mock hardware for all tests."""
    set_mock_mode(True)
    yield
    set_mock_mode(False)

@pytest.fixture(autouse=True)
def mock_vision():
    """Automatically use mock vision for all tests."""
    set_mock_vision_mode(True)
    yield
    set_mock_vision_mode(False)
```

### Example Tests

```python
# tests/test_subsystems.py

from subsystems.arm import Arm
from constants import CON_ARM

def test_arm_respects_voltage_limits():
    arm = Arm()
    arm._set_voltage(999)  # Way over limit
    assert arm.motor.get_last_voltage() == CON_ARM["max_voltage"]

def test_arm_at_target_within_tolerance():
    arm = Arm()
    arm.motor.simulate_position(90.0)
    arm._target = 90.0
    assert arm.at_target()

    arm._target = 91.0  # Just outside position but within tolerance
    assert arm.at_target()

    arm._target = 180.0  # Way off
    assert not arm.at_target()
```

```python
# tests/test_commands.py

from subsystems.arm import Arm

def test_go_to_position_command_lifecycle():
    arm = Arm()
    arm.motor.simulate_position(0)

    cmd = arm.go_to_position(90)

    # Initialize sets target
    cmd.initialize()
    assert arm._target == 90

    # Execute sends voltage
    cmd.execute()
    assert arm.motor.get_last_voltage() > 0  # Moving toward target

    # Not finished yet
    assert not cmd.isFinished()

    # Simulate reaching target
    arm.motor.simulate_position(90)
    assert cmd.isFinished()

    # End stops motor
    cmd.end(False)
    assert arm.motor.get_last_voltage() == 0
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=subsystems --cov=hardware

# Run specific test file
python -m pytest tests/test_subsystems.py -v
```

### CI Pipeline (GitHub Actions)

```yaml
# .github/workflows/test.yml

name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: python -m pytest tests/ -v --cov
```

---

## 11. Physics Simulation for Testing (NEW)

This is a major improvement for 2026: **calibrate a physics model from real robot measurements**, then use it to test autonomous routines in pure code.

Instead of just checking "did the motor receive 6V?", we can verify "did the robot end up at the right position?"

### The Concept

1. **Calibrate once** on the real robot:
   - At 12V, robot drives at X m/s
   - At 12V rotation, robot turns at Y deg/s
   - Arm moves at Z deg/s per volt

2. **Build physics model** using those measurements

3. **Run tests** that step through time, updating simulated position/heading

4. **Verify outcomes**: "After this auto routine, robot should be at (2, 1) facing 90°"

### Calibration Process

Run these tests on the real robot and record the results:

```python
# calibration/measure_drivetrain.py
"""
Run this on the real robot to measure drivetrain characteristics.
Record values in constants.py under SIM_CALIBRATION.
"""

from wpilib import Timer
import math

def measure_max_speed():
    """
    Procedure:
    1. Place robot in open area with room to drive
    2. Run this function
    3. Robot will drive at full voltage for 2 seconds
    4. Measure distance traveled (use tape measure or vision)
    5. Calculate: speed = distance / 2.0
    """
    print("Starting max speed test in 3 seconds...")
    print("Robot will drive forward at full power for 2 seconds")
    # ... implementation

def measure_rotation_rate():
    """
    Procedure:
    1. Place robot in open area
    2. Mark starting heading (use tape on floor)
    3. Run this function
    4. Robot will rotate at full voltage for 2 seconds
    5. Measure total rotation in degrees
    6. Calculate: rate = degrees / 2.0 (deg/s)
    """
    print("Starting rotation test in 3 seconds...")
    # ... implementation

def measure_mechanism_speed(mechanism_name):
    """
    Procedure:
    1. Move mechanism to known starting position
    2. Run at known voltage for measured time
    3. Record ending position
    4. Calculate: speed = (end - start) / time (units/s at that voltage)
    """
    pass
```

### Calibration Constants

```python
# constants.py

# =============================================================================
# SIMULATION CALIBRATION - Measured from real robot
# =============================================================================
SIM_CALIBRATION = {
    "drivetrain": {
        # Measured: at 12V, robot moves at 5.2 m/s
        "max_speed_mps": 5.2,
        "voltage_to_speed": 5.2 / 12.0,  # m/s per volt ≈ 0.433

        # Measured: at 12V rotation, robot turns at 540 deg/s
        "max_rotation_dps": 540,
        "voltage_to_rotation": 540 / 12.0,  # deg/s per volt = 45

        # Acceleration (estimated or measured)
        "accel_mps2": 8.0,  # m/s² - how fast it reaches max speed
        "rotation_accel_dps2": 720,  # deg/s² - rotation acceleration
    },

    "arm": {
        # Measured: at 10V, arm moves at 90 deg/s
        "max_speed_dps": 90,
        "voltage_to_speed": 90 / 10.0,  # deg/s per volt = 9
    },

    "elevator": {
        # Measured: at 12V, elevator moves at 1.5 m/s (or rotations/s)
        "max_speed": 1.5,
        "voltage_to_speed": 1.5 / 12.0,  # units/s per volt
    },
}

# Simulation time step (matches robot periodic rate)
SIM_DT = 0.020  # 20ms, same as robot loop
```

### Physics Simulation Classes

```python
# testing/physics_sim.py

import math
from dataclasses import dataclass, field
from typing import Optional
from constants import SIM_CALIBRATION, SIM_DT

@dataclass
class Pose2D:
    """Robot position and heading on the field."""
    x: float = 0.0       # meters, +X is toward opposing alliance
    y: float = 0.0       # meters, +Y is to the left
    heading: float = 0.0 # degrees, 0 = facing +X, 90 = facing +Y

    def distance_to(self, other: 'Pose2D') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

    def __repr__(self):
        return f"Pose2D(x={self.x:.2f}, y={self.y:.2f}, heading={self.heading:.1f}°)"


@dataclass
class DrivetrainState:
    """Current state of simulated drivetrain."""
    pose: Pose2D = field(default_factory=Pose2D)
    velocity_x: float = 0.0   # m/s in field frame
    velocity_y: float = 0.0   # m/s in field frame
    rotation_rate: float = 0.0  # deg/s

    # Command inputs (what the code is requesting)
    commanded_vx: float = 0.0
    commanded_vy: float = 0.0
    commanded_rotation: float = 0.0


class DrivetrainPhysicsSim:
    """
    Simulates drivetrain physics based on calibrated measurements.
    Call step() every 20ms (or your test time step) to update state.
    """

    def __init__(self):
        self.state = DrivetrainState()
        self.cal = SIM_CALIBRATION["drivetrain"]

        # Track command history for debugging
        self.command_history: list[dict] = []
        self.pose_history: list[Pose2D] = []

    def set_command(self, velocity_x: float, velocity_y: float, rotation: float) -> None:
        """
        Set drive command (typically called from mock drivetrain).

        Args:
            velocity_x: Commanded X velocity (m/s, field-relative)
            velocity_y: Commanded Y velocity (m/s, field-relative)
            rotation: Commanded rotation rate (deg/s or rad/s depending on your convention)
        """
        self.state.commanded_vx = velocity_x
        self.state.commanded_vy = velocity_y
        self.state.commanded_rotation = rotation

        self.command_history.append({
            "vx": velocity_x,
            "vy": velocity_y,
            "rotation": rotation,
        })

    def step(self, dt: float = SIM_DT) -> None:
        """
        Advance simulation by one time step.
        Call this in your test loop to simulate time passing.
        """
        # Simple model: velocity approaches commanded velocity with acceleration limit
        # More sophisticated: model inertia, wheel slip, etc.

        accel = self.cal["accel_mps2"]
        rot_accel = self.cal["rotation_accel_dps2"]

        # Update velocities (simple approach toward commanded)
        self.state.velocity_x = self._approach(
            self.state.velocity_x, self.state.commanded_vx, accel * dt
        )
        self.state.velocity_y = self._approach(
            self.state.velocity_y, self.state.commanded_vy, accel * dt
        )
        self.state.rotation_rate = self._approach(
            self.state.rotation_rate, self.state.commanded_rotation, rot_accel * dt
        )

        # Clamp to max speeds
        max_speed = self.cal["max_speed_mps"]
        speed = math.sqrt(self.state.velocity_x**2 + self.state.velocity_y**2)
        if speed > max_speed:
            scale = max_speed / speed
            self.state.velocity_x *= scale
            self.state.velocity_y *= scale

        self.state.rotation_rate = max(-self.cal["max_rotation_dps"],
                                        min(self.state.rotation_rate, self.cal["max_rotation_dps"]))

        # Update pose
        self.state.pose.x += self.state.velocity_x * dt
        self.state.pose.y += self.state.velocity_y * dt
        self.state.pose.heading += self.state.rotation_rate * dt

        # Normalize heading to [-180, 180]
        while self.state.pose.heading > 180:
            self.state.pose.heading -= 360
        while self.state.pose.heading < -180:
            self.state.pose.heading += 360

        # Record for analysis
        self.pose_history.append(Pose2D(
            self.state.pose.x, self.state.pose.y, self.state.pose.heading
        ))

    def _approach(self, current: float, target: float, max_delta: float) -> float:
        """Move current toward target by at most max_delta."""
        diff = target - current
        if abs(diff) <= max_delta:
            return target
        return current + math.copysign(max_delta, diff)

    def reset(self, pose: Optional[Pose2D] = None) -> None:
        """Reset simulation to starting state."""
        self.state = DrivetrainState()
        if pose:
            self.state.pose = pose
        self.command_history.clear()
        self.pose_history.clear()

    def run_for(self, seconds: float, dt: float = SIM_DT) -> None:
        """Run simulation for specified duration."""
        steps = int(seconds / dt)
        for _ in range(steps):
            self.step(dt)

    @property
    def pose(self) -> Pose2D:
        return self.state.pose


@dataclass
class MechanismState:
    """State of a single-axis mechanism (arm, elevator, etc.)."""
    position: float = 0.0
    velocity: float = 0.0
    commanded_voltage: float = 0.0


class MechanismPhysicsSim:
    """
    Simulates a single-axis mechanism (arm, elevator) based on calibration.
    """

    def __init__(self, name: str, min_pos: float, max_pos: float):
        self.name = name
        self.state = MechanismState()
        self.min_pos = min_pos
        self.max_pos = max_pos

        if name in SIM_CALIBRATION:
            self.cal = SIM_CALIBRATION[name]
        else:
            # Default calibration
            self.cal = {"voltage_to_speed": 10.0}

    def set_voltage(self, voltage: float) -> None:
        """Set commanded voltage (from mock motor)."""
        self.state.commanded_voltage = voltage

    def step(self, dt: float = SIM_DT) -> None:
        """Advance simulation by one time step."""
        # Velocity proportional to voltage
        target_velocity = self.state.commanded_voltage * self.cal["voltage_to_speed"]

        # Simple model: instant velocity change (could add acceleration)
        self.state.velocity = target_velocity

        # Update position
        new_pos = self.state.position + self.state.velocity * dt

        # Clamp to limits
        self.state.position = max(self.min_pos, min(new_pos, self.max_pos))

        # Stop if at limit
        if self.state.position == self.min_pos or self.state.position == self.max_pos:
            self.state.velocity = 0

    def reset(self, position: float = 0.0) -> None:
        self.state = MechanismState(position=position)

    @property
    def position(self) -> float:
        return self.state.position
```

### Integrating Physics with Mock Hardware

```python
# hardware/mock_hardware.py (updated)

from testing.physics_sim import DrivetrainPhysicsSim, MechanismPhysicsSim, Pose2D

class MockDrivetrain:
    """Mock drivetrain with physics simulation."""

    def __init__(self):
        self.physics = DrivetrainPhysicsSim()

        # Track raw commands for simple tests
        self.last_vx = 0.0
        self.last_vy = 0.0
        self.last_rotation = 0.0

    def drive(self, velocity_x: float, velocity_y: float, rotation: float) -> None:
        """Apply drive command."""
        self.last_vx = velocity_x
        self.last_vy = velocity_y
        self.last_rotation = rotation

        # Feed to physics sim
        self.physics.set_command(velocity_x, velocity_y, rotation)

    def step(self, dt: float = 0.020) -> None:
        """Advance physics simulation."""
        self.physics.step(dt)

    @property
    def pose(self) -> Pose2D:
        return self.physics.pose

    def reset(self, pose: Pose2D = None) -> None:
        self.physics.reset(pose)


class MockMotorWithPhysics:
    """Mock motor that updates a mechanism physics sim."""

    def __init__(self, physics_sim: MechanismPhysicsSim):
        self.physics = physics_sim
        self._voltage = 0.0

    def set_voltage(self, volts: float) -> None:
        self._voltage = volts
        self.physics.set_voltage(volts)

    def get_position(self) -> float:
        return self.physics.position

    def get_last_voltage(self) -> float:
        return self._voltage

    def step(self, dt: float = 0.020) -> None:
        self.physics.step(dt)
```

### Simulation Test Runner

```python
# testing/sim_runner.py

from testing.physics_sim import SIM_DT

class SimulationRunner:
    """
    Coordinates stepping through time for all simulated components.
    Use this to run autonomous commands and verify outcomes.
    """

    def __init__(self):
        self.components = []  # List of objects with .step() method
        self.time = 0.0

    def register(self, component) -> None:
        """Register a component to be stepped."""
        if hasattr(component, 'step'):
            self.components.append(component)

    def step(self, dt: float = SIM_DT) -> None:
        """Advance all components by one time step."""
        for comp in self.components:
            comp.step(dt)
        self.time += dt

    def run_for(self, seconds: float, dt: float = SIM_DT) -> None:
        """Run simulation for specified duration."""
        steps = int(seconds / dt)
        for _ in range(steps):
            self.step(dt)

    def run_command(self, command, timeout: float = 10.0, dt: float = SIM_DT) -> bool:
        """
        Run a command until it finishes or times out.
        Returns True if command finished, False if timed out.
        """
        command.initialize()
        elapsed = 0.0

        while elapsed < timeout:
            command.execute()
            self.step(dt)
            elapsed += dt

            if command.isFinished():
                command.end(False)
                return True

        command.end(True)  # Interrupted due to timeout
        return False

    def reset(self) -> None:
        """Reset simulation time."""
        self.time = 0.0
        for comp in self.components:
            if hasattr(comp, 'reset'):
                comp.reset()
```

### Example Tests with Physics

```python
# tests/test_auto_physics.py

import pytest
import math
from testing.physics_sim import Pose2D, DrivetrainPhysicsSim
from testing.sim_runner import SimulationRunner
from hardware import set_mock_mode
from handlers import set_mock_vision_mode, get_mock_vision

@pytest.fixture
def sim():
    """Create simulation environment."""
    set_mock_mode(True)
    set_mock_vision_mode(True)

    runner = SimulationRunner()
    yield runner

    set_mock_mode(False)
    set_mock_vision_mode(False)


def test_drive_forward_reaches_target(sim):
    """Verify driving forward for 2 seconds reaches expected distance."""
    from subsystems.drivetrain import Drivetrain

    drivetrain = Drivetrain()  # Uses mock with physics
    sim.register(drivetrain)

    # Command: drive forward at 2 m/s
    drivetrain.drive(velocity_x=2.0, velocity_y=0, rotation=0)

    # Run for 2 seconds
    sim.run_for(2.0)

    # At 2 m/s for 2 seconds = 4 meters (approximately, with acceleration)
    assert drivetrain.pose.x > 3.5, f"Expected ~4m forward, got {drivetrain.pose.x:.2f}m"
    assert drivetrain.pose.x < 4.5
    assert abs(drivetrain.pose.y) < 0.1, "Should not drift sideways"
    assert abs(drivetrain.pose.heading) < 1.0, "Should not rotate"


def test_rotation_reaches_target_heading(sim):
    """Verify rotation command turns robot expected amount."""
    from subsystems.drivetrain import Drivetrain

    drivetrain = Drivetrain()
    sim.register(drivetrain)

    # Command: rotate at 90 deg/s
    drivetrain.drive(velocity_x=0, velocity_y=0, rotation=90)

    # Run for 1 second
    sim.run_for(1.0)

    # Should be close to 90 degrees
    assert drivetrain.pose.heading > 80, f"Expected ~90°, got {drivetrain.pose.heading:.1f}°"
    assert drivetrain.pose.heading < 100


def test_arm_reaches_position(sim):
    """Verify arm moves to target position."""
    from subsystems.arm import Arm

    arm = Arm()  # Uses mock motor with physics
    sim.register(arm)

    # Start at 0, go to 90 degrees
    arm.motor.physics.reset(position=0)

    cmd = arm.go_to_position(90)
    finished = sim.run_command(cmd, timeout=5.0)

    assert finished, "Command should have finished"
    assert abs(arm.get_position() - 90) < 5, f"Arm should be at 90°, got {arm.get_position():.1f}°"


def test_vision_alignment_reaches_target(sim):
    """Verify vision alignment command centers on target."""
    from subsystems.drivetrain import Drivetrain
    from autonomous.auton_drive import AutonDrive

    drivetrain = Drivetrain()
    sim.register(drivetrain)

    auton_drive = AutonDrive(drivetrain)
    vision = get_mock_vision()

    # Start with target 15 degrees to the left, 3 meters away
    vision.simulate_target_left(tag_id=20, offset_degrees=15, distance=3.0)

    # As robot rotates and moves, update mock vision to simulate getting closer
    # (In a real test, you'd update vision based on pose, but this shows the concept)

    cmd = auton_drive.align_to_tag(20)
    cmd.initialize()

    # Run a few cycles manually to show the approach
    for i in range(50):  # 1 second of simulation
        cmd.execute()
        sim.step()

        # Simulate target getting more centered as robot moves
        current_offset = 15 - (i * 0.3)  # Decreasing offset
        current_distance = 3.0 - (i * 0.04)  # Getting closer

        if current_distance < 1.0:
            vision.simulate_target_centered(tag_id=20, distance=1.0)
            break
        else:
            vision.set_target(vision.VisionTarget(
                tag_id=20,
                tx=-current_offset,
                ty=0,
                distance=current_distance,
                yaw=0,
            ))

    # Robot should have moved forward and rotated
    assert drivetrain.pose.x > 0.5, "Should have driven forward"


def test_full_auto_routine_reaches_scoring_position(sim):
    """
    Integration test: Full auto routine ends at expected field position.
    This is the holy grail - test the whole auto in simulation.
    """
    from robot_container import RobotContainer

    container = RobotContainer()  # Creates all subsystems with mocks
    sim.register(container.drivetrain)
    sim.register(container.arm)

    vision = get_mock_vision()

    # Setup starting position (blue left starting zone)
    container.drivetrain.physics.reset(Pose2D(x=0, y=0, heading=0))

    # Simulate scoring target visible
    vision.simulate_target_centered(tag_id=20, distance=2.0)

    # Get and run the auto command
    auto_cmd = container.auton_modes.simple_score("blue_left")
    finished = sim.run_command(auto_cmd, timeout=15.0)

    assert finished, "Auto should complete within timeout"

    # Verify robot ended up in reasonable position
    # (exact values depend on your auto routine)
    assert container.drivetrain.pose.x > 1.0, "Should have driven forward"
    print(f"Final pose: {container.drivetrain.pose}")


def test_two_piece_auto_timing(sim):
    """Verify two-piece auto completes in expected time."""
    from robot_container import RobotContainer

    container = RobotContainer()
    sim.register(container.drivetrain)
    sim.register(container.arm)
    sim.register(container.intake)

    vision = get_mock_vision()
    vision.simulate_target_centered(tag_id=20, distance=2.0)

    auto_cmd = container.auton_modes.two_piece("blue_left")

    start_time = sim.time
    finished = sim.run_command(auto_cmd, timeout=15.0)
    elapsed = sim.time - start_time

    assert finished, "Auto should complete"
    assert elapsed < 14.0, f"Auto took {elapsed:.1f}s, should be under 14s for 15s auto period"
    print(f"Two-piece auto completed in {elapsed:.1f} seconds")
```

### Debugging Simulation

```python
# tests/test_debug_auto.py

def test_auto_with_trajectory_output(sim):
    """Run auto and output trajectory for visualization."""
    from subsystems.drivetrain import Drivetrain

    drivetrain = Drivetrain()
    sim.register(drivetrain)

    # Run some commands...
    drivetrain.drive(velocity_x=2.0, velocity_y=0, rotation=45)
    sim.run_for(2.0)

    drivetrain.drive(velocity_x=0, velocity_y=1.0, rotation=0)
    sim.run_for(1.0)

    # Output trajectory for plotting
    print("\n--- Trajectory ---")
    for i, pose in enumerate(drivetrain.physics.pose_history[::10]):  # Every 10th point
        print(f"{i*0.2:.1f}s: x={pose.x:.2f}, y={pose.y:.2f}, θ={pose.heading:.1f}°")

    # Could also write to CSV for plotting in Excel/Python
    with open("trajectory.csv", "w") as f:
        f.write("time,x,y,heading\n")
        for i, pose in enumerate(drivetrain.physics.pose_history):
            t = i * 0.020
            f.write(f"{t:.3f},{pose.x:.3f},{pose.y:.3f},{pose.heading:.1f}\n")
```

### Calibration Checklist

Before competition, run these calibration tests on the real robot:

```markdown
## Drivetrain Calibration Checklist

- [ ] **Max Speed Test**
  - Drive at 12V for 2 seconds
  - Measure distance traveled: ______ meters
  - Calculate: speed = distance / 2.0 = ______ m/s
  - Update `SIM_CALIBRATION["drivetrain"]["max_speed_mps"]`

- [ ] **Rotation Rate Test**
  - Rotate at 12V for 2 seconds
  - Measure total rotation: ______ degrees
  - Calculate: rate = degrees / 2.0 = ______ deg/s
  - Update `SIM_CALIBRATION["drivetrain"]["max_rotation_dps"]`

- [ ] **Acceleration Test** (optional)
  - Time from 0 to max speed: ______ seconds
  - Calculate: accel = max_speed / time = ______ m/s²
  - Update `SIM_CALIBRATION["drivetrain"]["accel_mps2"]`

## Mechanism Calibration

- [ ] **Arm Speed Test**
  - Run arm at 10V
  - Measure time for 90° rotation: ______ seconds
  - Calculate: speed = 90 / time = ______ deg/s at 10V
  - Update `SIM_CALIBRATION["arm"]["voltage_to_speed"]`

- [ ] **Elevator Speed Test**
  - Run elevator at 12V
  - Measure time for full travel: ______ seconds
  - Calculate speed and update calibration
```

---

## 12. Development Workflow

### Starting a New Mechanism

1. **Add config to `constants.py`:**
   ```python
   MOTOR_IDS["new_mechanism"] = 30
   CON_NEW_MECHANISM = {"max_voltage": 8, "tolerance": 2, ...}
   ```

2. **Create subsystem file:** Copy template from section 4

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
