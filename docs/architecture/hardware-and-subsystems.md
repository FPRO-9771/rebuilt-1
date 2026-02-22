# Hardware Abstraction & Subsystem Design

**Team 9771 FPRO - 2026**

This doc covers how we wrap hardware (motors, sensors) behind abstract interfaces so subsystems are testable, and how to structure subsystems that own their mechanisms.

> **When to read this:** You're adding a new mechanism to the robot.

---

## Table of Contents

1. [Hardware Abstraction Layer](#1-hardware-abstraction-layer)
2. [Subsystem Design](#2-subsystem-design)

---

## 1. Hardware Abstraction Layer

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
from phoenix6.controls import VoltageOut, VelocityVoltage, PositionVoltage

class MotorController(ABC):
    """Abstract interface for motor controllers."""

    @abstractmethod
    def set_voltage(self, volts: float) -> None:
        pass

    @abstractmethod
    def set_velocity(self, velocity: float, feedforward: float = 0) -> None:
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

    def set_velocity(self, velocity: float, feedforward: float = 0) -> None:
        self.motor.set_control(VelocityVoltage(velocity).with_feed_forward(feedforward))

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

    def set_velocity(self, velocity: float, feedforward: float = 0) -> None:
        self._velocity = velocity
        self.command_history.append({"type": "velocity", "value": velocity, "ff": feedforward})

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

from .motor_controller import MotorController
from .motor_controller_talon import TalonFXController
from .mock_motor_controller import MockMotorController

_use_mock_hardware = False

def set_mock_mode(enabled: bool) -> None:
    """Enable mock hardware for testing."""
    global _use_mock_hardware
    _use_mock_hardware = enabled

def is_mock_mode() -> bool:
    """Check if mock mode is enabled."""
    return _use_mock_hardware

def create_motor(can_id: int, inverted: bool = False) -> MotorController:
    """Factory function - returns real or mock TalonFX motor based on mode."""
    if _use_mock_hardware:
        return MockMotorController(can_id, inverted)
    return TalonFXController(can_id, inverted)

def create_motor_fxs(can_id: int, inverted: bool = False) -> MotorController:
    """Factory function - returns real or mock TalonFXS motor based on mode."""
    if _use_mock_hardware:
        return MockMotorController(can_id, inverted)
    return TalonFXSController(can_id, inverted)
```

### TalonFXS Support

Some motors (like WCP) connect through a TalonFXS controller instead of a TalonFX. The `TalonFXSController` class implements the same `MotorController` ABC, so subsystems don't need to know the difference. Use `create_motor_fxs()` instead of `create_motor()` when wiring up those motors.

Both factory functions return a `MockMotorController` in test mode — the mock doesn't care which real controller it's standing in for.

### Updated Subsystem (uses abstraction)

```python
# subsystems/arm.py (NEW WAY - testable)
from commands2 import SubsystemBase, Command
from hardware import create_motor
from constants import MOTOR_IDS, CON_ARM  # or: from constants.ids import MOTOR_IDS

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

## 2. Subsystem Design

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
from constants import MOTOR_IDS, CON_[MECHANISM]  # or import from specific file

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

**See also:**
- [Commands & Controls](commands-and-controls.md) - How commands compose and wire to buttons
- [Shooter System](shooter-system.md) - Concrete examples of three different control patterns (voltage, velocity, position)
- [Testing & Simulation](testing-and-simulation.md) - Writing tests against mock hardware
