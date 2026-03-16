# Test Plan: Pose-Based Aiming System

**Team 9771 FPRO -- 2026**
**Date: March 16, 2026**

Step-by-step checkout for the new pose-based turret aiming and auto-shoot system. Work through each phase in order -- each one builds on the last. If something fails, fix it before moving on.

**What you need:**
- Robot on the ground (not on blocks) with bumpers
- Operator Xbox controller plugged into the laptop (Port 1)
- Laptop running Elastic dashboard
- SSH access for logs (`ssh admin@10.97.71.2`)
- A target to aim at (ideally the Hub, but a cone or bucket works for early tests)
- Measuring tape

**Before you start:**
1. Deploy code: `source .venv/bin/activate && python -m robotpy deploy`
2. Open Elastic on the laptop
3. Set alliance to Red on the Alliance chooser in Elastic
4. Set starting pose to Center

---

## Phase 1: Manual Turret Checkout (5 min)

**Goal:** Confirm the turret motor works and soft limits are enforced.

**Debug settings:** No special settings needed.

| Step | Action | What to Look For | Pass? |
|------|--------|-----------------|-------|
| 1.1 | Enable teleop. Push left stick X right. | Turret rotates. Note which direction. | |
| 1.2 | Push left stick X left. | Turret rotates the other way. | |
| 1.3 | Hold left stick X right until turret stops. | Turret stops at soft limit, does not slam into hard stop. Check `Motors/Turret Position` on Elastic. | |
| 1.4 | Hold left stick X left until turret stops. | Turret stops at other soft limit. | |
| 1.5 | Release stick. | Turret holds position (not drifting). | |

**If turret direction is backwards:** Flip `inverted` in `constants/shooter.py` -> `CON_TURRET`.

**If turret does not stop at limits:** Check `min_position` and `max_position` in `CON_TURRET`. The position value on Elastic should be between those values.

---

## Phase 2: Pose Estimation Sanity Check (10 min)

**Goal:** Confirm the robot knows where it is on the field. Everything downstream depends on this.

**Debug settings:** Make sure `auto_aim_dashboard: True` in `constants/debug.py`.

| Step | Action | What to Look For | Pass? |
|------|--------|-----------------|-------|
| 2.1 | Place robot at a known position (e.g. Center start). Enable teleop. | Check Elastic for pose values. `AimDash/ShooterToHubM` should roughly match the real distance to the Hub (or where the Hub would be). | |
| 2.2 | Use a tape measure. Measure the real distance from the robot to the target. | `AimDash/ShooterToHubM` should be within ~0.5m of the measured distance. | |
| 2.3 | Rotate the robot 90 degrees in place. | `AimDash/BearingToHubDeg` should change by roughly 90. Distance should stay about the same. | |
| 2.4 | Drive the robot 1-2 meters toward the target. | `AimDash/ShooterToHubM` should decrease by roughly the distance you drove. | |
| 2.5 | Drive the robot 1-2 meters away from the target. | `AimDash/ShooterToHubM` should increase. | |

**If distance is way off:**
- Check `target_x` and `target_y` in `constants/match.py` for your alliance
- Check that the starting pose matches where you actually placed the robot
- Check `shooter_offset_x` and `shooter_offset_y` in `constants/pose.py`

**If bearing does not change when you rotate:**
- The gyro may not be calibrated. Let the robot sit still for 5 seconds after power-on before enabling.

---

## Phase 3: Static Pose-Based Aiming (15 min)

**Goal:** Turret points at the target when the robot is stationary.

**Debug settings:** Set `auto_aim_logging: True` and `verbose: False` in `constants/debug.py`. SSH into the robot and watch the log: `ssh admin@10.97.71.2` then `tail -f /var/log/messages | grep AIM`

