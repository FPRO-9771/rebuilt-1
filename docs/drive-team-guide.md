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
    │   │ L │  Left Stick         Auto Shooter   │
    │   │   │  X = Manual       toggle on/off    │
    │   │   │  turret                            │
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
| **Y button** | Toggle auto shooter on/off | Aims turret, spins launcher, sets hood from vision |
| **Left stick X** | Manual turret aim | Cancels auto shooter if running |
| **A button** | Toggle manual launcher on/off | Cancels auto shooter if running |
| **Left bumper** | Increase launcher speed | +5% step, works without interrupting launcher |
| **Left trigger** | Decrease launcher speed | -5% step, works without interrupting launcher |
| **Right bumper** | Nudge hood up | Cancels auto shooter if running |
| **Right trigger** | Nudge hood down | Cancels auto shooter if running |
| **Right stick Y** | Manual conveyor | Runs while stick is held |

### Testing workflow

1. Start with auto shooter **off**
2. Use **A** to toggle launcher on, adjust speed with **left bumper/trigger**
3. Use **right bumper/trigger** to set hood angle
4. Use **left stick** to aim turret manually
5. Once mechanisms are tuned, press **Y** to enable auto shooter

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

- Any manual shooter input (turret stick, hood nudge, launcher toggle) **cancels the auto shooter**. Press **Y** again to re-enable it.
- Launcher speed adjustments (bumper/trigger) **never** cancel anything -- they just change the target speed for next time.
- SysId routines require holding **two buttons at once** (Back/Start + X/Y) so they can't be triggered accidentally.
