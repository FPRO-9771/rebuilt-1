# Drive Team Guide

**Team 9771 FPRO - 2026**

Quick reference for what every button does on each Xbox controller.

---

## Operator Controller (Port 1)

```
          Left Bumper               Right Bumper
       Launcher speed +             Hood nudge up

       Left Trigger                 Right Trigger
       Launcher speed -             Hood nudge down

    ┌────────────────────────────────────────────┐
    │                                            │
    │   ┌───┐                        (Y)        │
    │   │ L │  Left Stick         Hold to Shoot  │
    │   │   │  X = Manual       (spins up,       │
    │   │   │  turret           feeds when lock)  │
    │   └───┘                 (X)        (B)     │
    │                                            │
    │                            (A)             │
    │                     Manual Launcher        │
    │              ┌───┐  toggle on/off          │
    │              │ R │                          │
    │              │   │  Right Stick             │
    │              │   │  Y = Conveyor            │
    │              └───┘                          │
    │                                            │
    └────────────────────────────────────────────┘
```

| Input | Action | Notes |
|-------|--------|-------|
| **Y button (hold)** | Hold to shoot | Spins launcher, sets hood; feeds when lock indicator is green |
| **Left stick X** | Manual turret aim | Interrupts auto-tracking; resumes on release |
| **A button** | Toggle manual launcher on/off | Cancels shoot command if running |
| **Left bumper** | Increase launcher speed | +5% step, works without interrupting launcher |
| **Left trigger** | Decrease launcher speed | -5% step, works without interrupting launcher |
| **Right bumper** | Nudge hood up | Cancels shoot command if running |
| **Right trigger** | Nudge hood down | Cancels shoot command if running |
| **Right stick Y** | Manual conveyor | Runs while stick is held |

### How shooting works

1. **Turret auto-tracks** scoring tags automatically during teleop -- no button needed
2. Watch the **Shooter/Lock** indicator on the dashboard (green = ready to fire)
3. **Hold Y** to spin up the launcher and set the hood -- feeder engages when locked
4. Release Y to stop

### Testing workflow

1. Use **A** to toggle launcher on, adjust speed with **left bumper/trigger**
2. Use **right bumper/trigger** to set hood angle
3. Use **left stick** to aim turret manually (auto-tracking resumes when released)
4. Hold **Y** to test the full shoot sequence

---

## Driver Controller (Port 0)

```
          Left Bumper               Right Bumper
       Reset heading               (unused)

       Left Trigger                 Right Trigger
       (unused)                     (unused)

    +-------------------------------------------------+
    |                                                 |
    |   +---+                        (Y)             |
    |   | L |  Left Stick         SysId (with        |
    |   |   |  X = Strafe         Back or Start)     |
    |   |   |  Y = Forward/Back                      |
    |   +---+                 (X)          (B)       |
    |                        SysId      Point wheels  |
    |                        (combo)    in stick dir  |
    |                            (A)                  |
    |                          Brake                  |
    |              +---+                              |
    |              | R |                              |
    |              |   |  Right Stick                 |
    |              |   |  X = Rotation                |
    |              +---+                              |
    |                                                 |
    +-------------------------------------------------+
```

| Input | Action | Notes |
|-------|--------|-------|
| **Left stick** | Field-centric drive (translation) | X = strafe, Y = forward/back |
| **Right stick X** | Rotation | Counterclockwise with left input |
| **A button (hold)** | Brake | Locks wheels in X pattern |
| **B button (hold)** | Point wheels | Aims wheels in left stick direction |
| **Left bumper** | Reset field-centric heading | Press once when robot faces away from you |
| **Back + Y** | SysId dynamic forward | For motor characterization only |
| **Back + X** | SysId dynamic reverse | For motor characterization only |
| **Start + Y** | SysId quasistatic forward | For motor characterization only |
| **Start + X** | SysId quasistatic reverse | For motor characterization only |

### Driving tips

- **10% deadband** is applied to both sticks -- small bumps are ignored
- Drive is **field-centric** -- pushing the stick "away from you" always drives away from the alliance wall, regardless of which way the robot is facing
- If the heading drifts, press **left bumper** while the robot faces away from you to reset
- Alliance color is detected automatically -- no need to configure red vs blue

---

## Important Interactions

- **Turret auto-tracks** continuously. Manual turret stick temporarily overrides; tracking resumes on release.
- Hood nudge or launcher toggle will **cancel the shoot command** if Y is held. Release and re-hold Y to resume.
- Launcher speed adjustments (bumper/trigger) **never** cancel anything -- they just change the target speed for next time.
- SysId routines require holding **two buttons at once** (Back/Start + X/Y) so they can't be triggered accidentally.
