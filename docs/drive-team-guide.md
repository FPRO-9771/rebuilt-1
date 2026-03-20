# Drive Team Guide

**Team 9771 FPRO - 2026**

Quick reference for what every button does on each Xbox controller.

---

## Operator Controller (Port 1)

### Joysticks

| Input | Action | Notes |
|-------|--------|-------|
| **Left stick X** | Manual turret aim | Active when stick is outside deadband |
| **Left stick Y** | *unassigned* | |
| **Right stick X** | *unassigned* | |
| **Right stick Y** | Launcher speed | Only active when launcher is held (right trigger). Forward = fast, back = slow |

### Face Buttons

| Input | Action | Notes |
|-------|--------|-------|
| **A button** | *unassigned* | |
| **B button** | *unassigned* | |
| **X button** | *unassigned* | |
| **Y button** | *unassigned* | |

### Bumpers & Triggers

| Input | Action | Notes |
|-------|--------|-------|
| **Left bumper (toggle)** | Toggle auto-aim on/off | Turret aims at Hub via odometry |
| **Left trigger (hold)** | Auto-shoot | Spins launcher; feeds when launcher at speed AND auto-aim on target |
| **Right bumper (hold)** | Reverse all feeds (unjam) | Reverses H feed, V feed, and conveyor; interrupts right trigger |
| **Right trigger (hold)** | Manual shoot (hold) | Spins launcher (right stick Y = speed); auto-feeds when at speed |

### D-pad / Other

| Input | Action | Notes |
|-------|--------|-------|
| **D-pad** | *unassigned* | |
| **Back / Start** | *unassigned* | |

### How to shoot (manual aim)

1. Driver presses **Y** to deploy intake, holds **left trigger** to spin rollers
2. Use **left stick X** to aim the turret at the target
3. Hold **right trigger** to spin launcher, use **right stick Y** to set speed
4. Feeds run automatically when launcher reaches target speed

### Testing workflow

1. Driver presses **Y** to deploy intake, holds **left trigger** to spin rollers (pulls Fuel in)
2. Hold **right trigger** to spin launcher, sweep **right stick Y** to find good speed
3. Use **left stick X** to aim turret
4. Feeds activate automatically when launcher is at speed

---

## Driver Controller (Port 0)

### Joysticks

| Input | Action | Notes |
|-------|--------|-------|
| **Left stick X** | Strafe | Field-centric by default |
| **Left stick Y** | Forward / back | Field-centric by default |
| **Right stick X** | Rotation | Counterclockwise with left input |
| **Right stick Y** | *unassigned* | |

### Face Buttons

| Input | Action | Notes |
|-------|--------|-------|
| **A button** | Manual Hub odometry reset | Drive to front of Hub, center robot, press A |
| **B button** | Limelight odometry reset | One-shot MegaTag2 pose reset |
| **X button** | *unassigned* | SysId combo only (Back/Start + X) |
| **Y button** | Toggle intake deploy | Lowers/raises intake arm |

### Bumpers & Triggers

| Input | Action | Notes |
|-------|--------|-------|
| **Left bumper** | Reset field-centric heading | Press once when robot faces away from you |
| **Right bumper** | Toggle field/robot centric | Dashboard shows current mode |
| **Left trigger (hold)** | Run intake | Spins intake rollers + holds arm in place |
| **Right trigger** | Slow mode | Squeeze to cap speed; harder squeeze = slower max |

### D-pad / Other

| Input | Action | Notes |
|-------|--------|-------|
| **D-pad** | *unassigned* | |
| **Back + Y** | SysId dynamic forward | Motor characterization only |
| **Back + X** | SysId dynamic reverse | Motor characterization only |
| **Start + Y** | SysId quasistatic forward | Motor characterization only |
| **Start + X** | SysId quasistatic reverse | Motor characterization only |

### Tuning drive feel

The power curve controls how stick position maps to actual speed. A higher
exponent gives more fine control at low/mid stick and reserves full power for
the very end of stick travel. Edit `constants/controls.py` to change these:

| Setting | Current | What it does |
|---------|---------|--------------|
| `drive_exponent` | 4.0 | Translation (left stick) response curve (normal mode) |
| `rotation_exponent` | 5.0 | Rotation (right stick X) response curve (normal mode) |
| `stick_deadband` | 0.03 | 3% stick dead zone (prevents drift) |
| `slow_max_speed` | 2.0 m/s | Speed ceiling at lightest trigger squeeze |
| `slow_min_speed` | 0.5 m/s | Speed ceiling at full trigger squeeze |

**Quick reference -- how much power at each stick position:**

| Stick % | Exp 2 | Exp 3 | Exp 4 | Exp 5 |
|---------|-------|-------|-------|-------|
| 25% | 6.3% | 1.6% | 0.4% | 0.1% |
| 50% | 25% | 12.5% | 6.3% | 3.1% |
| 75% | 56% | 42% | 32% | 24% |
| 100% | 100% | 100% | 100% | 100% |

- **Too jumpy?** Increase the exponent (try 5 or 6).
- **Too sluggish?** Decrease the exponent (try 3 or 2).
- Translation and rotation can be tuned independently.

### Driving tips

- **3% deadband** is applied to both sticks -- small bumps are ignored
- Default mode is **field-centric** -- pushing the stick "away from you" always drives away from the alliance wall, regardless of which way the robot is facing
- Press **right bumper** to switch to **robot-centric** (stick directions are relative to the robot's nose) -- useful for camera-guided maneuvering. Press again to switch back
- Check **Drive/Robot Centric** on the dashboard to see which mode is active
- If the heading drifts, press **left bumper** while the robot faces away from you to reset
- Alliance color is detected automatically -- no need to configure red vs blue

---

## Important Interactions

- **Reverse all feeds (right bumper)** interrupts the right trigger manual shoot since both require h_feed/v_feed. Release right bumper and hold right trigger again to resume shooting.
- **Driver Y** toggles the intake arm up/down. **Driver left trigger** spins the intake rollers and holds the arm in place.
- SysId routines require holding **two buttons at once** (Back/Start + X/Y) so they can't be triggered accidentally.
