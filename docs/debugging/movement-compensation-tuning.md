# Movement Compensation Tuning Guide

**Team 9771 FPRO - 2026**

Step-by-step guide for tuning the shooter to hit targets while the robot is moving. Follow the steps in order -- each one builds on the previous.

> **Before you start:** This guide assumes the auto-aim system is wired and the turret tracks the Hub. CoordinateAim is on the **left bumper** (toggle) and ShootWhenReady is on the **left trigger** (hold).

---

## Background: What Compensates for Movement?

Three systems work together to keep shots accurate while moving:

| System | What it does | Where to tune |
|--------|-------------|---------------|
| **Turret tracking (FF)** | Counter-rotates turret in real time to stay pointed at the Hub | `turret_velocity_ff_gain` in `constants/shooter.py` |
| **Velocity lead** | Aims ahead of the Hub so the ball curves into it during flight | `velocity_lead_enabled` + `ball_speed_mps` in the distance table |
| **Distance compensation** | Adjusts launcher power for approach/retreat speed | `ball_speed_mps` in the distance table |

The velocity lead system decomposes robot velocity into two components:
- **Radial** (toward/away from Hub) -- handled by distance compensation
- **Tangential** (perpendicular to Hub line) -- handled by velocity lead

This means the lead correction works regardless of which direction the swerve bot is driving relative to the Hub.

---

## What You Need

- The robot, a Hub target, and open floor space (at least 4m x 4m)
- Fuel (at least 10 balls)
- A laptop connected to the robot (for SmartDashboard/Shuffleboard)
- A tape measure
- Someone to feed balls and someone to drive
- This guide printed out or on a phone

---

## Step 1: Verify Static Aiming Works

**Goal:** Confirm the turret aims correctly when the robot is NOT moving.

1. Place the robot 2m from the Hub, facing the Hub
2. Enable CoordinateAim (left bumper)
3. Watch `AutoAim/ErrorDeg` on the dashboard -- it should be near 0
4. Watch `AutoAim/OnTarget` -- it should be True
5. Shoot 5 balls. They should all hit the Hub

**If shots miss while stationary:** Fix static aiming first. Check odometry, turret zero, and shooter offset. Do not proceed until stationary shots are accurate.

**If `AutoAim/OnTarget` flickers:** The turret is oscillating near the tolerance boundary.
- Try increasing `turret_alignment_tolerance` from 1.5 to 2.0
- Or decrease `turret_p_gain` slightly

---

## Step 2: Test Slow Lateral Movement (Strafing)

**Goal:** See how shots behave during slow sideways movement.

1. Place the robot 2m from the Hub
2. Enable CoordinateAim
3. Start the launcher (right trigger, set speed for 2m)
4. Strafe slowly left at about 0.5 m/s (gentle left stick)
5. Feed balls (B button) while strafing
6. Watch where they land relative to the Hub

**What to look for:**

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Balls land behind the robot's direction of travel | Turret is lagging -- FF too low | Increase `turret_velocity_ff_gain` (try 0.4, then 0.5) |
| Balls land ahead of the robot's direction of travel | FF too high, overcompensating | Decrease `turret_velocity_ff_gain` (try 0.15) |
| Balls land correctly left/right but short/long | Distance compensation is off | Jump to Step 5 (ball speed calibration) |
| Turret visibly jerks or oscillates while moving | EMA filter or D gain issue | Decrease `turret_tx_filter_alpha` (try 0.90) or increase `turret_d_velocity_gain` |

**How to adjust `turret_velocity_ff_gain`:**

This is in `constants/shooter.py` under `CON_SHOOTER`. Current default: **0.25**.

- Edit the value, redeploy, test again
- Start with small changes (0.05 increments)
- The right value makes the turret smoothly track with no visible lag during slow strafing

Once slow strafing works at 2m, try it at 1.5m and 3m. The FF gain should work at all distances because it compensates for turret rotation rate, not ball flight.

---

## Step 3: Test Faster Lateral Movement

