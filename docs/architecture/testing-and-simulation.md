# Testing & Simulation

**Team 9771 FPRO - 2026**

This doc covers writing automated tests with mock hardware and running physics simulations to verify autonomous routines reach expected positions.

> **When to read this:** You're writing tests, running simulation, or calibrating physics models.

---

## Table of Contents

1. [Testing](#1-testing)
2. [Physics Simulation](#2-physics-simulation)

---

## 1. Testing

**This is where phoenix-v1 was weak.** We had minimal automated tests. For 2026, we should:

### Test Structure

```
tests/
  conftest.py           # Pytest fixtures (mock mode setup)
  test_subsystems.py    # Unit tests for each subsystem
  test_commands.py      # Test command behavior
  test_autonomous.py    # Test auto routines
  test_integration.py   # End-to-end tests
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

## 2. Physics Simulation

This is a major improvement for 2026: **calibrate a physics model from real robot measurements**, then use it to test autonomous routines in pure code.

Instead of just checking "did the motor receive 6V?", we can verify "did the robot end up at the right position?"

### The Concept

1. **Calibrate once** on the real robot:
   - At 12V, robot drives at X m/s
   - At 12V rotation, robot turns at Y deg/s
   - Arm moves at Z deg/s per volt

2. **Build physics model** using those measurements

3. **Run tests** that step through time, updating simulated position/heading

4. **Verify outcomes**: "After this auto routine, robot should be at (2, 1) facing 90 degrees"

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
        "voltage_to_speed": 5.2 / 12.0,  # m/s per volt ~ 0.433

        # Measured: at 12V rotation, robot turns at 540 deg/s
        "max_rotation_dps": 540,
        "voltage_to_rotation": 540 / 12.0,  # deg/s per volt = 45

        # Acceleration (estimated or measured)
        "accel_mps2": 8.0,  # m/s^2 - how fast it reaches max speed
        "rotation_accel_dps2": 720,  # deg/s^2 - rotation acceleration
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
        return f"Pose2D(x={self.x:.2f}, y={self.y:.2f}, heading={self.heading:.1f} degrees)"


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
    assert drivetrain.pose.heading > 80, f"Expected ~90 degrees, got {drivetrain.pose.heading:.1f} degrees"
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
    assert abs(arm.get_position() - 90) < 5, f"Arm should be at 90 degrees, got {arm.get_position():.1f} degrees"


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
        print(f"{i*0.2:.1f}s: x={pose.x:.2f}, y={pose.y:.2f}, heading={pose.heading:.1f} degrees")

    # Could also write to CSV for plotting in Excel/Python
    with open("trajectory.csv", "w") as f:
        f.write("time,x,y,heading\n")
        for i, pose in enumerate(drivetrain.physics.pose_history):
            t = i * 0.020
            f.write(f"{t:.3f},{pose.x:.3f},{pose.y:.3f},{pose.heading:.1f}\n")
```

### Calibration Checklist

Before competition, run these calibration tests on the real robot:

### Drivetrain Calibration Checklist

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
  - Calculate: accel = max_speed / time = ______ m/s^2
  - Update `SIM_CALIBRATION["drivetrain"]["accel_mps2"]`

### Mechanism Calibration

- [ ] **Arm Speed Test**
  - Run arm at 10V
  - Measure time for 90 degree rotation: ______ seconds
  - Calculate: speed = 90 / time = ______ deg/s at 10V
  - Update `SIM_CALIBRATION["arm"]["voltage_to_speed"]`

- [ ] **Elevator Speed Test**
  - Run elevator at 12V
  - Measure time for full travel: ______ seconds
  - Calculate speed and update calibration

---

**See also:**
- [Hardware & Subsystems](hardware-and-subsystems.md) - Mock hardware that feeds into physics simulation
- [Vision](vision.md) - Testing vision-based alignment with mocks
- [Autonomous](autonomous.md) - Auto routines tested with simulation
