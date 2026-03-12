# Auto-Aim System

**Team 9771 FPRO - 2026**

The auto-aim system uses PD control to point the turret at the alliance Hub by tracking AprilTags with the Limelight camera. It is the most complex single command in the codebase: vision data flows through three correction stages, an EMA filter, and a PD controller with deadband compensation before reaching the turret motor.

> **When to read this:** You are debugging auto-aim behavior, tuning PD gains, or trying to understand why the turret is (or isn't) moving.

---

## Table of Contents

1. [What AutoAim Does](#1-what-autoaim-does)
2. [Data Flow (One Cycle)](#2-data-flow-one-cycle)
3. [Target Selection and Stickiness](#3-target-selection-and-stickiness)
4. [Correction Pipeline](#4-correction-pipeline)
5. [PD Controller](#5-pd-controller)
6. [Turret States](#6-turret-states)
7. [Constants Reference](#7-constants-reference)
8. [File Map](#8-file-map)
9. [Debugging Guide](#9-debugging-guide)
10. [Common Failure Modes](#10-common-failure-modes)

---

## 1. What AutoAim Does

AutoAim is a WPILib `Command` toggled on/off with the **Y button**. While active, every 20ms cycle it:

1. Picks an AprilTag to track (using the alliance's priority list)
2. Reads tx (horizontal offset in degrees) from the Limelight
3. Applies corrections (parallax, velocity lead) and smoothing (EMA filter)
4. Computes a voltage via PD + feedforward control
5. Sends that voltage to the turret motor

AutoAim only controls the **turret**. It does NOT set flywheel speed, hood angle, or lock status -- those are AutoShoot's job. Both commands run simultaneously because they require different subsystems.

---

## 2. Data Flow (One Cycle)

```
Limelight camera
       |
       v
  VisionProvider.get_target(tag_id)
       |
       v
  raw tx (degrees)              "target is 5.2 degrees right"
       |
  +----+----+
  |         |
  v         v
parallax  velocity lead         optional corrections (feature-flagged)
  |         |
  +----+----+
       |
       v
  corrected tx                  raw tx + parallax + lead
       |
       v
  EMA filter                    smooths noisy Limelight readings
       |
       v
  filtered_tx                   this is what the PD controller sees
       |
  +----+----+----+
  |         |    |
  v         v    v
 P term   D term  FF term       sqrt-P, velocity damping, lateral FF
  |         |    |
  +----+----+----+
       |
       v
  raw voltage
       |
       v
  clamp (asymmetric)            different limits for driving vs braking
       |
       v
  deadband comp                 bumps tiny voltages past static friction
       |
       v
  turret._set_voltage()         soft limits enforced inside turret subsystem
```

---

## 3. Target Selection and Stickiness

### Priority list

Each alliance defines an ordered list of AprilTag IDs in `constants/match.py`. AutoAim scans the list and locks onto the **first visible tag**.

```
Red:  [8, 10, 11]
Blue: [25, 26, 24, 27]
```

The priority list is supplied via `tag_priority_supplier` (a callable), so it updates live when the operator switches alliance on SmartDashboard.

### Stickiness (lock retention)

Once locked on a tag, the system does NOT immediately switch to a higher-priority tag that becomes visible. It stays on the locked tag until:

- The locked tag disappears for **TARGET_LOCK_LOST_CYCLES** consecutive cycles (default 10 = 200ms at 50Hz)
- Only then does it fall back to the priority scan

During a brief dropout (< 10 cycles), AutoAim coasts on the last known filtered_tx. This prevents jitter when the Limelight briefly loses a tag (common during motion or at frame edges).

### Lock lifecycle

```
No lock --> tag visible in priority scan --> LOCKED
LOCKED  --> tag visible                  --> reset lost_count, stay LOCKED
LOCKED  --> tag not visible              --> increment lost_count
LOCKED  --> lost_count >= 10             --> UNLOCKED, rescan priority list
LOCKED  --> lost_count < 10              --> coast on last filtered_tx
```

---

## 4. Correction Pipeline

All corrections are **additive** -- they shift tx without replacing or interfering with each other. Both are **feature-flagged** and disabled by default until tuned on the real robot.

### 4a. Parallax Correction

**Problem:** AprilTags are not at Hub center. They are offset toward the driver station wall and sometimes laterally. When the robot views a tag from an angle, "aimed at the tag" != "aimed at the Hub".

**Solution:** `calculations/parallax.py` computes the angular difference between pointing at the tag and pointing at Hub center, given:
- `tx_deg`: raw tx from Limelight
- `distance`: distance to tag
- `tag_y_offset_m`: how far the tag is from Hub center forward/back (always negative -- tags are closer to the wall)
- `tag_x_offset_m`: how far the tag is left/right of Hub center

The correction is larger when the robot is close and viewing at an angle. At long range it shrinks toward zero.

**Config:** `CON_SHOOTER["parallax_correction_enabled"]` (bool). Tag offsets are per-alliance in `constants/match.py`.

### 4b. Velocity Lead

**Problem:** When the robot is strafing, the ball inherits the robot's lateral velocity. If the turret aims directly at the Hub, the ball will miss to the side.

**Solution:** `calculations/velocity_lead.py` computes a lead angle:
1. Look up ball speed at current distance (from the distance table)
2. Compute flight time = distance / ball_speed
3. Lead distance = lateral velocity * flight time
4. Lead angle = atan2(lead_distance, distance)

The correction aims the turret **ahead** of the Hub so the ball curves into it.

**Config:** `CON_SHOOTER["velocity_lead_enabled"]` (bool). Requires a `robot_velocity_supplier` to be wired in.

### 4c. EMA Filter

After corrections, the tx value passes through an exponential moving average:

```
filtered_tx = alpha * corrected_tx + (1 - alpha) * previous_filtered_tx
```

`alpha` = `turret_tx_filter_alpha` (default 0.85). Higher alpha = less smoothing, faster response. Lower alpha = more smoothing, slower response.

When a new tag is first locked, filtered_tx is **seeded** to the raw tx to avoid a spike from a stale value.

---

## 5. PD Controller

The PD controller lives in `calculations/turret_pd.py`. It converts filtered_tx into a motor voltage.

### P term (sqrt compression)

```python
p_term = sqrt(|filtered_tx|) * sign(filtered_tx) * turret_p_gain
```

Why sqrt? A linear P gain would saturate at the voltage clamp for large errors, making the turret slam to max speed regardless of distance. Sqrt compresses large errors so the turret ramps gradually and decelerates as it approaches the target.

### D term (velocity damping)

```python
d_term = -turret_velocity * turret_d_velocity_gain
```

This damps the turret's actual velocity (not the tx derivative). It acts as a brake -- the faster the turret is spinning, the more it resists. This prevents overshoot. Too high and it causes sluggish response or oscillation; the current value (0.03) is intentionally light.

### Feedforward (lateral velocity)

```python
ff_term = vy * turret_velocity_ff_gain * aim_sign
```

Pre-compensates for robot lateral movement. If the robot is strafing right, the turret needs to spin left to keep tracking. This term handles the "constant offset" part; velocity lead handles the ballistic part.

### Voltage = P + D + FF

```python
raw_voltage = p_term * aim_sign + d_term + ff_term
```

`aim_sign` is +1 or -1 depending on `turret_aim_inverted`. It flips the P term direction if the turret's wiring runs opposite to the Limelight's tx convention.

### Asymmetric clamping

```
driving:  |voltage| <= turret_max_auto_voltage  (0.50V)
braking:  |voltage| <= turret_max_brake_voltage (0.50V)
```

"Braking" = voltage opposes current turret direction. This allows the turret to stop faster than it accelerates, reducing overshoot.

### Deadband compensation

If the turret is nearly stopped (`|velocity| < 0.05`) and the computed voltage is nonzero but below `turret_min_move_voltage` (0.35V), the voltage is bumped up to that minimum. This overcomes static friction so the turret actually starts moving on small corrections instead of sitting stuck.

---

## 6. Turret States

Each cycle, AutoAim is in exactly one of three states:

| State | Condition | Motor Output | When |
|-------|-----------|-------------|------|
| **Lost** | No locked tag and no target | 0V (stop) | No tags visible for > 200ms |
| **Hold** | `|filtered_tx| <= tolerance` | 0V (hold) | On target -- don't chase noise |
| **Drive** | Otherwise | PD voltage | Actively aiming |

The **Hold** state is critical for preventing oscillation. Without it, the deadband compensation would keep nudging the turret back and forth across the zero point.

The tolerance is `turret_alignment_tolerance` (default 1.5 degrees).

---

## 7. Constants Reference

All auto-aim tuning constants live in `constants/shooter.py` under `CON_SHOOTER`:

| Constant | Default | What It Does |
|----------|---------|--------------|
| `turret_p_gain` | 0.08 | P gain (volts per sqrt-degree) -- higher = more aggressive aim |
| `turret_d_velocity_gain` | 0.03 | Velocity damping -- higher = more braking, risk of oscillation |
| `turret_aim_inverted` | False | Flip turret direction vs tx convention |
| `turret_alignment_tolerance` | 1.5 | Degrees of tx within which turret holds still |
| `turret_max_auto_voltage` | 0.50 | Max driving voltage during auto-aim |
| `turret_max_brake_voltage` | 0.50 | Max braking voltage (opposing turret direction) |
| `turret_min_move_voltage` | 0.35 | Deadband compensation -- minimum voltage to overcome static friction |
| `turret_velocity_ff_gain` | 0.15 | Feedforward gain for lateral robot velocity |
| `turret_tx_filter_alpha` | 0.85 | EMA smoothing (0 = max smooth, 1 = no filter) |
| `velocity_lead_enabled` | False | Enable aim-ahead compensation while strafing |
| `parallax_correction_enabled` | False | Enable parallax correction (tag-to-Hub angle shift) |

Related constants in `constants/match.py`:

| Constant | Default | What It Does |
|----------|---------|--------------|
| `TARGET_LOCK_LOST_CYCLES` | 10 | Cycles before unlocking a lost tag (10 = 200ms) |
| `tag_priority` | per-alliance | Ordered list of tag IDs to track |
| `tag_offsets` | per-alliance | Per-tag parallax offsets (y and x in meters) |

---

## 8. File Map

```
commands/
  auto_aim.py                  # The command itself -- lifecycle + state machine

calculations/
  turret_pd.py                 # PD + FF + deadband voltage calculation
  velocity_lead.py             # Lateral velocity lead angle
  parallax.py                  # Tag-to-Hub parallax angle correction

constants/
  shooter.py                   # CON_SHOOTER: PD gains, voltage limits, feature flags
  match.py                     # Per-alliance tag priorities and parallax offsets

telemetry/
  auto_aim_telemetry.py        # SmartDashboard publishing (lock status, visible tags)
  auto_aim_logging.py          # Structured console logging (lost/hold/drive states)

tests/
  test_auto_aim.py             # Command behavior tests (aiming, stickiness, corrections)
  test_parallax.py             # Pure math tests for parallax correction
```

---

## 9. Debugging Guide

### SmartDashboard keys published by AutoAim

| Key | Type | Meaning |
|-----|------|---------|
| `Shooter/AutoAim` | boolean | True when AutoAim command is active |
| `Shooter/AutoAim/HasTarget` | boolean | True when a tag is locked |
| `Shooter/AutoAim/LockedTag` | number | Tag ID being tracked (-1 = none) |
| `Shooter/AutoAim/Priority` | string | Current priority list (debug only) |
| `Shooter/AutoAim/Visible` | string | Visible tag IDs (debug only) |
| `Shooter/AutoAim/vx` | number | Robot vx (debug only) |
| `Shooter/AutoAim/vy` | number | Robot vy (debug only) |
| `Shooter/AutoAim/LeadDeg` | number | Velocity lead correction (debug only) |

Debug-only keys require `DEBUG["debug_telemetry"] = True` in `constants/debug.py`.

### Console log format

Auto-aim logs are controlled by `DEBUG["auto_aim_logging"]` in `constants/debug.py`. Three log patterns:

- **LOST** -- `cycle=N pos=X.XX` -- no target locked, turret stopped
- **HOLD** -- `cycle=N tag=ID ftx=X.XX pos=X.XX` -- on target, turret holding
- **DRIVE** -- `cycle=N tag=ID tx=X.XX ftx=X.XX P=X.XX D=X.XX FF=X.XX raw=X.XX V=X.XX vel=X.XX pos=X.XX ...` -- full PD output with all terms

### What to look at first

1. **Is AutoAim even active?** Check `Shooter/AutoAim` on SmartDashboard
2. **Is a tag visible?** Check `Shooter/AutoAim/HasTarget` and `Shooter/AutoAim/LockedTag`
3. **Is it stuck in HOLD when it shouldn't be?** filtered_tx might be within tolerance but the turret isn't actually aimed right. Check if `turret_alignment_tolerance` is too wide
4. **Is it oscillating?** Usually means D gain is too high, or deadband comp is fighting the hold state. Check if filtered_tx is bouncing across the tolerance boundary
5. **Is it sluggish?** P gain too low, or max voltage too low, or EMA alpha too low (over-smoothing)

---

## 10. Common Failure Modes

### Turret doesn't move at all
- AutoAim not toggled on (Y button)
- No tags visible (wrong pipeline, Limelight unplugged, tags not in priority list)
- Turret at soft limit and voltage would push further past it (check turret position vs limits in CON_TURRET)
- `turret_max_auto_voltage` set too low to overcome friction (below `turret_min_move_voltage`)

### Turret oscillates back and forth
- `turret_d_velocity_gain` too high -- damps so hard it bounces
- `turret_alignment_tolerance` too tight -- never reaches hold state, deadband comp keeps kicking in
- `turret_tx_filter_alpha` too high (close to 1.0) -- noisy tx passes through unsmoothed
- Limelight tx jumping between two tags (stickiness should prevent this, but check if TARGET_LOCK_LOST_CYCLES is too low)

### Turret aims at wrong spot
- Wrong alliance selected (check tag_priority -- Red and Blue tags are different)
- Parallax correction enabled but offsets not measured on real field (currently placeholder values)
- `turret_aim_inverted` wrong -- turret moves away from target instead of toward it
- Velocity lead enabled but ball speeds in distance table are wrong

### Turret moves right direction but overshoots
- `turret_p_gain` too high -- try reducing
- `turret_d_velocity_gain` too low -- not enough braking
- `turret_max_brake_voltage` too low -- can't stop fast enough

### Turret tracks but then suddenly jumps
- Tag lock lost, system switched to different tag with different tx
- `TARGET_LOCK_LOST_CYCLES` too low -- increase for more stickiness
- EMA filter not seeded on new lock (this is handled in `_select_target`, but verify `_filtered_tx = target.tx` runs)

---

**See also:**
- [Shooter System](shooter-system.md) - Turret/launcher/hood subsystems and how commands compose
- [Vision](vision.md) - How the Limelight provides tx and distance
- [Controls](controls.md) - Y button binding and manual turret override
- [Telemetry](telemetry.md) - Dashboard setup and published keys
