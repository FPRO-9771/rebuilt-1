# Intake & Feed System

**Team 9771 FPRO - 2026**

This doc covers the intake and feed subsystems -- how Fuel gets collected from the field and transported to the launcher.

> **When to read this:** You're working on intake deploy/stow, the intake rollers, or the feed path.

---

## Overview

The intake and feed system has two jobs:

1. **Intake** -- deploy an arm over the bumper, spin rollers to pull Fuel in
2. **Feed** -- move collected Fuel horizontally then vertically up to the launcher

Four subsystems handle this, each owning one motor (except the intake arm which has two):

| Subsystem | File | Motor(s) | CAN ID(s) | Type | Bus |
|-----------|------|----------|-----------|------|-----|
| Intake (arm) | `subsystems/intake.py` | Left + Right | 41, 42 | TalonFX (KrakenX60) | `op_sys` |
| IntakeSpinner | `subsystems/intake_spinner.py` | Spinner | 40 | TalonFX (KrakenX60) | `op_sys` |
| HFeed | `subsystems/h_feed.py` | Horizontal | 22 | TalonFX (KrakenX60) | `op_sys` |
| VFeed | `subsystems/v_feed.py` | Vertical | 23 | TalonFX (KrakenX60) | `op_sys` |

---

## Intake Arm

The intake arm deploys and stows using two independent KrakenX60 motors (left and right), each running their own PID. It uses a **two-phase voltage move** pattern rather than simple position control:

- **Going down:** Phase 1 pushes the arm down (`down_push_voltage: -1.5V`), then phase 2 brakes against gravity (`down_brake_voltage: 0.1V`) so the arm doesn't slam.
- **Going up:** Phase 1 fights gravity hard (`up_fight_voltage: 2.5V`), then phase 2 eases off (`up_ease_voltage: -0.5V`) as the arm approaches vertical.

The transition between phases is controlled by fraction constants (`down_transition_fraction: 0.60`, `up_transition_fraction: 0.35`). Stall detection cuts power if the arm stops moving for ~0.4 seconds during phase 2.

Key positions from `CON_INTAKE`:

- `up_position: 0.0` -- fully raised (stowed)
- `down_position: -4.20` -- fully deployed
- `position_tolerance: 0.06` -- "close enough" in rotations
- `gear_ratio: 15.0` -- 1:15 gearbox

The arm also has a **hold mode** using soft P-control (`hold_kP: 2.0`, `hold_max_voltage: 1.0V`) with a deadband of `0.05` rotations. When the spinner is active, hold voltage is allowed up to `spin_hold_max_voltage: 6.0V` to counteract the reaction force.

## Intake Spinner

The spinner is a single KrakenX60 that pulls Fuel into the robot. It uses simple voltage control:

- `spin_voltage: 5V` -- voltage when actively intaking
- `max_voltage: 12.0V` -- safety clamp

The `RunIntake` command in `commands/run_intake.py` coordinates both subsystems -- it spins the rollers while holding the arm in place with P-control. This command requires both `Intake` and `IntakeSpinner` subsystems.

---

## Feed System

### Horizontal Feed (HFeed)

Moves Fuel horizontally from the intake to the vertical feed. Uses voltage control:

- `feed_voltage: 8.0V` -- forward feeding
- `reverse_voltage: -6.0V` -- reverse to un-jam
- `max_voltage: 10.0V` -- safety clamp

Supports both `run_at_voltage()` for fixed speed and `manual()` for joystick control.

### Vertical Feed (VFeed)

Lifts Fuel vertically from the horizontal feed into the launcher. Uses voltage control:

- `feed_voltage: -7.0V` -- forward feeding (negative because motor is inverted relative to feed direction)
- `max_voltage: 10.0V` -- safety clamp

Same command interface as HFeed (`run_at_voltage()` and `manual()`).

---

## Control Bindings

### Driver Controller (intake)

| Control | Action | Details |
|---------|--------|---------|
| Y button | Toggle intake deploy | Alternates between `go_down()` and `go_up()` |
| Left trigger (hold) | Run intake | `RunIntake` command -- spins rollers + holds arm |

### Operator Controller (feeds)

| Control | Action | Details |
|---------|--------|---------|
| B button (toggle) | Run both feeds | `ParallelCommandGroup` of h_feed + v_feed at feed voltage |
| Right bumper (hold) | Reverse H feed | Runs h_feed at `reverse_voltage` to un-jam (interrupts B toggle) |

---

## Fuel Path

The full flow from field to launcher:

```
Field -> Intake Spinner (pull in) -> HFeed (move horizontal) -> VFeed (move up) -> Launcher
```

The driver controls intake (deploy arm + spin rollers), while the operator controls the feed path (toggle feeds on, reverse if jammed). The two roles are independent -- the driver collects Fuel and the operator manages delivery to the launcher.

---

**See also:**
- [Hardware & Subsystems](hardware-and-subsystems.md) -- Hardware abstraction and subsystem patterns
- [Commands & Controls](commands-and-controls.md) -- Command composition and button bindings
- [Controls](controls.md) -- Full controller binding reference
