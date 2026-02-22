# Autonomous System

**Team 9771 FPRO - 2026**

This doc covers how to build, organize, and select autonomous routines using command composition.

> **When to read this:** You're building or editing auto routines.

---

## Table of Contents

1. [Structure](#1-structure)
2. [Autonomous Constants](#2-autonomous-constants)
3. [Autonomous Mode Factory](#3-autonomous-mode-factory)
4. [Chooser Setup](#4-chooser-setup)
5. [Using in Robot.py](#5-using-in-robotpy)

---

## 1. Structure

The autonomous system has three concerns:

- **Routines** — Compose commands into full auto sequences (drive here, score, intake, etc.). Each routine is a factory method that returns a fresh `SequentialCommandGroup`.
- **Constants** — Field-position data: AprilTag IDs per starting position, drive paths (velocity/duration tuples), and timing budgets. Separated so you can tweak values without touching command logic.
- **Selection** — Dashboard chooser that stores *factories* (lambdas), not command instances. A fresh command is created each time auto starts, avoiding stale-state bugs.

---

## 2. Autonomous Constants

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

---

## 3. Autonomous Mode Factory

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

---

## 4. Chooser Setup

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

---

## 5. Using in Robot.py

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

**See also:**
- [Commands & Controls](commands-and-controls.md) - Command composition patterns used in auto routines
- [Vision](vision.md) - Using Limelight for vision-based alignment in auto
- [Testing & Simulation](testing-and-simulation.md) - Testing auto routines with physics simulation
