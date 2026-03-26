# Movement Compensation Tuning Guide

**Team 9771 FPRO - 2026**

Step-by-step guide for tuning the shooter to hit targets while the robot is moving. Follow the steps in order -- each one builds on the previous.

> **Before you start:** Static shooting must already work. If you can not score while stationary, fix that first (see the auto-aim docs). This guide only covers the movement part.

---

## How It Works (2-Minute Version)

When the robot is moving and shooting, two things go wrong:

1. **Lateral movement** -- the ball inherits the robot's sideways speed, so it misses left/right
2. **Approach/retreat** -- the distance is changing while the ball is in the air, so it misses short/long

Two compensation modules fix this. Each one takes inputs, does math, and produces **one output**:

| Module | What it fixes | Output | Key constant |
|--------|--------------|--------|-------------|
| **Angle compensation** | Lateral miss (left/right) | Lead angle (degrees) added to turret aim | `flight_time_s` in distance table + `velocity_lead_gain` |
| **Distance compensation** | Range miss (short/long) | Corrected distance (meters) for launcher lookup | `flight_time_s` in distance table |

Both modules depend on the same thing: **how long is the ball in the air?** That is `flight_time_s` in the distance table. Everything starts there.

### Constants files

| File | What is in it |
|------|--------------|
| `constants/compensation.py` | `velocity_lead_enabled`, `velocity_lead_gain`, `min_distance` |
| `constants/shooter.py` (distance table) | `flight_time_s` per distance entry |

---

## What You Need

- The robot, a Hub target, and open floor space (at least 4m x 4m)
- Fuel (at least 10 balls)
- A laptop connected to the robot (for SmartDashboard or SSH logs)
- A tape measure
- **A stopwatch or phone timer** (for measuring flight time)
- Someone to feed balls and someone to drive
- This guide printed out or on a phone

---

## Step 1: Turn On Compensation Logging

Before tuning, enable the debug log so you can see what the compensation is doing.

In `constants/debug.py`, set:

```python
"compensation_logging": True,
```

This prints a `[COMP]` log line every ~200ms showing the full pipeline:

```
[COMP] vel=(0.50,1.20) dist=3.00 bearing=45.0 cls=0.50
  | v_tan=0.85 flightT=0.330 leadM=0.280 leadDeg=5.35 gain=1.00 finalLead=5.35
  | rawDist=3.00 corrDist=2.84
```

**How to read it:**

| Field | What it means |
|-------|--------------|
| `vel=(vx,vy)` | Robot velocity (m/s) |
| `dist` | Straight-line distance to Hub (meters) |
| `bearing` | Angle to Hub (degrees) |
| `cls` | Closing speed (positive = getting closer) |
| `v_tan` | Tangential velocity -- the part that causes lateral miss |
| `flightT` | Flight time from the table (seconds) |
| `leadM` | How far the ball would miss (meters) = v_tan * flightT |
| `leadDeg` | Lead angle from physics (degrees) |
| `gain` | The `velocity_lead_gain` multiplier |
| `finalLead` | Lead angle actually applied = leadDeg * gain |
| `rawDist` | Distance before compensation |
| `corrDist` | Distance after closing speed adjustment |

If balls are missing, look at `v_tan` and `flightT` first. Those two values multiplied together give `leadM` -- how far the ball misses if we do not compensate. Then `leadDeg` shows how much we are aiming ahead to fix it.

---

## Step 2: Measure Flight Times

**Goal:** Get accurate `flight_time_s` values for the distance table. This is the foundation for everything.

The distance table is in `constants/shooter.py`:

```python
"distance_table": [
    # (distance_m, launcher_rps, flight_time_s)
    (1.5, 35.0, 0.30),
    (2.0, 37.0, 0.29),
    (3.0, 45.0, 0.33),
    (4.0, 54.0, 0.33),
    (5.0, 70.0, 0.33),
],
```

### How to measure flight time

1. Set up at a known distance (start with 2m)
2. Shoot at the Hub while stationary -- confirm shots are accurate
3. Have someone with a stopwatch time the ball: **start when it leaves the shooter, stop when it hits the Hub**
4. Do 3-5 shots and average
5. Write that number in the `flight_time_s` column
6. Repeat at each distance in your table

**Tips:**
- Phone stopwatch is fine -- you do not need millisecond precision
- If the times feel hard to measure (too fast), try slow-mo video instead. Count frames and divide by FPS.
- Flight time usually increases with distance (the ball has further to go)
- Do not stress about being perfect. Within 0.05s is good enough to start.

---

## Step 3: Test Slow Strafing

**Goal:** See if the lead correction is working at low speed.

1. Place the robot 2-3m from the Hub
2. Enable CoordinateAim (left bumper)
3. Hold left trigger (ShootWhenReady)
4. Strafe slowly left or right (~0.5 m/s)
5. Watch where balls land

**Look at the `[COMP]` log:**

| What you see | What the log shows | Fix |
|-------------|-------------------|-----|
| Balls miss in the direction you are moving | `finalLead` is too small | Flight time is too low -- re-measure, or increase `velocity_lead_gain` above 1.0 |
| Balls miss opposite to the direction you are moving | `finalLead` is too large | Flight time is too high -- re-measure, or decrease `velocity_lead_gain` below 1.0 |
| Balls land correctly left/right but short/long | Distance compensation is off | Re-check flight times at this distance |

