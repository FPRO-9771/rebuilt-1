# Swerve Drivetrain Setup

**Team 9771 FPRO - 2026**

This doc covers the Phoenix 6 swerve drivetrain -- how it was generated, where the files live, and how it integrates with the rest of the codebase.

> **When to read this:** You're debugging the drivetrain, re-running Tuner X, or trying to understand how swerve fits into the project.

---

## File Layout

| File | What it is | Edit by hand? |
|------|-----------|---------------|
| `generated/tuner_constants.py` | Swerve constants (CAN IDs, PID gains, gear ratios, module positions) | **No** -- regenerate with Tuner X |
| `subsystems/command_swerve_drivetrain.py` | Swerve subsystem (WPILib Subsystem + Phoenix SwerveDrivetrain) | **No** -- regenerate with Tuner X |
| `controls/driver_controls.py` | Driver button bindings and swerve requests | Yes |
| `telemetry/swerve_telemetry.py` | Swerve-specific NetworkTables + SignalLogger telemetry | Yes |

---

## Phoenix Tuner X Workflow

1. **Configure each module in Phoenix Tuner X:**
   - Set CAN IDs for drive motor, steer motor, CANcoder
   - Calibrate CANcoder offset (wheels straight forward)

2. **Use Swerve Generator:**
   - Enter physical dimensions (module positions in inches from center)
   - Enter gear ratios, wheel radius, slip current
   - Click "Generate Constants" -- save to `generated/tuner_constants.py`
   - Click "Generate Project" -- copy `subsystems/command_swerve_drivetrain.py` from the output

3. **Don't edit the generated files by hand.** If you need to change CAN IDs, offsets, or gains, re-run the generator in Tuner X and replace the files.

---

## How It Fits Together

```
TunerConstants (generated)
    |
    +-- create_drivetrain() --> CommandSwerveDrivetrain (generated)
                                    |
                                    +-- Subsystem (WPILib commands)
                                    +-- TunerSwerveDrivetrain (Phoenix 6 swerve)
                                    +-- SysId routines
                                    +-- Sim thread (4ms loop)

robot_container.py
    |
    +-- self.drivetrain = TunerConstants.create_drivetrain()
    +-- configure_driver(self.driver, self.drivetrain)
            |
            +-- Field-centric drive (default command)
            +-- Brake, point wheels, reset heading
            +-- SysId bindings
            +-- SwerveTelemetry registration
```

---

## Key Details

### Alliance Perspective

The drivetrain automatically detects alliance color and adjusts the "forward" direction:
- **Blue alliance:** 0 degrees (toward red wall)
- **Red alliance:** 180 degrees (toward blue wall)

This is handled in `CommandSwerveDrivetrain.periodic()`. No driver input needed.

### Simulation

In simulation, a separate thread runs at 4ms (250Hz) to update the swerve model. This makes PID gains behave more realistically than the default 20ms robot loop. The sim thread is started automatically when `utils.is_simulation()` is True.

### Swerve Telemetry

`SwerveTelemetry` publishes to two places:
- **NetworkTables** (`DriveState/` table) -- pose, speeds, module states, odometry frequency
- **SignalLogger** (hoot log files) -- same data for post-match analysis

It also publishes a `Field2d` widget and per-module `Mechanism2d` visualizations to SmartDashboard.

### Vision Integration

`CommandSwerveDrivetrain` provides three methods for Limelight MegaTag2 odometry corrections, all of which iterate over every camera defined in `CON_VISION`:

- **`vision_pose_correct()`** -- soft, Kalman-blended. Reads **MT2** from every Limelight that currently sees tags and feeds each estimate into `add_vision_measurement()`. Called automatically from `periodic()` every `VISION_POSE_CORRECT_PERIOD_LOOPS` loops (default: every loop, ~50 Hz), and also from the auton `CorrectOdometry` PathPlanner named command. Honors the `VISION_POSE_CORRECT_ENABLED` kill switch.
- **`vision_pose_reset_request()`** -- hard. Arms a one-shot flag that `periodic()` services on the next loop a camera satisfies the MT1 tag-count requirement (default 2 tags). Reads **MT1** (gyro-independent) and overrides the **full** pose -- X, Y, AND yaw -- so it can escape gyro drift. Bound to the driver B button as an escape hatch.
- **`_vision_pose_read_mt1()`** -- private helper for the hard reset. Returns the best `(camera_key, PoseEstimate)` MT1 tuple across all cameras, requiring `LIMELIGHT_RESET_MIN_TAGS` tags.

See `docs/architecture/vision.md` for the full flow and tuning knobs.

---

## Our Robot's Config

From `generated/tuner_constants.py`:

| Parameter | Value |
|-----------|-------|
| Swerve module | WCP Swerve X2c (X3 ratio set, 12t pinion) |
| Max speed at 12V | 5.72 m/s |
| Drive gear ratio | 5.4:1 |
| Steer gear ratio | 12.1:1 |
| Wheel radius | 2.0 in (4" OD WCP Molded Wheel Hub, High-Grip tread) |
| Slip current | 120 A |
| Pigeon 2 ID | 10 |
| Module spacing | 20 in x 26 in (center to center) |

### Module CAN IDs

| Module | Drive | Steer | Encoder |
|--------|-------|-------|---------|
| Front Left | 1 | 2 | 11 |
| Back Left | 3 | 4 | 12 |
| Back Right | 5 | 6 | 13 |
| Front Right | 7 | 8 | 14 |

---

**See also:**
- [Controls](controls.md) - Driver and operator button maps
- [Commands & Controls](commands-and-controls.md) - Command-based architecture
- [Testing & Simulation](testing-and-simulation.md) - Running the sim
- [Drive Team Guide](../drive-team-guide.md) - Printable button reference