**Goal:** Verify the velocity lead correction works at higher speeds.

1. Same setup as Step 2, but strafe faster (about 1-2 m/s)
2. Shoot while strafing

At higher speeds, the turret FF keeps the turret pointed at the Hub, but the ball's flight time means it arrives at where the Hub *was* when launched. The velocity lead correction aims the turret slightly ahead to compensate.

**What to look for:**

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Balls consistently miss in the direction of travel | Lead correction too weak -- ball speed values too high | Decrease `ball_speed_mps` values in the distance table (Step 5) |
| Balls consistently miss opposite to travel direction | Lead correction too strong -- ball speed values too low | Increase `ball_speed_mps` values in the distance table (Step 5) |
| Turret can't keep up, visibly behind | `turret_max_auto_voltage` too low | Increase from 2.0 to 2.5 or 3.0 |

Watch `AutoAim/LeadDeg` on the dashboard (requires `DEBUG["debug_telemetry"] = True`). This shows how many degrees of lead the system is applying. At 1 m/s strafing at 2m, expect roughly 5-10 degrees of lead.

---

## Step 4: Test Driving Toward and Away from the Hub

**Goal:** Verify distance compensation works while approaching/retreating.

1. Start 3m from the Hub, facing it
2. Enable CoordinateAim and start the launcher
3. Drive slowly toward the Hub (about 0.5 m/s) while shooting
4. Then drive slowly away while shooting

**What to look for:**

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Balls go long while approaching | Distance compensation not reducing power enough | `ball_speed_mps` values too high -- the system underestimates flight time |
| Balls fall short while retreating | Distance compensation not adding enough power | Same cause -- `ball_speed_mps` values too high |
| Shots are fine approaching but miss retreating (or vice versa) | Asymmetric error suggests ball speed is approximately right but closing speed calculation may be off | Check `AutoAim/ClosingSpeed` on dashboard |

---

## Step 5: Calibrate Ball Speeds in the Distance Table

**Goal:** Get accurate `ball_speed_mps` values. These are the foundation for both lead correction and distance compensation.

The distance table is in `constants/shooter.py` under `CON_SHOOTER["distance_table"]`:

```python
"distance_table": [
    # (distance_m, launcher_rps, hood_position, ball_speed_mps)
    (1.5, 33.0, 0, 5.0),
    (2.0, 37.0, 0, 7.0),
    (3.0, 47.0, 0, 9.0),
],
```

### How to measure ball speed (simple method)

You don't need a radar gun. Use a phone with slow-motion video (most phones do 240fps).

1. Set up at a known distance (e.g. 2m)
2. Place two markers on the floor 1 meter apart along the ball's path
3. Shoot a ball and record it in slow-mo
4. Count frames between the ball crossing marker 1 and marker 2
5. `ball_speed = 1.0 / (frames / fps)`

Example: 240fps camera, ball crosses 1m in 30 frames = 1.0 / (30/240) = **8.0 m/s**

### How to measure ball speed (no slow-mo method)

If slow-mo is not available, use the strafing test:

1. Set up at 2m, aim stationary, confirm shots hit
2. Strafe at a known speed (use `AutoAim/vx` or `AutoAim/vy` on the dashboard to read your speed)
3. Note how far the balls miss (in ball-widths or inches)
4. If balls miss by `d` meters at lateral speed `v_lat` from distance `D`:
   - `flight_time = d / v_lat`
   - `ball_speed = D / flight_time`
5. Update the table

### Tips for ball speed calibration

