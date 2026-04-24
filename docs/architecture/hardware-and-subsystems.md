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


class MotorController(ABC):
    """Abstract interface for motor controllers."""

    @abstractmethod
    def set_voltage(self, volts: float) -> None:
        """Apply voltage to motor (open-loop control)."""
        pass

    @abstractmethod
    def set_velocity(self, velocity: float, feedforward: float = 0) -> None:
        """Run at velocity using closed-loop control (rotations per second)."""
        pass

    @abstractmethod
    def set_position(self, position: float, feedforward: float = 0) -> None:
        """Move to position using closed-loop control."""
        pass

    @abstractmethod
    def get_position(self) -> float:
        """Get current position in rotations."""
        pass

    @abstractmethod
    def get_velocity(self) -> float:
        """Get current velocity in rotations per second."""
        pass

    @abstractmethod
    def zero_position(self) -> None:
        """Set current position as zero."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the motor."""
        pass

    def set_follower(self, leader_id: int, oppose_direction: bool = False) -> None:
        """Follow another motor controller. No-op by default."""
        pass
```

The interface has two methods beyond the basic six that are worth noting:

- **`zero_position()`** -- resets the encoder to zero. Called automatically by `create_motor()` on every motor at creation time.
- **`set_follower(leader_id, oppose_direction)`** -- makes this motor mirror another motor's output. The base class provides a no-op default; `TalonFXController` overrides it with real follower logic.

Each real controller (`TalonFXController` in `motor_controller_talon.py`, `TalonFXSController` in `motor_controller_fxs.py`) and `MockMotorController` all implement this same ABC. The implementations live in separate files -- the doc won't reproduce them in full, but the key differences are:

- **TalonFXController** -- wraps a Phoenix 6 `TalonFX`. Accepts optional `slot0` gains dict, `bus` string, and `current_limit` dict.
- **TalonFXSController** -- wraps a Phoenix 6 `TalonFXS`. Also accepts `brake` mode, `current_limit` dict, and configures `MotorArrangementValue.MINION_JST`.
- **MockMotorController** -- tracks commands in `command_history` and provides test helpers like `simulate_position()`, `simulate_velocity()`, `get_last_voltage()`, and `clear_history()`.

### Factory for Creating Motors

There is one factory function, `create_motor()`. It picks the right hardware class based on the `"type"` field in the config dict (`"talon_fx"` or `"talon_fxs"`). Subsystems never need to know which controller type they are using.

```python
# hardware/__init__.py

from .motor_controller import MotorController
from .motor_controller_talon import TalonFXController
from .motor_controller_fxs import TalonFXSController
from .mock_motor_controller import MockMotorController

_use_mock_hardware = False

# Maps config "type" strings to real hardware classes
_MOTOR_TYPES = {
    "talon_fx": TalonFXController,
    "talon_fxs": TalonFXSController,
}

def set_mock_mode(enabled: bool) -> None:
    """Enable mock hardware for testing."""
    global _use_mock_hardware
    _use_mock_hardware = enabled

def is_mock_mode() -> bool:
    """Check if mock mode is enabled."""
    return _use_mock_hardware

def create_motor(
    config: dict,
    inverted: bool = False,
    brake: bool = False,
    slot0: dict | None = None,
) -> MotorController:
    """
    Factory function - returns the right motor controller based on config.

    Args:
        config: Entry from MOTOR_IDS, e.g.
                {"can_id": 30, "type": "talon_fx", "wired": True,
                 "current_limit": {"stator": 40, "supply": 30}}
        inverted: Whether to invert motor direction
        brake: Whether to use brake mode (TalonFXS/Minion only)
        slot0: Optional PID/FF gains, e.g. {"kP": 12.0, "kV": 0.12}

    The factory reads "current_limit" from the config dict and passes it
    to the controller constructor. No extra parameter needed.

    Returns mock in three cases:
      - mock mode is enabled (testing)
      - config has "wired": False (motor not physically connected)
    Otherwise returns the real hardware class.

    Calls zero_position() on every motor before returning it.
    """
    ...