### Adjusting velocity_lead_gain

`velocity_lead_gain` is in `constants/compensation.py`. It multiplies the physics-based lead angle:

- `1.0` = trust the physics (default)
- `1.2` = 20% more lead (if balls miss in direction of travel)
- `0.8` = 20% less lead (if balls miss opposite to travel)

**Start with flight time fixes first.** Only use `velocity_lead_gain` for fine-tuning after flight times are measured.

---

## Step 4: Test Faster Strafing

**Goal:** Verify compensation scales correctly at higher speeds.

1. Same setup, but strafe faster (1-2 m/s)
2. Shoot while strafing

The `[COMP]` log should show larger `v_tan`, larger `leadM`, and larger `finalLead`. If balls hit at slow speeds but miss at fast speeds, the flight time is probably too low (under-leading at high speed).

| Symptom | Fix |
|---------|-----|
| Turret can not keep up, visibly behind | Increase `turret_max_auto_voltage` (try 2.5 or 3.0) |
| Turret tracks but balls still miss | Check `flightT` in the log -- is it reasonable? |
| Turret oscillates wildly | Increase `turret_d_velocity_gain` (try 0.08-0.10) |

---

## Step 5: Test Driving Toward and Away

**Goal:** Verify distance compensation works.

1. Start 3m from the Hub, facing it
2. Enable CoordinateAim + ShootWhenReady
3. Drive slowly toward the Hub (~0.5 m/s) while shooting
4. Then drive slowly away while shooting

**Look at the `[COMP]` log:**

| What you see | What the log shows | Fix |
|-------------|-------------------|-----|
| Balls go long while approaching | `corrDist` is not much less than `rawDist` | Flight time too low at this distance |
| Balls fall short while retreating | `corrDist` is not much more than `rawDist` | Same -- flight time too low |

The correction is `closing_speed * flight_time`. If flight time is accurate, distance compensation should just work.

---

## Step 6: Test Diagonal and Full Speed

**Goal:** Verify everything works together.

1. Drive diagonally, shoot while moving
2. Then try full-speed driving: collect balls, shoot without stopping

The velocity decomposition handles all directions automatically. If Steps 2-5 are tuned, diagonal should just work.

**If accuracy drops at full speed:**

| Symptom | Fix |
|---------|-----|
| Turret can not keep up | Increase `turret_max_auto_voltage` (try 3.0-3.5) and `turret_p_gain` (try 0.40) |
| Balls miss consistently in one direction | Check `finalLead` in log -- is it the right magnitude? Adjust `velocity_lead_gain` |
| Everything is slightly off at certain distances | Add more entries to the distance table with measured flight times |

---

## Constants Quick Reference

### Compensation constants (`constants/compensation.py`)

| Constant | Default | Range to try | What it does |
|----------|---------|-------------|--------------|
| `velocity_lead_enabled` | True | True/False | Master on/off for angle compensation |
| `velocity_lead_gain` | 1.0 | 0.5 - 2.0 | Multiplier on the physics lead angle. Adjust after flight times are measured. |
| `min_distance` | 0.5 | 0.3 - 1.0 | Below this distance, skip compensation |

### Distance table (`constants/shooter.py`)

| Column | What it is | How to tune |
|--------|-----------|-------------|
| `distance_m` | Distance to Hub (meters) | Tape measure |
| `launcher_rps` | Launcher speed at this distance | Tune stationary first |
| `flight_time_s` | Ball flight time (seconds) | **Stopwatch: launch to landing** |

### Turret PD constants (`constants/shooter.py`)

These affect how fast the turret tracks, not the compensation math:

| Constant | Default | Range | What it does |
|----------|---------|-------|--------------|
| `turret_p_gain` | 0.30 | 0.20 - 0.50 | How aggressively turret chases errors |
| `turret_d_velocity_gain` | 0.05 | 0.03 - 0.12 | Turret braking (prevents overshoot) |
| `turret_max_auto_voltage` | 2.0 | 1.5 - 4.0 | Top speed of turret during auto-aim |
| `turret_alignment_tolerance` | 1.5 | 1.0 - 3.0 | Degrees of error where turret holds still |
| `turret_tx_filter_alpha` | 0.95 | 0.85 - 1.0 | Error smoothing (higher = faster response) |

---

## Troubleshooting Checklist

If nothing seems to work:

- [ ] Is CoordinateAim running? Check `AutoAim/OnTarget` exists on dashboard
- [ ] Is `AutoAim/DistanceM` correct? Compare to tape measure. If wrong, odometry has drifted
- [ ] Is the right alliance selected? Red and Blue Hubs are at different positions
- [ ] Is `velocity_lead_enabled` set to `True` in `constants/compensation.py`?
- [ ] Are flight times reasonable? (0.2-0.8s for typical FRC shooters)
- [ ] Is `turret_aim_inverted` correct? Turret should move toward the Hub, not away
- [ ] Is the gyro calibrated? Bad heading = bad velocity decomposition
- [ ] Is `compensation_logging` turned on? Check `[COMP]` lines in the log

---

**See also:**
- [Auto-Aim System](../architecture/auto-aim.md) -- Full auto-aim architecture and debugging
- [Shooter System](../architecture/shooter-system.md) -- Turret, launcher details
- [Telemetry](../architecture/telemetry.md) -- Dashboard setup
