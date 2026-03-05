# Shooter System

**Team 9771 FPRO - 2026**

This doc covers the automated shooter: a turret, flywheel launcher, and adjustable hood coordinated by vision to aim and fire without operator input.

> **When to read this:** You're tuning the shooter, adding a new mechanism to the system, or trying to understand how multi-subsystem coordination works.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Subsystem Patterns](#2-subsystem-patterns)
3. [Distance Lookup Table](#3-distance-lookup-table)
4. [Shooter Orchestrator](#4-shooter-orchestrator)
5. [Multi-Subsystem Commands](#5-multi-subsystem-commands)

---

## 1. System Overview

The shooter has three mechanisms and a camera, all working together:

```
Limelight Camera (on turret)
        │
        ▼
┌──────────────────────────────┐
│     AutoTracker              │
│  (turret default command)    │
│                              │
│  vision ──► tx, distance     │
│  PD aim ──► turret voltage   │
│  publishes Shooter/Lock      │
│  requires: turret            │
└──────────────────────────────┘
        │ is_locked()
        │ get_distance()
        ▼
┌──────────────────────────────┐
│     ShootCommand             │
│  (Y button whileTrue)       │
│                              │
│  distance ──► lookup table   │
│  launcher ──► _set_velocity  │
│  hood ──► _set_position      │
│  feeder ──► placeholder      │
│  requires: launcher, hood    │
└──────────────────────────────┘
```

| Component | Motor | Controller | Control Mode |
|-----------|-------|------------|--------------|
| Turret | Kraken X60 | TalonFX | Voltage (P-control from vision) |
| Launcher | Kraken X60 | TalonFX | Closed-loop velocity |
| Hood | WCP | TalonFXS | Closed-loop position |

All three are "dumb" subsystems -- they don't know about each other or about vision. Two commands coordinate them: `AutoTracker` (always-on turret aiming) and `ShootCommand` (hold-to-shoot).

---

## 2. Subsystem Patterns

Each shooter subsystem follows the standard template from [Hardware & Subsystems](hardware-and-subsystems.md) but demonstrates a different control pattern.

### Turret: Voltage Control with Soft Limits

The turret rotates via voltage but has physical limits it must not exceed. Safety is enforced inside `_set_voltage()` so every caller gets it automatically:

```python
# subsystems/turret.py (key pattern)

def _set_voltage(self, volts: float) -> None:
    """Apply voltage with safety clamping and soft limit enforcement."""
    max_v = CON_TURRET["max_voltage"]
    clamped = max(-max_v, min(volts, max_v))

    # Block voltage that would push past limits
    pos = self.get_position()
    if pos >= CON_TURRET["max_position"] and clamped > 0:
        clamped = 0
    elif pos <= CON_TURRET["min_position"] and clamped < 0:
        clamped = 0

    self.motor.set_voltage(clamped)
```

The key insight: soft limits allow the motor to return (negative voltage at max, positive at min) but block pushing further. This prevents the turret from driving into a hard stop while still allowing recovery.

### Launcher: Closed-Loop Velocity

The flywheel needs consistent speed regardless of battery voltage. Phoenix 6's `VelocityVoltage` handles PID internally — we just command a target RPS:

```python
# subsystems/launcher.py (key pattern)

def _set_velocity(self, rps: float) -> None:
    """Set flywheel to target velocity using closed-loop control."""
    self.motor.set_velocity(rps)

def is_at_speed(self, target_rps: float) -> bool:
    """Check if flywheel is within tolerance of target speed."""
    return abs(self.get_velocity() - target_rps) <= CON_LAUNCHER["velocity_tolerance"]
```

The `spin_up()` command never finishes — it holds speed until canceled. This is the correct pattern for a flywheel that should keep spinning.

### Hood: Closed-Loop Position with Clamping

The hood adjusts shot angle. Position is clamped before commanding the motor, so it's impossible to request an out-of-range position:

```python
# subsystems/hood.py (key pattern)

def _set_position(self, position: float) -> None:
    """Move hood to position, clamped to min/max limits."""
    clamped = max(CON_HOOD["min_position"], min(position, CON_HOOD["max_position"]))
    self.motor.set_position(clamped)
```

The hood uses `create_motor_fxs()` instead of `create_motor()` because the WCP motor connects through a TalonFXS controller. From the subsystem's perspective, the interface is identical.

---

## 3. Distance Lookup Table

Instead of a formula, we use a table of measured (distance, launcher_rps, hood_position) tuples. This is easier to tune at competition — just edit numbers in `constants.py`.

```python
# constants.py
CON_SHOOTER = {
    "distance_table": [
        # (distance_m, launcher_rps, hood_position)
        (1.0, 30.0, 0.05),
        (2.0, 45.0, 0.10),
        (3.0, 55.0, 0.15),
        (4.0, 65.0, 0.20),
        (5.0, 75.0, 0.24),
    ],
}
```

The lookup function in `subsystems/shooter_lookup.py` linearly interpolates between entries:

```python
# At 2.5m → halfway between (2.0, 45, 0.10) and (3.0, 55, 0.15)
rps, hood = get_shooter_settings(2.5)
# rps = 50.0, hood = 0.125
```

Distances outside the table range clamp to the nearest entry. This prevents extrapolation errors — if you're closer than 1m or farther than 5m, you get the closest known-good settings.

### Tuning at Competition

1. Set up at a known distance from the target
2. Use manual controls (A button + bumpers) to find the RPS and hood angle that score
3. Record the values in the distance table
4. Repeat at 3-5 distances
5. The interpolation handles everything in between

---

## 4. AutoTracker + ShootCommand

The shooter is split into two independent commands:

### AutoTracker (`commands/auto_tracker.py`)

The turret's **default command** during teleop. Runs continuously, aiming at scoring AprilTags via PD control. Uses priority-based targeting with stickiness to avoid oscillation between tags.

Each `execute()` cycle:
1. Check `DriverStation.isTeleopEnabled()` -- skip if not in teleop
2. Select target using priority list + stickiness logic
3. Apply per-tag offsets to tx and distance
4. PD control: `voltage = (tx * p_gain + d_term) * aim_sign`
5. Publish `Shooter/Lock` boolean to SmartDashboard

**Lock conditions** (`is_locked()`):
- Target is visible
- Turret is aligned (tx within tolerance)
- Distance is within the lookup table range

Manual turret override (left stick X) interrupts AutoTracker via WPILib requirements. When the stick is released, AutoTracker resumes automatically as the default command.

### ShootCommand (`commands/shoot_command.py`)

Bound to **Y button whileTrue** -- hold to shoot. Receives the AutoTracker instance to query lock status and distance.

Each `execute()` cycle:
1. Look up RPS + hood position from `tracker.get_distance()`
2. Always: spin launcher, set hood (pre-spin while aiming)
3. If `tracker.is_locked()`: engage feeder (placeholder for now)
4. Else: disengage feeder

On `end()`: stops launcher, stops hood, disengages feeder.

### Interaction Between Commands

AutoTracker only requires **turret**. ShootCommand requires **launcher + hood**. They run simultaneously without conflict -- the operator can hold Y to pre-spin the launcher while the tracker is still acquiring lock.

---

## 5. Multi-Subsystem Commands

Most commands are inner classes of a single subsystem (see the template in [Hardware & Subsystems](hardware-and-subsystems.md)). But some commands need to coordinate multiple subsystems. These live in `commands/`:

```
commands/
├── auto_tracker.py          # Requires turret only (default command)
├── shoot_command.py         # Requires launcher + hood
└── shooter_orchestrator.py  # Legacy -- requires turret + launcher + hood
```

The new pattern splits subsystem requirements so commands can run in parallel:

```python
class AutoTracker(Command):       # Requires: turret
class ShootCommand(Command):      # Requires: launcher, hood
```

AutoTracker and ShootCommand can run simultaneously because they require different subsystems. ShootCommand reads from the tracker instance (not a subsystem requirement) to get distance and lock status.

Vision is not a subsystem (no `addRequirements`), so multiple commands can read from it simultaneously.

---

**See also:**
- [Hardware & Subsystems](hardware-and-subsystems.md) - Subsystem template and TalonFXS support
- [Vision](vision.md) - How the Limelight provides `tx` and `distance`
- [Controls](controls.md) - Manual override controls for testing and emergency use
- [Commands & Controls](commands-and-controls.md) - Command lifecycle and composition
