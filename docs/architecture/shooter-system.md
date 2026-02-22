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
┌─────────────────────────────────────────────┐
│            ShooterOrchestrator               │
│                                             │
│  vision.get_target() ──► tx, distance       │
│                            │                │
│          ┌─────────────────┼────────────┐   │
│          ▼                 ▼            ▼   │
│    Turret aim      Lookup table    Hood pos │
│   (P-control       (distance →    (position │
│    from tx)        rps + hood)    control)  │
│          │                │            │    │
│          ▼                ▼            ▼    │
│     _set_voltage    _set_velocity  _set_pos │
└─────────────────────────────────────────────┘
```

| Component | Motor | Controller | Control Mode |
|-----------|-------|------------|--------------|
| Turret | Kraken X60 | TalonFX | Voltage (P-control from vision) |
| Launcher | Kraken X60 | TalonFX | Closed-loop velocity |
| Hood | WCP | TalonFXS | Closed-loop position |

All three are "dumb" subsystems — they don't know about each other or about vision. The `ShooterOrchestrator` command coordinates them.

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

## 4. Shooter Orchestrator

`commands/shooter_orchestrator.py` is the brain. Each `execute()` cycle:

1. **Query vision** for the target AprilTag
2. **Update state** — if target found, update `tx` and `distance`; if lost, hold last values
3. **Aim turret** — proportional control: `voltage = tx * p_gain`
4. **Look up settings** — interpolate the distance table for RPS and hood position
5. **Command launcher** — closed-loop velocity at the looked-up RPS
6. **Command hood** — closed-loop position at the looked-up angle
7. **Compute readiness** — all aligned AND target visible → `is_ready() == True`

### Target Loss Behavior

When the target disappears (momentary occlusion, camera glitch), the orchestrator holds the last known `tx` and `distance`. This prevents the turret from snapping to center or the launcher from changing speed on a brief dropout. The target must be visible again for `is_ready()` to return True.

### Readiness Check

`is_ready()` is a query, not a trigger. It returns True when all four conditions are met simultaneously:

```python
def is_ready(self) -> bool:
    turret_aligned = abs(self._last_tx) <= CON_SHOOTER["turret_alignment_tolerance"]
    rps, hood_pos = get_shooter_settings(self._last_distance)
    launcher_ready = self.launcher.is_at_speed(rps)
    hood_ready = self.hood.is_at_position(hood_pos)
    return turret_aligned and launcher_ready and hood_ready and self._target_visible
```

A future conveyor command can poll `is_ready()` to decide when to feed a game piece.

### Never Auto-Finishes

The orchestrator runs until canceled by the operator (Y button toggle). `isFinished()` always returns `False`. When `end()` is called, all three motors stop.

---

## 5. Multi-Subsystem Commands

Most commands are inner classes of a single subsystem (see the template in [Hardware & Subsystems](hardware-and-subsystems.md)). But some commands need to coordinate multiple subsystems. These live in `commands/`:

```
commands/
└── shooter_orchestrator.py   # Requires turret + launcher + hood
```

The key pattern: a multi-subsystem command receives subsystem references in its constructor and calls `addRequirements()` for all of them:

```python
class ShooterOrchestrator(Command):
    def __init__(self, turret, launcher, hood, vision):
        super().__init__()
        self.turret = turret
        self.launcher = launcher
        self.hood = hood
        self.vision = vision  # Not a subsystem — no requirement needed
        self.addRequirements(turret, launcher, hood)
```

Because it requires all three subsystems, the scheduler guarantees exclusive access — no other command can control the turret, launcher, or hood while the orchestrator is running. If a manual override command requires one of these subsystems, the scheduler cancels the orchestrator. This is the correct emergency override behavior.

Note: vision is not a subsystem (it has no `addRequirements`), so it's just passed as a dependency. Multiple commands can read from vision simultaneously.

---

**See also:**
- [Hardware & Subsystems](hardware-and-subsystems.md) - Subsystem template and TalonFXS support
- [Vision](vision.md) - How the Limelight provides `tx` and `distance`
- [Controls](controls.md) - Manual override controls for testing and emergency use
- [Commands & Controls](commands-and-controls.md) - Command lifecycle and composition