```

### TalonFXS Support

Some motors (like WCP) connect through a TalonFXS controller instead of a TalonFX. The `TalonFXSController` class implements the same `MotorController` ABC, so subsystems don't need to know the difference. The `"type"` field in the motor config dict controls which class gets created -- `"talon_fx"` or `"talon_fxs"`.

In mock/test mode, `create_motor()` always returns a `MockMotorController` regardless of type -- the mock doesn't care which real controller it's standing in for.

### Current Limits

Every motor has current limits configured to prevent brownouts and protect mechanisms. There are two types:

- **Stator current limit** -- limits torque output. Protects mechanisms from excessive force.
- **Supply current limit** -- limits draw from the battery. Prevents brownouts under load.

#### Where to change current limits

Current limits live in two places depending on the motor:

**Mechanism motors** -- `constants/ids.py`. Each motor config dict has a `"current_limit"` field:

```python
MOTOR_IDS = {
    "intake_spinner": {
        "can_id": 40, "type": "talon_fx", "bus": "op_sys", "wired": True,
        "current_limit": {"stator": 30, "supply": 10},  # amps
    },
    ...
}
```

The factory reads `"current_limit"` from the config and passes it to the controller. Both `TalonFXController` and `TalonFXSController` apply it via Phoenix 6 `CurrentLimitsConfigs`. Either `"stator"` or `"supply"` can be omitted if you only want one type.

**Drivetrain motors** -- `generated/tuner_constants.py`. Drive and steer limits are set in `_drive_initial_configs` and `_steer_initial_configs`:

```python
_drive_initial_configs = configs.TalonFXConfiguration().with_current_limits(
    configs.CurrentLimitsConfigs()
    .with_stator_current_limit(80.0)
    .with_stator_current_limit_enable(True)
    .with_supply_current_limit(50.0)
    .with_supply_current_limit_enable(True)
)
```

**Note:** Re-exporting from Phoenix Tuner X will overwrite `generated/tuner_constants.py`. If you re-export, you must re-add the drive motor current limits manually.

#### Current limit summary

| Motor | Stator (A) | Supply (A) | Config file |
|-------|-----------|-----------|-------------|
| Drive (x4) | 80 | 50 | `generated/tuner_constants.py` |
| Steer (x4) | 60 | 35 | `generated/tuner_constants.py` |
| H-feed | 30 | 15 | `constants/ids.py` |
| V-feed | 30 | 15 | `constants/ids.py` |
| Intake spinner | 30 | 10 | `constants/ids.py` |
| Intake left/right | 30 | 10 | `constants/ids.py` |
| Turret (Minion) | 45 | 40 | `constants/ids.py` |
| Launcher | 60 | 40 | `constants/ids.py` |

#### Tuning tips

- If a motor **stalls or smokes** -- lower the stator limit.
- If you're getting **brownouts** -- lower supply limits (especially on intake and drive).
- If a mechanism feels **sluggish** -- raise limits, but watch battery voltage.
- Start conservative, raise only after testing on a charged battery.

### Updated Subsystem (uses abstraction)

```python
# subsystems/arm.py (NEW WAY - testable)
from commands2 import SubsystemBase, Command
from hardware import create_motor
from constants.ids import MOTOR_IDS
from constants.arm import CON_ARM

class Arm(SubsystemBase):
    def __init__(self):
        super().__init__()
        # MOTOR_IDS["arm_main"] is a config dict like:
        #   {"can_id": 10, "type": "talon_fx", "wired": True}
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
from constants.ids import MOTOR_IDS
from constants.[mechanism] import CON_[MECHANISM]

class [Mechanism](SubsystemBase):
    def __init__(self):
        super().__init__()
        # MOTOR_IDS["mechanism_name"] is a config dict with can_id, type, wired
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
