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

The shooter has three mechanisms. CoordinateAim, ShootWhenReady, and ManualShoot are all active and wired to controls.

```
Active bindings:

+-----------------+  +-----------------+  +-----------------+
| Manual turret   |  | CoordinateAim   |  | ShootWhenReady  |
| (left stick X)  |  | (LB toggle)     |  | (LT hold)       |
|                 |  |                 |  |                 |
| stick -> volts  |  | turret -> hub   |  | launcher + feed |
| req: turret     |  | req: turret     |  | req: launcher,  |
|                 |  |                 |  |   hood, feeds   |
+-----------------+  +-----------------+  +-----------------+

+-----------------+  +-----------------+
| ManualShoot     |  | ReverseFeeds    |
| (RT hold)       |  | (RB hold)       |
|                 |  |                 |
| launcher +      |  | H feed reverse  |
| auto-feed at    |  | req: h_feed     |
| speed           |  |                 |
| req: launcher,  |  |                 |
|   h_feed, v_feed|  |                 |
+-----------------+  +-----------------+
```

| Component | Motor | Controller | Control Mode |
|-----------|-------|------------|--------------|
| Turret (active) | Minion | TalonFXS | Closed-loop position hold (default command), voltage (manual/auto-aim) |
| Turret (alternate) | Kraken X60 | TalonFX | Same interface, different motor |
| Launcher | Kraken X60 | TalonFX | Closed-loop velocity |
| Hood | WCP | TalonFXS | Closed-loop position |

All three are "dumb" subsystems -- they don't know about each other or about vision. Small command modules coordinate them, and the operator chooses which to enable.

### Turret Motor Swap: Kraken vs Minion

We have two turret subsystem files with identical public interfaces so all commands (CoordinateAim, manual control) work with either motor.

**Currently active: Minion (TalonFXS).** The Kraken import is commented out in `robot_container.py`.

| | Kraken X60 (alternate) | Minion (active) |
|---|---|---|
| Subsystem file | `subsystems/turret.py` | `subsystems/turret_minion.py` |
| Constants | `CON_TURRET` | `CON_TURRET_MINION` |
| Motor ID entry | `MOTOR_IDS["turret"]` | `MOTOR_IDS["turret_minion"]` |
| Controller type | TalonFX | TalonFXS |
| Gear ratio | 18:90 (5:1) | 18:90 (5:1) |
| Free speed | ~6000 RPM | ~7700 RPM |
| Stall torque | ~7.09 Nm | ~3.17 Nm |
| Weight | ~1.1 lbs | 0.65 lbs |

The Minion has higher free speed but lower torque. Both are more than sufficient for turret rotation through the 5:1 gear ratio at the low voltages we use.

**How to switch between Kraken and Minion:**

1. In `constants/ids.py`, flip the `wired` flags:
   ```python
   # For Kraken:
   "turret":        {..., "wired": True},
   "turret_minion": {..., "wired": False},

   # For Minion (current):
   "turret":        {..., "wired": False},
   "turret_minion": {..., "wired": True},
   ```

2. In `robot_container.py`, swap the import:
   ```python
   # For Kraken:
   from subsystems.turret import Turret

   # For Minion (current):
   from subsystems.turret_minion import TurretMinion as Turret
   ```

3. Tune constants for whichever motor is active. The Minion variant uses `CON_TURRET_MINION` in `constants/shooter.py`, which includes slot0 PID gains for closed-loop position hold and brake mode.

**Why two files instead of a flag?** The TalonFXS needs brake mode and slot0 PID gains passed at construction time, which is different enough from the TalonFX path that a clean separate file is easier to read and debug than conditionals. Both files are short and follow the same pattern.

---

## 2. Subsystem Patterns

Each shooter subsystem follows the standard template from [Hardware & Subsystems](hardware-and-subsystems.md) but demonstrates a different control pattern.

### Turret: Closed-Loop Position Hold + Voltage Manual Control

