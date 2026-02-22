# Commands & Controls

**Team 9771 FPRO - 2026**

This doc covers the WPILib command-based pattern and how to wire controllers (buttons, joysticks) to robot actions.

> **When to read this:** You're wiring buttons/joysticks to actions, or composing multi-step command sequences.

---

## Table of Contents

1. [Command-Based Architecture](#1-command-based-architecture)
2. [Control Bindings](#2-control-bindings)

---

## 1. Command-Based Architecture

This is the WPILib pattern for robot control. Understanding it is essential.

### Core Concepts

1. **CommandScheduler** - Runs every 20ms, executes all scheduled commands
2. **Command** - A unit of work with `initialize()`, `execute()`, `isFinished()`, `end()`
3. **Subsystem** - Hardware abstraction that commands "require"
4. **Requirements** - A command declares which subsystems it uses; scheduler prevents conflicts

### Command Lifecycle

```
schedule() -> initialize() -> execute() [loop] -> end() when isFinished() == True
                               ^______|
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

## 2. Control Bindings

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

**See also:**
- [Hardware & Subsystems](hardware-and-subsystems.md) - How subsystems expose commands
- [Autonomous](autonomous.md) - Composing commands into auto routines
