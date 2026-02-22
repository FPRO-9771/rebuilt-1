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

> Not yet configured. Will be added when drivetrain is built.

| Input | Action | Notes |
|-------|--------|-------|
| Left stick | Drive (translation) | TBD |
| Right stick X | Drive (rotation) | TBD |

---

## Important Interactions

- Any manual shooter input (turret stick, hood nudge, launcher toggle) **cancels the auto shooter**. Press **Y** again to re-enable it.
- Launcher speed adjustments (bumper/trigger) **never** cancel anything — they just change the target speed for next time.