| Step | Action | What to Look For | Pass? |
|------|--------|-----------------|-------|
| 3.1 | Place robot 3-4 meters from target, facing it. Press Y to enable coordinate aim. | Turret should rotate to point at the target. `AutoAim/OnTarget` on Elastic should turn True. | |
| 3.2 | Read the SSH log. | You should see `[AIM HOLD]` lines. Check that `pose=` matches where you placed the robot, `tgt=` matches the Hub coordinates, `err=` is small (< 2 degrees). | |
| 3.3 | Press Y to disable. Manually rotate turret with left stick. Press Y again. | Turret should swing back to point at the target. | |
| 3.4 | Place robot at a different position (e.g. 45 degrees off to the side). Press Y. | Turret should aim at the target from the new angle. | |
| 3.5 | Place robot 1 meter from target. Press Y. | Turret aims. Distance on log should show ~1m. | |
| 3.6 | Place robot 5+ meters from target. Press Y. | Turret aims. Distance on log should show ~5m. | |

**If turret points the wrong way:**
- Flip `turret_aim_inverted` in `CON_SHOOTER`
- Check that `center_position` in `CON_POSE` is correct (the motor position when turret faces forward)
- Check `degrees_per_rotation` in `CON_POSE` (should be 360 / number of motor rotations for one full turret rotation)

**If turret oscillates back and forth:**
- Lower `turret_p_gain` in `CON_SHOOTER`
- Check `turret_alignment_tolerance` -- if too tight, the turret never reaches HOLD state
- Check `turret_tx_filter_alpha` -- lower it (toward 0.5) for more smoothing

**If turret gets stuck at a soft limit:**
- This is the routing working. If the shortest path hits a limit, it goes the long way. If it can't reach either way, it goes to the nearest limit. Check `rte=` in the log -- that's the routed error.

---

## Phase 4: Aiming While Moving (10 min)

**Goal:** Turret tracks the target while the robot drives around.

**Debug settings:** Same as Phase 3. Watch the SSH log for `[AIM DRIVE]` lines.

| Step | Action | What to Look For | Pass? |
|------|--------|-----------------|-------|
| 4.1 | Press Y to enable aim. Slowly drive forward toward the target. | Turret stays pointed at target. On the log, `trk=` (tracking correction) should be small. | |
| 4.2 | Drive slowly to the left (strafe). | Turret compensates. `trk=` should be nonzero. The turret should stay roughly aimed. | |
| 4.3 | Drive slowly to the right (strafe). | Turret compensates in the other direction. `trk=` flips sign. | |
| 4.4 | Drive in a circle around the target. | Turret continuously tracks. It should never lose the target (there is no "lost" state with pose-based aiming). | |
| 4.5 | Drive faster. | Turret may lag behind but should recover. If it overshoots, note it -- we'll tune later. | |

**If turret lags badly while strafing:**
- Increase `turret_velocity_ff_gain` in `CON_SHOOTER` (currently 0.15)
- This is the feedforward that pre-compensates for lateral movement

**If turret overshoots and oscillates while moving:**
- Increase `turret_d_velocity_gain` slightly (currently 0.03)
- Or lower `turret_max_auto_voltage` to cap the drive speed

---

## Phase 5: Auto-Shoot Distance Lookup (10 min)

**Goal:** Launcher and hood set themselves based on distance to the target.

**Debug settings:** Same SSH log. Now also watch for `[SHOOT]` lines (they appear on odd cycles, interleaved with aim logs).

| Step | Action | What to Look For | Pass? |
|------|--------|-----------------|-------|
| 5.1 | Place robot 2m from target. Hold left bumper (AutoShoot). | Launcher spins up. On the log: `[SHOOT] rawDist=~2.00` and `rps=` should match the 2m entry in the distance table. | |
| 5.2 | Release left bumper. | Launcher and hood stop. | |
| 5.3 | Move to 3m. Hold left bumper. | `rawDist=~3.00`, `rps=` should be higher (farther = more power). | |
| 5.4 | Move to 1m. Hold left bumper. | `rawDist=~1.00`, `rps=` should be lower. | |
| 5.5 | While holding left bumper, slowly drive away from target. | `rawDist` increases, `corrDist` should be slightly higher than raw (closing speed is negative = retreating). `rps` should gradually increase. | |

**If RPS does not change with distance:**
- Check the distance table in `CON_SHOOTER` -- are there enough entries?
- Check `[SHOOT]` log for the `rawDist` value -- is it changing?

