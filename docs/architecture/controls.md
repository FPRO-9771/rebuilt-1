# Controls & Manual Overrides

**Team 9771 FPRO - 2026**

This doc covers how controller bindings are organized to keep `robot_container.py` short, and how manual override controls work alongside the automated shooter.

> **When to read this:** You're adding new button bindings, wondering how manual controls interact with the auto shooter, or trying to keep robot_container from growing out of control.

---

## Table of Contents

1. [Binding Extraction Pattern](#1-binding-extraction-pattern)
2. [Operator Control Map](#2-operator-control-map)
3. [Manual Override Design](#3-manual-override-design)
4. [How Overrides Interact with Auto Shooter](#4-how-overrides-interact-with-auto-shooter)

---

## 1. Binding Extraction Pattern

As the robot gains mechanisms, `robot_container.py` grows fast. Every new button binding adds lines. The fix: group bindings by controller role and move them to dedicated modules.

### Before (everything in robot_container)

```python
# robot_container.py — gets long fast
class RobotContainer:
    def _configure_bindings(self):
        # 10 lines of operator controls...
        # 10 lines of driver controls...
        # More for each new mechanism...
```

### After (one function call per role)

```python
# robot_container.py — stays short
from controls import configure_operator

class RobotContainer:
    def _configure_bindings(self):
        configure_operator(
            self.operator, self.conveyor, self.turret,
            self.launcher, self.hood, self.vision,
        )
        # configure_driver(self.driver, self.drivetrain)  # future
```

The binding module (`controls/operator_controls.py`) receives the controller and subsystems, then wires everything internally. `robot_container.py` doesn't need to know which button does what.

### Adding a New Binding

When you add a new operator control:

1. Edit `controls/operator_controls.py` — add the binding
2. Add any new constants to `constants.py` under `CON_MANUAL`
3. If the function signature changes (new subsystem needed), update the call in `robot_container.py`
4. Write tests in `tests/test_operator_controls.py`

---

## 2. Operator Control Map

| Input | Binding | Action |
|-------|---------|--------|
| Right stick Y | `whileTrue` | Conveyor manual control |
| Y button | `toggleOnTrue` | Auto shooter on/off |
| Left stick X | `whileTrue` | Manual turret override |
| A button | `toggleOnTrue` | Manual launcher on/off |
| Left bumper | `onTrue` | Increase launcher speed (+5%) |
| Left trigger | `onTrue` | Decrease launcher speed (-5%) |
| Right bumper | `onTrue` | Nudge hood up |
| Right trigger | `onTrue` | Nudge hood down |

The manual launcher and hood controls exist for two purposes:
- **Testing** — verify mechanisms work before enabling the auto shooter
- **Emergency override** — if the auto shooter fails during a match, the operator can aim and shoot manually

---

## 3. Manual Override Design

The manual controls need mutable state — the launcher speed can be adjusted while it's running, and the hood position accumulates nudges over multiple presses.

### Mutable State in a Closure

The `configure_operator` function creates a `state` dict that lives as long as the bindings do:

```python
def configure_operator(operator, conveyor, turret, launcher, hood, vision):
    state = {
        "launcher_rps": CON_MANUAL["launcher_default_rps"],
        "hood_position": CON_MANUAL["hood_default_position"],
    }
    # ... bindings reference `state` via closures
```

### Dynamic Launcher Speed

The A button toggles a command that reads from `state["launcher_rps"]` each cycle. The bumper/trigger adjust that value. The running command picks up the new speed on its next execute:

```python
# A button toggles the launcher — reads speed each cycle
operator.a().toggleOnTrue(
    _LauncherToggleCommand(launcher, lambda: state["launcher_rps"])
)

# Bumper/trigger adjust speed — no subsystem requirement, won't interrupt
operator.leftBumper().onTrue(
    InstantCommand(lambda: adjust_launcher_rps(state, step))
)
```

The speed adjustment uses `InstantCommand` with **no subsystem requirement**. This is critical — it means pressing the bumper changes the speed variable without interrupting the running launcher command. The launcher command reads the updated value on its next cycle.

### Hood Nudge

Each press of right bumper/trigger nudges the hood by a small increment. The state tracks the accumulated position:

```python
operator.rightBumper().onTrue(
    hood.runOnce(lambda: nudge_hood(state, hood_step, hood))
)
```

This uses `hood.runOnce()`, which **does** require the hood subsystem. After the instant command ends, the Phoenix 6 firmware holds the new position — no running command needed.

---

## 4. How Overrides Interact with Auto Shooter

The auto shooter (`ShooterOrchestrator`) requires turret + launcher + hood. Manual controls interact with it through the WPILib requirement system:

| Action | What Happens |
|--------|-------------|
| Auto running, press A (launcher toggle) | Launcher requires launcher subsystem → cancels auto shooter |
| Auto running, press right bumper (hood nudge) | Hood requires hood subsystem → cancels auto shooter |
| Auto running, push left stick (manual turret) | Turret requires turret subsystem → cancels auto shooter |
| Manual launcher running, press Y (auto shooter) | Auto requires all three → cancels manual launcher |
| Press left bumper (speed adjust) | No requirement → nothing interrupted |

This is intentional:
- **During testing:** Auto shooter is off, manual controls work independently
- **During a match:** Auto shooter runs normally; any manual input cancels it as an emergency override
- **To return to auto:** Press Y again to re-enable

The speed adjustment (left bumper/trigger) is the exception — it changes a variable without requiring a subsystem, so it never interrupts anything. You can pre-set the launcher speed before toggling it on with A.

---

**See also:**
- [Shooter System](shooter-system.md) - How the auto shooter orchestrates subsystems
- [Commands & Controls](commands-and-controls.md) - Button binding patterns and command lifecycle
- [Hardware & Subsystems](hardware-and-subsystems.md) - Subsystem template