> **Two variants exist:** `subsystems/turret.py` (Kraken/TalonFX) and `subsystems/turret_minion.py` (Minion/TalonFXS). Both use the same pattern below. See [Turret Motor Swap](#turret-motor-swap-kraken-vs-minion) above for switching instructions.

Both turret variants set a **default command** (`hold_position()`) that uses closed-loop position control to hold the turret steady when no other command is running. When the operator uses manual control (left stick X), that command takes over and drives via voltage. When the stick is released, the default command resumes and holds the turret at its current position.

```python
# subsystems/turret_minion.py -- default command set in __init__
self.setDefaultCommand(self.hold_position())
```

The turret has physical limits it must not exceed. Safety is enforced inside `_set_voltage()` so every caller gets it automatically:

```python
# subsystems/turret_minion.py (key pattern -- includes soft limit ramp)

def _set_voltage(self, volts: float) -> None:
    """Apply voltage with safety clamping, soft limit ramp-down, and hard stop."""
    max_v = CON_TURRET_MINION["max_voltage"]
    clamped = max(-max_v, min(volts, max_v))

    pos = self.get_position()
    # Hard stop -- block voltage that would push past limits
    if pos >= max_pos and clamped > 0:
        clamped = 0
    elif pos <= min_pos and clamped < 0:
        clamped = 0

    # Ramp down voltage when approaching a limit from inside
    if ramp > 0 and clamped != 0:
        if clamped > 0 and pos > max_pos - ramp:
            scale = max(0.5, (max_pos - pos) / ramp)
            clamped *= scale
        elif clamped < 0 and pos < min_pos + ramp:
            scale = max(0.5, (pos - min_pos) / ramp)
            clamped *= scale

    self.motor.set_voltage(clamped)
```

The key insight: soft limits allow the motor to return (negative voltage at max, positive at min) but block pushing further. The **soft limit ramp** (`soft_limit_ramp: 0.5` rotations in `CON_TURRET_MINION`) gradually reduces voltage as the turret approaches a soft limit, so it decelerates smoothly instead of slamming to a sudden stop. The ramp scales voltage down to a minimum of 50% within the ramp zone. The Kraken variant (`turret.py`) has the same hard stop but does not include the ramp feature.

#### TurretMinion manual control: exponential response curve

The Minion variant applies an exponential response curve to joystick input for fine control at small deflections:

```python
exp = CON_TURRET_MINION["manual_exponent"]  # 2.0
speed = abs(raw) ** exp * (1.0 if raw >= 0 else -1.0)
voltage = speed * CON_TURRET_MINION["max_voltage"] * CON_TURRET_MINION["manual_speed_factor"]
```

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

The hood uses `create_motor()` with TalonFXS configuration (brake mode + slot0 PID gains) because the WCP motor connects through a TalonFXS controller. From the subsystem's perspective, the interface is identical.

**Enabled flag:** `CON_HOOD["enabled"]` (default `True`) controls whether the hood motor is initialized. When `False`, the Hood subsystem becomes a safe no-op -- all methods return without touching hardware, `get_position()` returns 0.0, and `is_at_position()` returns `True`. This allows the rest of the shooter system to run without a hood motor connected.

---

## 3. Distance Lookup Table

Instead of a formula, we use a table of measured (distance, launcher_rps, hood_position, ball_speed) tuples. This is easier to tune at competition -- just edit numbers in `constants/shooter.py`.

```python
# constants/shooter.py (current values)
CON_SHOOTER = {
    "distance_table": [
        # (distance_m, launcher_rps, hood_position, ball_speed_mps)
        (1.5, 33.0, 0, 5.0),
        (2.0, 37.0, 0, 7.0),
        (3.0, 47.0, 0, 9.0),
    ],
}
```

The `ball_speed_mps` column is used for velocity compensation -- estimating ball flight time so we can adjust for robot movement. `get_shooter_settings()` returns only `(rps, hood)`.

The lookup function in `subsystems/shooter_lookup.py` linearly interpolates between entries:

```python
# At 1.75m --> halfway between (1.5, 33, 0) and (2.0, 37, 0)
rps, hood = get_shooter_settings(1.75)
# rps = 35.0, hood = 0.0
```

Distances outside the table range clamp to the nearest entry. This prevents extrapolation errors -- if you're closer than 1.5m or farther than 3m, you get the closest known-good settings.

### Tuning at Competition

1. Set up at a known distance from the target
2. Hold **right trigger** to run the launcher, adjust speed with **right stick Y**
3. Record the RPS and hood angle that score
4. Update the distance table in `constants/shooter.py`
5. Repeat at 3-5 distances
6. The interpolation handles everything in between

---

## 4. Command Modules

### CoordinateAim (`commands/coordinate_aim.py`)

Odometry-based turret angle calculation. In teleop, toggled on/off with **left bumper**. In auto, registered as the `AimStart` named command and triggered by PathPlanner event markers. The robot's pose is used to compute the angle to the Hub, then movement compensation, turret routing, EMA filtering, and a PD controller with deadband compensation drive the turret motor. Manual turret override (left stick X) interrupts CoordinateAim via WPILib requirements; it resumes on release.

> **Full deep dive:** [Auto-Aim System](auto-aim.md) -- data flow, pose-based aiming, PD controller math, movement compensation, and debugging guide.

### ShootWhenReady (`commands/shoot_when_ready.py`)

The fully integrated shooter command. In teleop, bound to **left trigger whileTrue** -- hold to engage. In auto, registered as the `ShooterStart` named command and triggered by PathPlanner event markers. Spins up the launcher immediately, then feeds Fuel once the launcher is at speed AND the turret is on target.

Each `execute()` cycle:
1. Call `context_supplier()` to get corrected distance
2. Look up RPS + hood position and command launcher/hood
3. One-time speed gate: once the launcher first reaches target RPS, feeding is unlocked
4. Check `on_target_supplier()` (from CoordinateAim) to decide whether to feed

**Feed debounce:** To prevent feeder stutter when the turret oscillates near the on-target threshold, feeding uses a debounce: it starts instantly when on-target, but requires `feed_off_target_debounce` consecutive off-target cycles before stopping. This is tuned in `CON_SHOOTER` (default 20 cycles = ~400ms at 50Hz). If feeding feels too aggressive or too cautious, adjust that constant.

**Un-jam:** While feeding, if the horizontal feed motor velocity drops near zero (stall detected), the feed reverses briefly to clear a jam, then resumes.

Requires: launcher, hood, h_feed, v_feed.

### ManualShoot (`commands/manual_shoot.py`)

Manual launcher + auto-feed command. Bound to **right trigger whileTrue** -- hold to engage. Spins up the launcher at a fixed speed; once the launcher reaches target RPS, the feeds run automatically.

Requires: launcher, h_feed, v_feed.

### ManualLauncher (`commands/manual_launcher.py`)

Maps the right stick Y axis to a launcher RPS range. Kept as a reference/fallback.

- Stick full forward (1.0) = `CON_MANUAL["launcher_max_rps"]` (100 RPS)
- Stick full back (-1.0) = `CON_MANUAL["launcher_min_rps"]` (40 RPS)
- Stick center (0.0) = midpoint (70 RPS)

---

## 5. How Commands Compose

Each command requires different subsystems, so they can run simultaneously without conflict:

```
commands/
+-- coordinate_aim.py    # Requires: turret           (LB toggle)
+-- shoot_when_ready.py  # Requires: launcher, hood,  (LT hold)
|                        #   h_feed, v_feed
+-- manual_shoot.py      # Requires: launcher,        (RT hold)
|                        #   h_feed, v_feed
+-- reverse_feeds.py     # Requires: h_feed           (RB hold)
+-- manual_launcher.py   # Requires: launcher         (reference/fallback)
```

Currently active bindings:

| Control | Command | Subsystem |
|---------|---------|-----------|
| Left bumper (toggle) | CoordinateAim | turret |
| Left trigger (hold) | ShootWhenReady | launcher, hood, h_feed, v_feed |
| Right trigger (hold) | ManualShoot | launcher, h_feed, v_feed |
| Right bumper (hold) | ReverseFeeds | h_feed |
| Left stick X | Manual turret (via deadband trigger) | turret |

When no operator command is running on the turret, the default command (`hold_position()`) holds the turret steady via closed-loop position control.

| Scenario | What Happens |
|----------|-------------|
| Manual turret stick moved | Stick command takes over turret; default hold_position resumes on release |
| CoordinateAim (LB) + ShootWhenReady (LT) | Both run simultaneously (different subsystem requirements) |
| ReverseFeeds (RB) while ShootWhenReady active | Reverse takes h_feed, interrupts ShootWhenReady. Resume by releasing RB and holding LT again. |

---

**See also:**
- [Auto-Aim System](auto-aim.md) - Auto-aim deep dive: pose-based aiming, PD controller, movement compensation
- [Hardware & Subsystems](hardware-and-subsystems.md) - Subsystem template and TalonFXS support
- [Controls](controls.md) - Full operator control map and override patterns
- [Commands & Controls](commands-and-controls.md) - Command lifecycle and composition
