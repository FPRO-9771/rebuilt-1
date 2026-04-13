# Controls & Manual Overrides

**Team 9771 FPRO - 2026**

This doc covers how controller bindings are organized to keep `robot_container.py` short, and how the operator's manual and automatic controls work together.

> **When to read this:** You're adding new button bindings, wondering how manual controls interact with auto-aim/auto-shoot, or trying to keep robot_container from growing out of control.

---

## Table of Contents

1. [Binding Extraction Pattern](#1-binding-extraction-pattern)
2. [Driver Control Map](#2-driver-control-map)
3. [Operator Control Map](#3-operator-control-map)
4. [Manual vs Auto Modes](#4-manual-vs-auto-modes)
5. [How Commands Interact](#5-how-commands-interact)

---

## 1. Binding Extraction Pattern

As the robot gains mechanisms, `robot_container.py` grows fast. Every new button binding adds lines. The fix: group bindings by controller role and move them to dedicated modules.

### Before (everything in robot_container)

```python
# robot_container.py -- gets long fast
class RobotContainer:
    def _configure_bindings(self):
        # 10 lines of operator controls...
        # 10 lines of driver controls...
        # More for each new mechanism...
```

### After (one function call per role)

```python
# robot_container.py -- stays short
from controls import configure_driver, configure_operator

class RobotContainer:
    def _configure_bindings(self):
        configure_driver(self.driver, self.drivetrain,
                         intake=self.intake,
                         intake_spinner=self.intake_spinner)
        configure_operator(
            self.operator, None, self.turret,
            self.launcher, self.vision["shooter"],
            self.match_setup, self.h_feed, self.v_feed,
            drivetrain=self.drivetrain,
        )
```

Each binding module receives the controller and subsystems, then wires everything internally. `robot_container.py` doesn't need to know which button does what.

### GameController Wrapper

`controls/game_controller.py` defines a `GameController` class that wraps either a `CommandXboxController` or a `CommandPS4Controller` behind a single, Xbox-style interface. The constructor takes a joystick port and a `use_ps4` flag (read from `CON_ROBOT["use_ps4"]` in `constants/controls.py`). When `use_ps4` is `True`, Xbox-named methods like `a()`, `b()`, `leftBumper()`, and `getLeftTriggerAxis()` delegate to the PS4 equivalents (`cross()`, `circle()`, `L1()`, `getL2Axis()`, etc.). D-pad and stick axes are the same on both controller types and pass straight through.

`robot_container.py` creates one `GameController` per role:

```python
use_ps4 = CON_ROBOT["use_ps4"]
self.driver = GameController(CON_ROBOT["driver_controller_port"], use_ps4)
self.operator = GameController(CON_ROBOT["operator_controller_port"], use_ps4)
```

The binding modules (`driver_controls.py`, `operator_controls.py`) only call Xbox-style methods, so switching to PS4 controllers for simulation requires changing just the one constant -- no binding code needs to change.

### Adding a New Binding

When you add a new control:

1. Edit the appropriate module (`controls/driver_controls.py` or `controls/operator_controls.py`)
2. Add any new constants to `constants/controls.py`
3. If the function signature changes (new subsystem needed), update the call in `robot_container.py`
4. Write tests in the matching test file
5. Update `docs/drive-team-guide.md` so the drive team knows about the new button

---

## 2. Driver Control Map

| Input | Binding | Action |
|-------|---------|--------|
| Left stick | Default command | Drive translation (X = strafe, Y = forward/back) |
| Right stick X | Default command | Rotation |
| A button | `onTrue` | Manual Hub odometry reset (when all else fails) |
| B button | `onTrue` | One-shot Limelight MegaTag2 odometry reset |
| Left bumper | `onTrue` | Reset field-centric heading |
| Right bumper | `onTrue` | Toggle field-centric / robot-centric |
| Y button | `onTrue` | Toggle intake deploy (down/up) |
| Left trigger | `whileTrue` | Run intake (spin rollers + hold arm) |
| Right trigger | axis (default cmd) | Slow mode -- squeeze to cap speed (linear stick, trigger sets ceiling) |
| Back + Y | `whileTrue` | SysId dynamic forward |
| Back + X | `whileTrue` | SysId dynamic reverse |
| Start + Y | `whileTrue` | SysId quasistatic forward |
| Start + X | `whileTrue` | SysId quasistatic reverse |

### Drive Response: Normal vs Slow Mode

The driver has two distinct speed modes, selected by the right trigger:

**Normal mode** (no trigger): Joystick inputs pass through a power curve (`_apply_curve` in `driver_controls.py`) before becoming velocity commands. The exponent is configurable in `constants/controls.py`:

- `drive_exponent` (currently 4.0) -- translation (left stick)
- `rotation_exponent` (currently 5.0) -- rotation (right stick X)

Higher exponents give more fine control at low/mid stick. See `docs/drive-team-guide.md` for a tuning reference table.

**Slow mode** (any trigger squeeze): Stick response is linear (no curve). The trigger controls the speed ceiling -- light squeeze caps at `slow_max_speed` (2.0 m/s), full squeeze caps at `slow_min_speed` (0.5 m/s). Stick position is a simple percentage of that ceiling.

A 3% stick deadband (`stick_deadband`) is applied in both modes to prevent drift.

### Source

- `controls/driver_controls.py` -- all driver bindings
- `generated/tuner_constants.py` -- swerve constants (generated by Tuner X, do not edit by hand)
- `subsystems/command_swerve_drivetrain.py` -- swerve subsystem (generated by Tuner X, do not edit by hand)
- `telemetry/swerve_telemetry.py` -- swerve-specific telemetry publisher

---

## 3. Operator Control Map

| Input | Binding | Action |
|-------|---------|--------|
| Left stick X | `whileTrue` | Manual turret aim |
| Left stick Y | | *unassigned* |
| Right stick Y | (via right trigger) | Launcher speed (stick maps to RPS range) |
| A button | | *unassigned* |
| B button | | *unassigned* |
| X button | | *unassigned* |
| Y button | | *unassigned* |
| Left bumper | `toggleOnTrue` | Coordinate aim (turret aims at Hub via odometry) |
| Left trigger | `whileTrue` | Shoot when ready (launcher + auto-feed when aligned and at speed) |
| Right bumper | `whileTrue` | Reverse all feeds (unjam H feed + V feed + conveyor, interrupts right trigger) |
| Right trigger | `whileTrue` | Manual shoot (launcher + auto-feed when at speed, speed from right stick Y) |
| Start (hold) + Right stick Y | `whileTrue` | Pit-mode intake jog -- low-voltage raise/lower when mechanical locks prevent manual movement |

### Source

- `controls/operator_controls.py` -- all operator bindings
- `commands/manual_shoot.py` -- launcher spin-up + auto-feed when at speed
- `commands/manual_launcher.py` -- stick-to-RPS mapping (fallback when feeds not wired)
- `commands/reverse_feeds.py` -- reverse all feeds to clear jams (shared by manual and auto)
- `commands/coordinate_aim.py` -- odometry-based turret aiming
- `commands/shoot_when_ready.py` -- launcher + auto-feed combo (uses shared unjam logic from reverse_feeds)

---

## 4. Manual vs Auto Modes

The operator can mix manual and automatic controls freely. Each command is independent:

### Always Manual
- **Left stick X** -- turret aim (works regardless of coordinate aim state)
- **Right trigger hold + right stick Y** -- manual shoot (launcher + auto-feed when at speed)
- **Right bumper hold** -- reverse all feeds (unjam)

### Auto Aim
- **Left bumper toggle** -- coordinate aim (turret aims at Hub using odometry)
- **Left trigger hold** -- shoot when ready (launcher + auto-feed when aligned and at speed)

### Typical Workflows

**Full manual:**
1. Use left stick X to aim turret
2. Hold right trigger to spin launcher, use right stick Y to set speed
3. Feeds run automatically when launcher reaches target speed

**Auto aim:**
1. Toggle left bumper to enable coordinate aim (turret tracks Hub)
2. Hold left trigger to shoot when ready (launcher spins, feeds when on target and at speed)

---

## 5. How Commands Interact

Commands interact through the WPILib requirement system:

| Action | What Happens |
|--------|-------------|
| Reverse all feeds (right bumper) + manual shoot (right trigger) | ReverseFeeds requires h_feed + v_feed -> interrupts ManualShoot. Release right bumper, hold right trigger again to resume. |
| Reverse all feeds (right bumper) + shoot when ready (left trigger) | ReverseFeeds requires h_feed + v_feed -> interrupts ShootWhenReady. Release right bumper, hold left trigger again to resume. |
| Manual turret (left stick) + coordinate aim (left bumper) | Both require turret -> manual stick interrupts CoordinateAim. Toggle left bumper again to re-enable. |
| ManualShoot (right trigger) + coordinate aim (left bumper) | Different subsystems (launcher/feeds vs turret) -> both run simultaneously. |
| IntakeSpinner on (driver) + manual shoot (operator) | Both run -- different subsystem requirements (intake_spinner vs launcher/h_feed/v_feed) |

Key principle: commands that require different subsystems can run simultaneously. Commands that require the same subsystem will interrupt each other, with the most recently scheduled command winning.

---

**See also:**
- [Shooter System](shooter-system.md) - How the command modules and distance table work
- [Commands & Controls](commands-and-controls.md) - Button binding patterns and command lifecycle
- [Hardware & Subsystems](hardware-and-subsystems.md) - Subsystem template
