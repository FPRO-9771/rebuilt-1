# Shooter System

**Team 9771 FPRO - 2026**

This doc covers the shooter system: a turret, flywheel launcher, and adjustable hood. The system is built from small, independent command modules that can be used individually or composed together.

> **When to read this:** You're tuning the shooter, adding a new mechanism to the system, or trying to understand how the command modules compose.

---

## Table of Contents

1. [System Overview](#1-system-overview) (includes [Turret Motor Swap](#turret-motor-swap-kraken-vs-minion))
2. [Subsystem Patterns](#2-subsystem-patterns)
3. [Distance Lookup Table](#3-distance-lookup-table)
4. [Command Modules](#4-command-modules)
5. [How Commands Compose](#5-how-commands-compose)

---

## 1. System Overview

The shooter has three mechanisms. Three independent command modules control them. CoordinateAim, AutoShoot, and ShootWhenReady all consume a shared `ShootContext` from a single supplier (built in `controls/operator_controls.py`):

```
              _make_shoot_context_supplier()
              (controls/operator_controls.py)
                 pose -> shooter position -> target -> velocity
                 -> raw distance -> corrected distance
                            |
              +-------------+-------------+
              |             |             |
              v             v             v
+-----------------+ +-----------------+ +-----------------+
| CoordinateAim   | | AutoShoot       | | ShootWhenReady  |
| (Y toggle)      | | (LB hold)      | | (LT hold)       |
|                 | |                 | |                 |
| ctx -> angle    | | ctx -> dist     | | ctx -> dist     |
| PD -> turret    | | table -> RPS,  | | table -> RPS,  |
| publishes       | |   hood          | |   hood + feeds  |
|   AutoAim       | | req: launcher, | |   when ready    |
| req: turret     | |      hood       | | req: launcher, |
+-----------------+ +-----------------+ |   hood, feeds   |
                                        +-----------------+

+-----------------+
| ManualLauncher  |
| (A toggle)      |
|                 |
| stick -> RPS    |
| req: launcher   |
+-----------------+
```

| Component | Motor | Controller | Control Mode |
|-----------|-------|------------|--------------|
| Turret (default) | Kraken X60 | TalonFX | Voltage (PD-control from odometry) |
| Turret (alternate) | Minion | TalonFXS | Voltage (same PD-control) |
| Launcher | Kraken X60 | TalonFX | Closed-loop velocity |
| Hood | WCP | TalonFXS | Closed-loop position |

All three are "dumb" subsystems -- they don't know about each other or about vision. Small command modules coordinate them, and the operator chooses which to enable.

### Turret Motor Swap: Kraken vs Minion

We have two turret subsystem files with identical public interfaces so all commands (CoordinateAim, manual control) work with either motor:

| | Kraken X60 (default) | Minion (alternate) |
|---|---|---|
| Subsystem file | `subsystems/turret.py` | `subsystems/turret_minion.py` |
| Constants | `CON_TURRET` | `CON_TURRET_MINION` |
| Motor ID entry | `MOTOR_IDS["turret"]` | `MOTOR_IDS["turret_minion"]` |
| Controller type | TalonFX | TalonFXS |
| Gear ratio | 18:90 (5:1) | 18:90 (5:1) |
| Free speed | ~6000 RPM | ~7700 RPM |
| Stall torque | ~7.09 Nm | ~3.17 Nm |
| Weight | ~1.1 lbs | 0.65 lbs |

The Minion has higher free speed but lower torque. Both are more than sufficient for turret rotation through the 5:1 gear ratio at the low voltages we use (0.35-0.8V typical).

**How to switch between Kraken and Minion:**

1. In `constants/ids.py`, flip the `wired` flags:
   ```python
   # For Kraken (default):
   "turret":        {..., "wired": True},
   "turret_minion": {..., "wired": False},

   # For Minion:
   "turret":        {..., "wired": False},
   "turret_minion": {..., "wired": True},
   ```

2. In `robot_container.py`, swap the import:
   ```python
   # For Kraken (default):
   from subsystems.turret import Turret

   # For Minion:
   from subsystems.turret_minion import TurretMinion as Turret
   ```

3. Tune constants for whichever motor is active. The Minion variant uses `CON_TURRET_MINION` in `constants/shooter.py`, which includes slot0 PID gains for closed-loop position hold and brake mode.

**Why two files instead of a flag?** The TalonFXS needs brake mode and slot0 PID gains passed at construction time, which is different enough from the TalonFX path that a clean separate file is easier to read and debug than conditionals. Both files are short and follow the same pattern.

---

## 2. Subsystem Patterns

Each shooter subsystem follows the standard template from [Hardware & Subsystems](hardware-and-subsystems.md) but demonstrates a different control pattern.

### Turret: Voltage Control with Soft Limits

> **Two variants exist:** `subsystems/turret.py` (Kraken/TalonFX) and `subsystems/turret_minion.py` (Minion/TalonFXS). Both use the same pattern below. See [Turret Motor Swap](#turret-motor-swap-kraken-vs-minion) above for switching instructions.

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

The flywheel needs consistent speed regardless of battery voltage. Phoenix 6's `VelocityVoltage` handles PID internally -- we just command a target RPS:

```python
# subsystems/launcher.py (key pattern)

def _set_velocity(self, rps: float) -> None:
    """Set flywheel to target velocity using closed-loop control."""
    self.motor.set_velocity(rps)

def is_at_speed(self, target_rps: float) -> bool:
    """Check if flywheel is within tolerance of target speed."""
    return abs(self.get_velocity() - target_rps) <= CON_LAUNCHER["velocity_tolerance"]
```

The `spin_up()` command never finishes -- it holds speed until canceled. This is the correct pattern for a flywheel that should keep spinning.

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

Instead of a formula, we use a table of measured (distance, launcher_rps, hood_position, ball_speed) tuples. This is easier to tune at competition -- just edit numbers in `constants/shooter.py`.

```python
# constants/shooter.py
CON_SHOOTER = {
    "distance_table": [
        # (distance_m, launcher_rps, hood_position, ball_speed_mps)
        (1, 65.0, 0.05, 5.0),
        (2.0, 80.0, 0.10, 7.0),
        (3.0, 95.0, 0.15, 9.0),
    ],
}
```

The `ball_speed_mps` column is used for velocity compensation -- estimating ball flight time so we can adjust for robot movement. `get_shooter_settings()` returns only `(rps, hood)`.

The lookup function in `subsystems/shooter_lookup.py` linearly interpolates between entries:

```python
# At 1.5m --> halfway between (1, 65, 0.05) and (2.0, 80, 0.10)
rps, hood = get_shooter_settings(1.5)
# rps = 72.5, hood = 0.075
```

Distances outside the table range clamp to the nearest entry. This prevents extrapolation errors -- if you're closer than 1m or farther than 3m, you get the closest known-good settings.

### Tuning at Competition

1. Set up at a known distance from the target
2. Use **A button** to toggle launcher on, adjust speed with **right stick Y**
3. Record the RPS and hood angle that score
4. Update the distance table in `constants/shooter.py`
5. Repeat at 3-5 distances
6. The interpolation handles everything in between

---

## 4. Command Modules

The shooter is split into three independent, small command files:

### CoordinateAim (`commands/coordinate_aim.py`)

Odometry-based turret angle calculation. Toggled on/off with **Y button**. The robot's pose is used to compute the angle to the Hub, then movement compensation, turret routing, EMA filtering, and a PD controller with deadband compensation drive the turret motor. Manual turret override (left stick X) interrupts CoordinateAim via WPILib requirements; it resumes on release.

> **Full deep dive:** [Auto-Aim System](auto-aim.md) -- data flow, pose-based aiming, PD controller math, movement compensation, and debugging guide.

### AutoShoot (`commands/auto_shoot.py`)

Receives a `context_supplier` that provides a `ShootContext` -- a struct with the velocity-corrected distance from the shooter to the Hub (plus raw distance, closing speed, and pose data for telemetry). Looks up launcher RPS and hood position from the distance table. Bound to **left bumper whileTrue** -- hold to engage.

Each `execute()` cycle:
1. Call `context_supplier()` to get a `ShootContext` with corrected distance
2. Look up RPS + hood position via `get_shooter_settings(ctx.corrected_distance)`
3. Set launcher velocity and hood position

The context supplier is built in `controls/operator_controls.py` using shared calculation modules:
- `get_shooter_field_position()` -- converts the robot-relative shooter offset to field coordinates (the shooter is not at robot center)
- `compute_range_state()` -- distance and closing speed from shooter to Hub
- `compute_corrected_distance()` -- adjusts distance for closing speed (if approaching, the ball needs less energy)

### ManualLauncher (`commands/manual_launcher.py`)

Maps the right stick Y axis to a launcher RPS range. Toggled on/off with **A button**.

- Stick full forward (1.0) = `CON_MANUAL["launcher_max_rps"]` (100 RPS)
- Stick full back (-1.0) = `CON_MANUAL["launcher_min_rps"]` (40 RPS)
- Stick center (0.0) = midpoint (70 RPS)

---

## 5. How Commands Compose

Each command requires different subsystems, so they can run simultaneously without conflict:

```
commands/
+-- coordinate_aim.py    # Requires: turret
+-- auto_shoot.py        # Requires: launcher, hood
+-- manual_launcher.py   # Requires: launcher
```

| Scenario | What Happens |
|----------|-------------|
| CoordinateAim on + manual turret stick | Stick interrupts CoordinateAim; resumes on release |
| ManualLauncher on + hold left bumper (AutoShoot) | AutoShoot takes launcher -> interrupts ManualLauncher. Release bumper, press A to restart manual. |
| CoordinateAim on + AutoShoot held | Both run simultaneously (different subsystem requirements) |
| ManualLauncher on + CoordinateAim on | Both run simultaneously (different subsystem requirements) |

Odometry is read from the drivetrain but is not gated by `addRequirements`, so multiple commands can read pose data simultaneously.

---

**See also:**
- [Auto-Aim System](auto-aim.md) - Full auto-aim deep dive: pose-based aiming, PD controller, movement compensation, debugging
- [Hardware & Subsystems](hardware-and-subsystems.md) - Subsystem template and TalonFXS support
- [Controls](controls.md) - Full operator control map and override patterns
- [Commands & Controls](commands-and-controls.md) - Command lifecycle and composition
