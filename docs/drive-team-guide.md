# Drive Team Guide

**Team 9771 FPRO - 2026**

Quick reference for what every button does on each Xbox controller.

---

## Operator Controller (Port 1)

### Joysticks

| Input | Action | Notes |
|-------|--------|-------|
| **Left stick X** | Manual turret aim | Interrupts auto-aim; auto-aim resumes on release |
| **Left stick Y** | Manual hood nudge | Tap up = more closed, tap down = more open. Always active. |
| **Right stick X** | *unassigned* | |
| **Right stick Y** | Launcher speed | Only active when launcher is toggled on (A). Forward = fast, back = slow |

### Face Buttons

| Input | Action | Notes |
|-------|--------|-------|
| **A button** | Toggle launcher on/off | Speed controlled by right stick Y |
| **B button** | Toggle feeds on/off | Runs H feed + V feed together |
| **X button** | *unassigned* | |
| **Y button** | Toggle coordinate aim on/off | Turret aims at Hub using odometry -- no vision needed |

### Bumpers & Triggers

| Input | Action | Notes |
|-------|--------|-------|
| **Left bumper (hold)** | Auto-shoot | Sets launcher speed + hood from vision distance |
| **Right bumper** | Toggle intake deploy + spinner | Lowers intake arm and spins rollers together |
| **Left trigger (hold)** | Shoot when ready | Spins launcher + sets hood; feeds only when at speed AND on target |
| **Right trigger** | *unassigned* | |

### D-pad / Other

| Input | Action | Notes |
|-------|--------|-------|
| **D-pad** | *unassigned* | |
| **Back / Start** | *unassigned* | |

### How to shoot (manual aim)

1. Press **right bumper** to deploy intake and spin rollers
2. Use **left stick X** to aim the turret at the target
3. Tap **left stick Y** to nudge the hood angle (up = closed, down = open)
4. Press **A** to toggle launcher on, use **right stick Y** to set speed
5. Press **B** to start feeding Fuel

### How to shoot (coordinate aim + auto-shoot)

1. Press **right bumper** to deploy intake and spin rollers
2. Press **Y** to enable coordinate aim (turret aims at Hub via odometry)
3. Hold **left bumper** to auto-shoot (sets speed + hood from distance)
4. Press **B** to start feeding Fuel

### How to shoot (one button)

1. Press **right bumper** to deploy intake and spin rollers
2. Press **Y** to enable coordinate aim
3. Hold **left trigger** -- launcher spins up, hood sets angle, feeds run automatically when on target and at speed

### Testing workflow

1. Press **right bumper** to deploy intake and spin rollers (pulls Fuel in)
2. Press **A** to toggle launcher on, sweep **right stick Y** to find good speed
3. Use **left stick X** to aim turret, tap **left stick Y** to adjust hood angle
4. Press **B** to run feeds
5. Try **Y** (coordinate aim) and **left bumper** (auto-shoot) when ready

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
| **A button (hold)** | Brake | Locks wheels in X pattern |
| **B button (hold)** | Point wheels | Aims wheels in left stick direction |
| **X button** | *unassigned* | SysId combo only (Back/Start + X) |
| **Y button (hold)** | Drive straight forward | Alignment test -- 25% speed, robot-centric |

### Bumpers & Triggers

| Input | Action | Notes |
|-------|--------|-------|
| **Left bumper** | Reset field-centric heading | Press once when robot faces away from you |
| **Right bumper** | Toggle field/robot centric | Dashboard shows current mode |
| **Left trigger** | *unassigned* | |
| **Right trigger** | *unassigned* | |

### D-pad / Other

| Input | Action | Notes |
|-------|--------|-------|
| **D-pad** | *unassigned* | |
| **Back + Y** | SysId dynamic forward | Motor characterization only |
| **Back + X** | SysId dynamic reverse | Motor characterization only |
| **Start + Y** | SysId quasistatic forward | Motor characterization only |
| **Start + X** | SysId quasistatic reverse | Motor characterization only |

### Driving tips

- **10% deadband** is applied to both sticks -- small bumps are ignored
- Default mode is **field-centric** -- pushing the stick "away from you" always drives away from the alliance wall, regardless of which way the robot is facing
- Press **right bumper** to switch to **robot-centric** (stick directions are relative to the robot's nose) -- useful for camera-guided maneuvering. Press again to switch back
- Check **Drive/Robot Centric** on the dashboard to see which mode is active
- If the heading drifts, press **left bumper** while the robot faces away from you to reset
- Alliance color is detected automatically -- no need to configure red vs blue

---

## Important Interactions

- **Coordinate aim (Y toggle)** can run alongside manual turret stick -- the stick temporarily overrides, and coordinate aim resumes when released.
- **Auto-shoot (left bumper)** takes over the launcher and hood from manual mode. Release the bumper, then press A again to go back to manual launcher.
- **Shoot when ready (left trigger)** does everything auto-shoot does, plus runs feeds automatically when aligned and at speed.
- **Hood nudge (left stick Y)** is always active as a default command. Auto-shoot and shoot-when-ready temporarily override it; it resumes when they end.
- **Right bumper** deploys the intake arm and spins the rollers together -- one button for the whole intake system.
- SysId routines require holding **two buttons at once** (Back/Start + X/Y) so they can't be triggered accidentally.