**If corrected distance seems wrong:**
- `cls=` in the log is closing speed. Positive = approaching, negative = retreating.
- The correction uses ball flight time. If ball speed entries in the distance table are way off, the correction will be off too.

---

## Phase 6: Shoot When Ready -- Full Integration (10 min)

**Goal:** The complete pipeline -- aim + spin up + feed only when everything is ready.

| Step | Action | What to Look For | Pass? |
|------|--------|-----------------|-------|
| 6.1 | Press Y (coordinate aim on). Hold left trigger (shoot when ready). | Turret aims, launcher spins up. Feeds should NOT run yet. Log shows `WAITING`. | |
| 6.2 | Wait for launcher to reach speed and turret to be on target. | Feeds start running. Log shows `AT_SPEED ON_TARGET FEEDING`. `AutoAim/OnTarget` = True on Elastic. | |
| 6.3 | While holding left trigger, manually bump the turret with left stick X. | Feeds should stop (turret off target). Log shows `AT_SPEED` but not `ON_TARGET`. | |
| 6.4 | Release left stick. Let turret re-aim. | Feeds resume when back on target. | |
| 6.5 | Release left trigger. | Everything stops -- launcher, hood, feeds. | |

---

## Phase 7: Tuning Notes

After completing all phases, record these values for the tuning log:

| Parameter | Current Value | Observation | New Value |
|-----------|--------------|-------------|-----------|
| `turret_p_gain` | 0.16 | | |
| `turret_d_velocity_gain` | 0.03 | | |
| `turret_max_auto_voltage` | 0.6 | | |
| `turret_min_move_voltage` | 0.20 | | |
| `turret_alignment_tolerance` | 1.5 | | |
| `turret_velocity_ff_gain` | 0.15 | | |
| `turret_tx_filter_alpha` | 0.85 | | |
| `center_position` | 4.5 | | |
| `degrees_per_rotation` | 40.0 | | |
| `shooter_offset_x` | -0.1524 | | |
| `shooter_offset_y` | -0.2032 | | |

**What to bring back from testing:**
- Are the Hub coordinates in `match.py` correct? Measure them.
- Is `center_position` correct? What motor position is "turret forward"?
- Is `degrees_per_rotation` correct? Rotate the turret 360 degrees and note how many motor rotations that takes.
- Does the turret track smoothly or does it oscillate? Note the conditions.
- Does distance compensation help or hurt? (Try driving while shooting.)

---

## Quick Debug Reference

### SSH log commands
```bash
ssh admin@10.97.71.2
tail -f /var/log/messages | grep AIM     # aim logs only
tail -f /var/log/messages | grep SHOOT   # shoot logs only
tail -f /var/log/messages | grep -E "AIM|SHOOT"  # both
```

### Log line cheat sheet

**[AIM HOLD]** -- turret is on target, not moving
```
pose=(x,y)  hdg=heading  shooter=(sx,sy)  tgt=(tx,ty)  tpos=turret_rotations
err=degrees  dist=meters  cls=closing_speed  -- HOLD
```

**[AIM DRIVE]** -- turret is actively correcting
```
pose  shooter  tgt  tpos
| err  dist  cls                          <- what we computed
| trk=tracking  ld=lead  rte=routed  flt=filtered  <- corrections
| P  D  FF  rv=raw_voltage  v=voltage [ok/SAT]  tvel  <- PD output
| vel=(vx,vy)                             <- robot velocity
```

**[SHOOT]** -- launcher/hood settings from distance
```
pose  shooter  tgt
| rawDist  corrDist  cls  vel             <- distance + velocity
| rps  actual=current_speed  hood         <- motor commands
| AT_SPEED ON_TARGET FEEDING / WAITING    <- status flags
```

### Elastic keys to watch
| Key | What It Means |
|-----|---------------|
| `AutoAim/OnTarget` | True = turret is aimed at Hub |
| `AutoAim/ErrorDeg` | How far off the turret is (debug only) |
| `AutoAim/DistanceM` | Distance to Hub (debug only) |
| `AimDash/ShooterToHubM` | Distance from shooter to Hub |
| `AimDash/BearingToHubDeg` | Angle from robot front to Hub |
