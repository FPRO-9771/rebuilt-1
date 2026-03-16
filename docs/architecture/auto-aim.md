# Auto-Aim System (Pose-Based)

**Team 9771 FPRO - 2026**

The auto-aim system uses drivetrain odometry to compute the turret angle needed to point at the alliance Hub. Every 20ms cycle, it reads a shared `ShootContext` (pose, shooter field position, target, velocity), calculates the angle from the shooter's actual field position to the Hub, applies movement compensation, routes through soft limits, filters, and feeds a PD controller that drives the turret motor.

> **When to read this:** You are debugging auto-aim behavior, tuning PD gains, or trying to understand why the turret is (or isn't) moving.

---

## Table of Contents

1. [What CoordinateAim Does](#1-what-coordinateaim-does)
2. [ShootContext Shared Supplier](#2-shootcontext-shared-supplier)
3. [Data Flow (One Cycle)](#3-data-flow-one-cycle)
4. [Target State Calculation](#4-target-state-calculation)
5. [Movement Compensation](#5-movement-compensation)
6. [Turret Routing](#6-turret-routing)
7. [EMA Filter](#7-ema-filter)
8. [PD Controller](#8-pd-controller)
9. [Turret States](#9-turret-states)
10. [Constants Reference](#10-constants-reference)
11. [File Map](#11-file-map)
12. [Debugging Guide](#12-debugging-guide)
13. [Common Failure Modes](#13-common-failure-modes)

---

## 1. What CoordinateAim Does

CoordinateAim is a WPILib `Command` toggled on/off with the **Y button**. While active, every 20ms cycle it:

1. Reads the shared `ShootContext` (pose, shooter field position, target, velocity)
2. Computes the angle and distance from the shooter to the alliance Hub
3. Applies movement compensation (tracking + lead corrections)
4. Routes the desired turret angle through soft limits (shortest path)
5. Filters the error through an EMA
6. Computes a voltage via PD + feedforward control
7. Sends that voltage to the turret motor

CoordinateAim only controls the **turret**. It does NOT set flywheel speed, hood angle, or lock status -- those are AutoShoot's job. Both commands run simultaneously because they require different subsystems.

Because the system uses odometry instead of AprilTags, there is no "Lost" state -- we always have a pose, so we always know where the Hub is. The turret is either actively driving toward the target or holding still because it is already on target.

---

## 2. ShootContext Shared Supplier

All three shooter commands (CoordinateAim, AutoShoot, ShootWhenReady) consume a shared `ShootContext` namedtuple from a single supplier built in `controls/operator_controls.py`. This eliminates duplicated pose/distance math -- every command sees the same shooter position, target, and velocity data.

### ShootContext fields

`ShootContext` is defined in `calculations/target_state.py`:

| Field | Type | Description |
|-------|------|-------------|
| `corrected_distance` | float | Velocity-adjusted distance for lookup table (meters) |
| `raw_distance` | float | Raw shooter-to-target distance (meters) |
| `closing_speed_mps` | float | Rate of closure (positive = closing) |
| `pose_x`, `pose_y` | float | Robot position (meters) |
| `heading_deg` | float | Robot heading (degrees) |
| `shooter_x`, `shooter_y` | float | Shooter field position (meters) |
| `target_x`, `target_y` | float | Hub position (meters) |
| `vx`, `vy` | float | Robot velocity (m/s) |

### How the supplier works

The supplier `_make_shoot_context_supplier()` in `controls/operator_controls.py` is the single place that runs the pose-to-distance pipeline:

1. Read robot pose from drivetrain odometry
2. Convert robot-relative shooter offset to field coordinates via `get_shooter_field_position()` (the shooter is not at robot center)
3. Get the alliance Hub target position
4. Get robot velocity from drivetrain state
5. Compute raw distance and closing speed via `compute_range_state()`
6. Compute velocity-corrected distance via `compute_corrected_distance()`
7. Package everything into a `ShootContext`

The supplier is created once during `configure_operator()` and passed to all three commands. Each command calls `context_supplier()` every cycle to get fresh data.

### Shooter position offset

The shooter is not at the robot center -- it is offset (6" back, 8" right, configured in `constants/pose.py`). Because the robot rotates, this offset points in a different field direction each cycle. `calculations/shooter_position.py` handles the rotation math. All distance and angle calculations measure from the actual shooter position, not robot center.

### Distance compensation

`calculations/distance_compensation.py` adjusts the lookup distance based on closing speed. When the robot is driving toward the Hub, the ball needs less energy because the target will be closer by the time the ball arrives. When retreating, it needs more. The correction uses ball flight time from the distance table to estimate the effective distance.

---

## 3. Data Flow (One Cycle)

```
ShootContext (from shared supplier)
  pose, shooter_xy, target_xy, velocity, corrected_distance
       |
       v
  compute_target_state()              target_state.py
       |                              takes scalars -- no WPILib objects
       +-- error_deg                  "turret needs to rotate 12.3 deg right"
       +-- distance_m                 "Hub is 4.2 meters away"
       +-- closing_speed              "we are approaching at 1.1 m/s"
       |
       v
  movement_compensation()             movement_compensation.py
       |
       +-- tracking correction        compensate for robot rotation
       +-- lead correction            compensate for ball flight time
       |
       v
  compensated error (degrees)
       |
       v
  choose_rotation_direction()         turret_routing.py
       |                              picks shortest path within soft limits
       v
  routed error (degrees)
       |
       v
  EMA filter                          smooths cycle-to-cycle noise
       |
       v
  filtered_error                      this is what the PD controller sees
       |
  +----+----+----+
  |         |    |
  v         v    v
 P term   D term  FF term             sqrt-P, velocity damping, lateral FF
  |         |    |
  +----+----+----+
       |
       v
  raw voltage
       |
       v
  clamp (asymmetric)                  different limits for driving vs braking
       |
       v
  deadband comp                       bumps tiny voltages past static friction
       |
       v
  turret._set_voltage()               soft limits enforced inside turret subsystem
```

---

## 4. Target State Calculation

`calculations/target_state.py` contains two functions:

### `compute_target_state()` -- turret error, distance, closing speed

Takes scalar inputs -- no WPILib Pose2d needed. This makes it pure math with no framework dependencies, easy to unit test.

**Arguments:** `heading_deg`, `shooter_xy` (tuple), `target_xy` (tuple), `velocity_xy` (tuple), plus turret position info.

**Returns:** `TargetState` namedtuple with `error_deg`, `distance_m`, `closing_speed_mps`, `bearing_deg`.

CoordinateAim reads `shooter_xy` and `target_xy` from the ShootContext and passes them as tuples.

### Error (degrees)

The angle between where the turret is currently pointing and where it needs to point to face the Hub. This is the primary input to the PD controller.

```
1. Read shooter_xy and target_xy from ShootContext
2. Compute desired global heading = atan2(hub_y - shooter_y, hub_x - shooter_x)
3. Subtract robot heading and current turret angle
4. Result = error in degrees
```

### `compute_range_state()` -- distance and closing speed only

A lighter function that skips the turret angle calculation. Used by the shared context supplier to compute raw distance and closing speed for the ShootContext. AutoShoot uses the ShootContext's `corrected_distance` (which includes velocity compensation) for lookup table queries.

### Distance (meters)

Straight-line distance from the shooter (not robot center) to the Hub. The ShootContext provides both `raw_distance` and `corrected_distance` (adjusted for closing speed via `compute_corrected_distance()`).

### Closing speed (m/s)

How fast the robot is approaching or receding from the Hub. Positive = approaching, negative = moving away. Used to adjust the lookup distance -- if closing, the ball needs less energy because the target will be closer by the time the ball arrives.

---

## 5. Movement Compensation

`calculations/movement_compensation.py` applies two corrections to the raw error:

### Tracking correction

When the robot is rotating, the turret needs to counter-rotate to stay on target. This correction uses the robot's angular velocity (from the gyro) to anticipate how much the robot will rotate during the next control cycle.

### Lead correction (velocity lead)

When the robot is strafing, the ball inherits the robot's lateral velocity. If the turret aims directly at the Hub, the ball will miss to the side.

The lead correction:
1. Looks up ball speed at the current distance (from the distance table)
2. Computes flight time = distance / ball_speed
3. Computes lead distance = lateral velocity * flight time
4. Computes lead angle = atan2(lead_distance, distance)

The correction aims the turret **ahead** of the Hub so the ball curves into it.

**Config:** `CON_SHOOTER["velocity_lead_enabled"]` (bool). Feature-flagged and disabled by default until tuned on the real robot.

---

## 6. Turret Routing

`calculations/turret_routing.py` contains `choose_rotation_direction()`, which determines which way the turret should rotate to reach the target angle.

The turret has soft limits (e.g., -0.5 to +0.5 rotations). The routing logic:

1. Computes the shortest angular path to the target (clockwise vs counter-clockwise)
2. Checks if that path stays within soft limits
3. If the shortest path would hit a limit, takes the longer path instead
4. Returns the signed error for the PD controller

This prevents the turret from trying to spin through a hard stop when going the other way would work.

---

## 7. EMA Filter

After routing, the error passes through an exponential moving average:

```
filtered_error = alpha * routed_error + (1 - alpha) * previous_filtered_error
```

`alpha` = `turret_tx_filter_alpha` (default 0.85). Higher alpha = less smoothing, faster response. Lower alpha = more smoothing, slower response.

The filter uses the `auto_aim_` naming convention in telemetry keys for consistency with dashboard layouts.

---

## 8. PD Controller

The PD controller lives in `calculations/turret_pd.py`. It converts filtered_error into a motor voltage. This module is unchanged from the previous system.

### P term (sqrt compression)

```python
p_term = sqrt(|filtered_error|) * sign(filtered_error) * turret_p_gain
```

Why sqrt? A linear P gain would saturate at the voltage clamp for large errors, making the turret slam to max speed regardless of distance. Sqrt compresses large errors so the turret ramps gradually and decelerates as it approaches the target.

### D term (velocity damping)

```python
d_term = -turret_velocity * turret_d_velocity_gain
```

This damps the turret's actual velocity (not the error derivative). It acts as a brake -- the faster the turret is spinning, the more it resists. This prevents overshoot. Too high and it causes sluggish response or oscillation; the current value (0.03) is intentionally light.

### Feedforward (lateral velocity)

```python
ff_term = vy * turret_velocity_ff_gain * aim_sign
```

Pre-compensates for robot lateral movement. If the robot is strafing right, the turret needs to spin left to keep tracking. This term handles the "constant offset" part; the lead correction in movement compensation handles the ballistic part.

### Voltage = P + D + FF

```python
raw_voltage = p_term * aim_sign + d_term + ff_term
```

`aim_sign` is +1 or -1 depending on `turret_aim_inverted`. It flips the P term direction if the turret's wiring runs opposite to the expected convention.

### Asymmetric clamping

```
driving:  |voltage| <= turret_max_auto_voltage  (0.50V)
braking:  |voltage| <= turret_max_brake_voltage (0.50V)
```

"Braking" = voltage opposes current turret direction. This allows the turret to stop faster than it accelerates, reducing overshoot.

### Deadband compensation

If the turret is nearly stopped (`|velocity| < 0.05`) and the computed voltage is nonzero but below `turret_min_move_voltage` (0.35V), the voltage is bumped up to that minimum. This overcomes static friction so the turret actually starts moving on small corrections instead of sitting stuck.

---

## 9. Turret States

Each cycle, CoordinateAim is in exactly one of two states:

| State | Condition | Motor Output | When |
|-------|-----------|-------------|------|
| **Hold** | `|filtered_error| <= tolerance` | 0V (hold) | On target -- don't chase noise |
| **Drive** | Otherwise | PD voltage | Actively aiming |

There is no "Lost" state. Because the system uses odometry, we always have a pose and always know where the Hub is. If odometry drifts, the turret will aim at the wrong spot, but it will never stop aiming entirely.

The **Hold** state is critical for preventing oscillation. Without it, the deadband compensation would keep nudging the turret back and forth across the zero point.

The tolerance is `turret_alignment_tolerance` (default 1.5 degrees).

---

## 10. Constants Reference

Auto-aim tuning constants live in three files:

### `constants/shooter.py` -- PD gains and voltage limits (`CON_SHOOTER`)

| Constant | Default | What It Does |
|----------|---------|--------------|
| `turret_p_gain` | 0.08 | P gain (volts per sqrt-degree) -- higher = more aggressive aim |
| `turret_d_velocity_gain` | 0.03 | Velocity damping -- higher = more braking, risk of oscillation |
| `turret_aim_inverted` | False | Flip turret direction vs error convention |
| `turret_alignment_tolerance` | 1.5 | Degrees of error within which turret holds still |
| `turret_max_auto_voltage` | 0.50 | Max driving voltage during auto-aim |
| `turret_max_brake_voltage` | 0.50 | Max braking voltage (opposing turret direction) |
| `turret_min_move_voltage` | 0.35 | Deadband compensation -- minimum voltage to overcome static friction |
| `turret_velocity_ff_gain` | 0.15 | Feedforward gain for lateral robot velocity |
| `turret_tx_filter_alpha` | 0.85 | EMA smoothing (0 = max smooth, 1 = no filter) |
| `velocity_lead_enabled` | False | Enable aim-ahead compensation while strafing |

### `constants/match.py` -- Hub positions

| Constant | What It Does |
|----------|--------------|
| Hub position (per-alliance) | (x, y) field coordinates of the Red and Blue Hubs |

### `constants/pose.py` -- Turret geometry and shooter position

| Constant | What It Does |
|----------|--------------|
| `center_position` | Motor rotations when turret faces forward (robot heading) |
| `degrees_per_rotation` | Turret degrees per motor rotation (360 / gear ratio) |
| `shooter_offset_x` | Forward offset of shooter from robot center (meters, +X = forward) |
| `shooter_offset_y` | Left offset of shooter from robot center (meters, +Y = left) |

---

## 11. File Map

```
calculations/
  target_state.py                # ShootContext namedtuple, compute_target_state(),
                                 #   compute_range_state() -- all scalar math
  shooter_position.py            # get_shooter_field_position() -- robot offset to field coords
  distance_compensation.py       # compute_corrected_distance() -- closing speed adjustment
  movement_compensation.py       # Tracking + lead corrections
  turret_routing.py              # Shortest path within soft limits
  turret_pd.py                   # PD + FF + deadband voltage calculation

commands/
  coordinate_aim.py              # Turret aiming command -- reads ShootContext
  auto_shoot.py                  # Launcher/hood from distance -- reads ShootContext
  shoot_when_ready.py            # Auto-shoot + auto-feed -- reads ShootContext

controls/
  operator_controls.py           # _make_shoot_context_supplier() -- builds the shared supplier

constants/
  shooter.py                     # CON_SHOOTER: PD gains, voltage limits, feature flags
  match.py                       # Per-alliance Hub positions
  pose.py                        # Turret geometry + shooter_offset_x/y

telemetry/
  auto_aim_telemetry.py          # SmartDashboard publishing (on-target, error, distance)
  auto_aim_logging.py            # Structured console logging (hold/drive/shoot states)

tests/
  test_coordinate_aim.py         # Command behavior tests (aiming, routing, compensation)
```

---

## 12. Debugging Guide

### Debug flags in `constants/debug.py`

| Flag | Default | What It Controls |
|------|---------|-----------------|
| `auto_aim_logging` | True | Console logs for aim and shoot pipeline (independent of `verbose`) |
| `auto_aim_dashboard` | True | SmartDashboard aim geometry keys (`AimDash/`) |
| `debug_telemetry` | True | Extra SmartDashboard keys (vx, vy, lead, closing speed) |
| `verbose` | True | Global DEBUG-level logging (also enables auto-aim logs) |

### SmartDashboard keys published by CoordinateAim

| Key | Type | Match-critical? | Meaning |
|-----|------|-----------------|---------|
| `AutoAim/OnTarget` | boolean | Yes | True when turret is aimed at Hub (within tolerance) |
| `AutoAim/ErrorDeg` | number | Yes | Current error in degrees (+ = need to rotate right) |
| `AutoAim/DistanceM` | number | Yes | Distance to Hub in meters |
| `AutoAim/vx` | number | Debug only | Robot vx |
| `AutoAim/vy` | number | Debug only | Robot vy |
| `AutoAim/LeadDeg` | number | Debug only | Velocity lead correction in degrees |
| `AutoAim/ClosingSpeed` | number | Debug only | Closing speed to Hub in m/s |

Debug-only keys require `DEBUG["debug_telemetry"] = True` in `constants/debug.py`.

### Aim geometry dashboard (`AimDash/`)

| Key | Type | Description |
|-----|------|-------------|
| `AimDash/ShooterToHubM` | number | Distance from shooter (with offset) to Hub in meters |
| `AimDash/BearingToHubDeg` | number | Angle from robot front to Hub in degrees (+ = left) |

These keys are toggled with `DEBUG["auto_aim_dashboard"]` in `constants/debug.py` and update at ~2 Hz. They show the "next iteration" geometry -- the computed distance and bearing that the aiming system uses -- so the team can verify pose estimation and aiming are working correctly.

The `AutoAim/` prefix is kept for consistency with dashboard layouts and logging, even though the command is now called CoordinateAim.

### Console log format

Auto-aim logs are controlled by `DEBUG["auto_aim_logging"]` in `constants/debug.py` (independent of `DEBUG["verbose"]`). Three log functions in `telemetry/auto_aim_logging.py`:

- **`log_hold()`** -- `[AIM HOLD] pose=(X,Y) hdg=H shooter=(X,Y) tgt=(X,Y) err=E dist=D cls=C -- HOLD` -- on target, turret holding
- **`log_drive()`** -- `[AIM DRIVE] pose=(X,Y) ... | err=E ... | P=p D=d FF=f rv=r v=V [ok/SAT] ...` -- full PD output with all terms
- **`log_shoot()`** -- `[SHOOT] pose=(X,Y) ... | rawDist=R corrDist=C ... | rps=R hood=H | AT_SPEED ON_TARGET FEEDING` -- auto-shoot pipeline

All three show full pose context (robot pose, shooter field position, target position, velocity).

**Interleaved logging:** Aim logs (`log_hold`, `log_drive`) fire on even cycles. Shoot logs (`log_shoot`) fire on odd cycles. This keeps the console readable -- you see aim and shoot data alternating instead of doubled up.

### What to look at first

1. **Is CoordinateAim even active?** Check `AutoAim/OnTarget` on SmartDashboard (if the key exists, the command is running)
2. **Is the error reasonable?** Check `AutoAim/ErrorDeg` -- if it is very large (>90 deg), odometry may have drifted or the wrong alliance Hub is selected
3. **Is it stuck in HOLD when it shouldn't be?** The filtered error might be within tolerance but the turret is not actually aimed right. This usually means odometry has drifted. Check if `turret_alignment_tolerance` is too wide
4. **Is it oscillating?** Usually means D gain is too high, or deadband comp is fighting the hold state. Check if filtered error is bouncing across the tolerance boundary
5. **Is it sluggish?** P gain too low, or max voltage too low, or EMA alpha too low (over-smoothing)

---

### Shooter position mismatch

If the turret aims correctly when the robot is near the Hub but misses at long range, the shooter offset in `constants/pose.py` may be wrong. At close range the offset matters less because the angle difference is small. At far range a bad offset shifts the aim point.

---

## 13. Common Failure Modes

### Turret does not move at all
- CoordinateAim not toggled on (Y button)
- Turret at soft limit and voltage would push further past it (check turret position vs limits in CON_TURRET)
- `turret_max_auto_voltage` set too low to overcome friction (below `turret_min_move_voltage`)

### Turret oscillates back and forth
- `turret_d_velocity_gain` too high -- damps so hard it bounces
- `turret_alignment_tolerance` too tight -- never reaches hold state, deadband comp keeps kicking in
- `turret_tx_filter_alpha` too high (close to 1.0) -- noisy error passes through unsmoothed

### Turret aims at wrong spot
- Wrong alliance selected (check Hub positions in constants/match.py -- Red and Blue Hubs are at different field coordinates)
- Odometry has drifted -- the robot thinks it is somewhere it is not. Reset pose or verify with a known field position
- `turret_aim_inverted` wrong -- turret moves away from target instead of toward it
- Turret zero heading in constants/pose.py does not match the physical turret orientation
- Shooter offset (`shooter_offset_x`, `shooter_offset_y` in constants/pose.py) is wrong -- more visible at long range
- Velocity lead enabled but ball speeds in distance table are wrong

### Turret moves right direction but overshoots
- `turret_p_gain` too high -- try reducing
- `turret_d_velocity_gain` too low -- not enough braking
- `turret_max_brake_voltage` too low -- cannot stop fast enough

### Turret takes the long way around
- Turret routing is choosing the wrong direction. Check if the soft limits in CON_TURRET are correct
- If the turret is near a soft limit, routing may intentionally go the long way to avoid hitting it

### Odometry drift causes gradual aim error
- This is expected over time. Odometry drifts, especially during collisions or wheel slip
- Vision-based pose resets (if available) can correct this periodically
- Watch `AutoAim/ErrorDeg` -- if it grows over time without the robot moving, odometry is the likely cause

---

**See also:**
- [Shooter System](shooter-system.md) -- Turret/launcher/hood subsystems and how commands compose
- [Controls](controls.md) -- Y button binding and manual turret override
- [Telemetry](telemetry.md) -- Dashboard setup and published keys
- [Drivetrain](drivetrain.md) -- Odometry source for pose-based aiming