- Do each distance 3-5 times and average
- Ball speed increases with distance (because you're spinning the launcher faster)
- The values don't need to be perfect -- within 20% is usually good enough
- After updating, re-test Step 3 (fast strafing) to verify

---

## Step 6: Test Diagonal Movement

**Goal:** Verify the full velocity decomposition works when driving at angles to the Hub.

The velocity lead system decomposes your full velocity (vx, vy) into radial and tangential components relative to the Hub. This means it should work regardless of drive direction.

1. Place the robot 2.5m from the Hub
2. Drive diagonally (e.g. forward-left at 45 degrees to the Hub line)
3. Shoot while moving

If Steps 2-5 are tuned correctly, diagonal movement should just work. If it doesn't:
- Check `AutoAim/LeadDeg` -- it should be nonzero whenever you have tangential velocity
- Check `AutoAim/ClosingSpeed` -- it should be nonzero whenever you have radial velocity

---

## Step 7: Test at Competition Speed

**Goal:** Full-speed intake-and-shoot while moving.

1. Scatter balls on the field
2. Drive around collecting balls
3. Shoot at the Hub while still moving between pickups
4. Don't stop to shoot -- that's what we're trying to eliminate

**If accuracy drops significantly at full speed:**

| Symptom | Fix |
|---------|-----|
| Turret can't keep up at all | Increase `turret_max_auto_voltage` (try 3.0-3.5) and `turret_p_gain` (try 0.45) |
| Turret tracks but balls miss consistently | Re-check ball speed values -- errors compound at high speed |
| Turret oscillates wildly | Increase `turret_d_velocity_gain` (try 0.08-0.10) |
| Everything is slightly off | You may need to add more entries to the distance table at the distances you're shooting from |

---

## Constants Quick Reference

All in `constants/shooter.py` under `CON_SHOOTER`:

| Constant | Default | Range to try | What it does |
|----------|---------|-------------|--------------|
| `turret_velocity_ff_gain` | 0.25 | 0.15 - 0.60 | Real-time turret counter-rotation speed |
| `turret_tx_filter_alpha` | 0.95 | 0.85 - 1.0 | Error smoothing (higher = less smoothing, faster response) |
| `turret_p_gain` | 0.30 | 0.20 - 0.50 | How aggressively turret chases errors |
| `turret_d_velocity_gain` | 0.05 | 0.03 - 0.12 | Turret braking (prevents overshoot) |
| `turret_max_auto_voltage` | 2.0 | 1.5 - 4.0 | Top speed of turret during auto-aim |
| `turret_alignment_tolerance` | 1.5 | 1.0 - 3.0 | Degrees of error where turret holds still |
| `velocity_lead_enabled` | True | True/False | Enable/disable aim-ahead correction |
| `ball_speed_mps` (in table) | 5-9 | Measure! | Ball flight speed at each distance |

---

## Dashboard Keys to Watch

Enable `DEBUG["debug_telemetry"] = True` in `constants/debug.py` to see all of these.

| Key | What it tells you |
|-----|------------------|
| `AutoAim/OnTarget` | Is the turret aimed correctly right now? |
| `AutoAim/ErrorDeg` | How far off is the turret (degrees)? |
| `AutoAim/DistanceM` | Distance to Hub (should match your tape measure) |
| `AutoAim/LeadDeg` | How much aim-ahead is being applied |
| `AutoAim/ClosingSpeed` | How fast you're approaching/retreating |
| `AutoAim/vx`, `AutoAim/vy` | Robot velocity components |

---

## Troubleshooting Checklist

If nothing seems to work:

- [ ] Is CoordinateAim actually running? Check `AutoAim/OnTarget` exists on dashboard
- [ ] Is `AutoAim/DistanceM` correct? Compare to tape measure. If wrong, odometry is drifted
- [ ] Is the right alliance selected? Red and Blue Hubs are at different positions
- [ ] Is `velocity_lead_enabled` set to `True`?
- [ ] Are ball speed values reasonable? (3-15 m/s range for typical FRC shooters)
- [ ] Is `turret_aim_inverted` correct? Turret should move toward the Hub, not away
- [ ] Is the gyro calibrated? Bad heading = bad velocity decomposition

---

**See also:**
- [Auto-Aim System](../architecture/auto-aim.md) -- Full auto-aim architecture and debugging
- [Shooter System](../architecture/shooter-system.md) -- Turret, launcher, hood details
- [Telemetry](../architecture/telemetry.md) -- Dashboard setup
