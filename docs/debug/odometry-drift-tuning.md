# Odometry Drift Tuning Guide

**Team 9771 FPRO - 2026**

Step-by-step procedure for reducing swerve odometry drift. Work through these in order -- each step isolates one variable. You need: a tape measure, masking tape, a straight edge (aluminum bar or level), and a laptop with Phoenix Tuner X.

**Time estimate:** ~45 minutes for all steps.

---

## Before You Start

Open the Shuffleboard/Glass dashboard so you can see live odometry. You need these values visible:

- Robot pose X (meters)
- Robot pose Y (meters)
- Robot heading (degrees)

Reset odometry to a known pose before each test (e.g., X=0, Y=0, heading=0).

---

## Step 1: Wheel Radius Calibration (Do This First)

**Why it matters:** Every distance the robot reports is calculated from wheel rotations. If the wheel radius is wrong, every measurement is scaled wrong -- and the error compounds over distance. This is the single biggest source of drift.

**Our hardware:** WCP Swerve X2c with 4" OD Molded Wheel Hub (WCP-1727) and High-Grip Molded Tread (WCP-1728).

**Current value:** `_wheel_radius = inchesToMeters(2)` (2.0 inches / 4.0 inch diameter) in `generated/tuner_constants.py`. This matches the nominal 4" OD wheel.

> The nominal radius (2.0 in) is correct for our wheels, but the **effective** radius on carpet under robot weight will be slightly smaller because the high-grip tread compresses. It is common to end up with ~1.93-1.97 inches after calibration. The straight-line test below will find the real value.

### Procedure

1. Put a strip of masking tape on the floor, at least 3 meters long
2. Mark a clear start line on the tape
3. Measure exactly **3.00 meters** from the start line and mark the end line
4. Line up the center of the robot's front bumper with the start line
5. Reset odometry to (0, 0, 0)
6. **Drive the robot straight forward slowly** until the front bumper reaches the end line
   - Use low speed -- no jerky movements
   - Keep the robot as straight as possible (watch the heading -- it should stay near 0)
7. Stop and read the odometry X value

### Interpreting Results

| Odometry reads | Wheel radius is | Action |
|----------------|-----------------|--------|
| 3.00 m | Correct | Move to Step 2 |
| More than 3.00 m (e.g., 3.06) | Too large | Decrease wheel radius |
| Less than 3.00 m (e.g., 2.94) | Too small | Increase wheel radius |

### Calculating the Corrected Radius

```
corrected_radius = current_radius * (actual_distance / odometry_distance)
```

**Example:** You drove 3.00 m but odometry says 3.06 m.
```
corrected_radius = 2.0 in * (3.00 / 3.06) = 1.961 in
```

### Applying the Fix

1. Open **Phoenix Tuner X**
2. Go to the **Swerve Generator** tab
3. Update the **Wheel Radius** field with the corrected value
4. Click **Generate Constants**
5. Save the output to `generated/tuner_constants.py`
6. **Repeat the straight-line test** to verify. Target: within 2 cm over 3 meters.

---

## Step 2: CANcoder Offset Verification

**Why it matters:** Each swerve module has a CANcoder that tells the robot which direction the wheel is pointed. If a module's zero position is even slightly off, that wheel pushes the robot a little sideways when it should be going straight. This causes drift that gets worse during turns.

### Current Offsets

| Module | CAN ID | Offset (rotations) |
|--------|--------|---------------------|
| Front Left | 14 | +0.291015625 |
| Front Right | 11 | -0.28759765625 |
| Back Left | 13 | +0.37841796875 |
| Back Right | 12 | -0.039306640625 |

### Procedure

#### A. Physical Alignment

1. **Lift the robot** so all four wheels are off the ground, OR push it to an open area where you can freely turn wheels by hand
2. Get a **straight edge** (aluminum extrusion, level, or long ruler)
3. For each module, manually rotate the wheel so it points perfectly forward
   - Use the straight edge along the side of the robot frame as your reference
   - The wheel should be parallel to the frame rail
   - Be as precise as you can -- even 1-2 degrees matters

#### B. Read Absolute Positions in Tuner X

4. Connect your laptop to the robot (USB or WiFi)
5. Open **Phoenix Tuner X**
6. For each CANcoder (IDs 11, 12, 13, 14):
   - Click the device in the left sidebar
   - Go to the **Device Details** tab (or **Config** tab)
   - Look at **Absolute Position** -- this is the raw reading with wheels pointed straight
   - Write down all four values

#### C. Check Against Current Offsets

The offset should equal the absolute position reading when the wheel is pointed straight forward. If a value has drifted from what is in the config, the module's zero is off.

7. Compare each reading to the current offsets in the table above
8. If any value differs by more than ~0.002 rotations, it needs updating

#### D. Apply Updated Offsets in Tuner X

9. In Phoenix Tuner X, go to the **Swerve Generator** tab
10. Enter the new absolute position values as the **Encoder Offset** for each module
11. Click **Generate Constants**
12. Save the output to `generated/tuner_constants.py`

#### E. Verify

13. Power cycle the robot
14. With the wheels still pointed straight forward, the steer motors should NOT twitch or correct on startup. If a wheel snaps to a slightly different angle, its offset is still wrong.

---

## Step 3: Module Position Measurement

**Why it matters:** The odometry math uses the distance between modules to calculate how rotation translates to position change. If these distances are wrong, driving in curves or rotating creates position drift.

**Current values:** 20 in front-to-back, 26 in left-to-right (center-to-center)

### Procedure

1. Measure the distance between the **center of the front-left wheel contact patch** and the **center of the back-left wheel contact patch**. This is the wheelbase (front-to-back).
   - Measure at the floor where the wheel touches the carpet
   - Should be close to 20 inches
2. Measure the distance between the **center of the front-left wheel contact patch** and the **center of the front-right wheel contact patch**. This is the track width (left-to-right).
   - Should be close to 26 inches
3. If either measurement is off by more than 0.25 inches from the current config:
   - Open Phoenix Tuner X Swerve Generator
   - Update the module X/Y positions (half the measured distance for each axis)
   - Regenerate constants

### Rotation Test (Verifies Module Positions)

4. Place a piece of tape on the floor pointing in the same direction as the robot's front
5. Reset odometry to (0, 0, 0)
6. Rotate the robot **360 degrees in place** (slowly, using rotation-only input)
7. Stop when the robot's front is aligned with the tape again
8. Check odometry:
   - Heading should be ~360 (or ~0 if it wraps). The Pigeon gyro handles heading, so this should be close.
   - **X and Y should still be ~0.** If X or Y drifted more than 5 cm during a pure rotation, the module positions are likely wrong.

---

## Step 4: Gear Ratio Verification

**Why it matters:** A wrong gear ratio has the same effect as a wrong wheel radius -- every distance is scaled incorrectly.

**Our hardware:** WCP Swerve X2c, X3 Ratio Set with 12-tooth pinion.

**Current value:** Drive gear ratio = 5.4:1

### Procedure

1. Physically verify we are running the **X3 Ratio Set** (central gear 54/40, second stage 16t) with a **12-tooth pinion**. That combination gives exactly 5.40:1 per the WCP spec sheet.
2. If the pinion or gear set was swapped at any point, look up the correct ratio from the WCP X2 gear ratio table:

| Ratio Set | Central Gear | 2nd Stage | Pinion 10 | Pinion 11 | Pinion 12 |
|-----------|-------------|-----------|-----------|-----------|-----------|
| X1 | 54/38 | 18t | 7.67 | 6.98 | 6.39 |
| X2 | 54/38 | 16t | 6.82 | 6.20 | 5.68 |
| X3 | 54/40 | 16t | 6.48 | 5.89 | **5.40** |
| X4 | 54/40 | 14t | 5.67 | 5.15 | 4.73 |

3. If the ratio does not match, update it in Tuner X and regenerate
4. The steer (rotation) gear ratio is **12.1:1** for all WCP X2 configurations using 10t pinions -- this should be correct

---

## Step 5: Coupling Ratio Check

**Why it matters:** On most swerve modules, rotating the steering also slightly back-drives the drive motor through gear coupling. Phoenix 6 compensates for this, but only if the coupling ratio is correct. A wrong value creates small distance errors every time a module steers -- which happens constantly during curves.

**Current value:** 4.5:1

This is typically set correctly by Tuner X. If Steps 1-4 fixed your drift, you can skip this. If you still have drift specifically during turns (but straight-line is good), this may need adjustment. Consult your module vendor's documentation for the correct coupling ratio.

---

## Step 6: Full Circle Test (Validation)

After completing the above steps, run the full validation test.

### Procedure

1. Place the robot at a known position, mark it with tape
2. Reset odometry to (0, 0, 0)
3. Drive slowly in a big circle:
   - ~3 m to the left
   - ~3 m forward
   - Continue the circle back to the start
4. Stop at the starting tape mark
5. Read odometry X and Y

### Targets

| Metric | Good | Needs work |
|--------|------|------------|
| X error | < 5 cm | > 10 cm |
| Y error | < 5 cm | > 10 cm |
| Heading error | < 2 degrees | > 5 degrees |

If drift is still significant after tuning all the above, **vision-based pose correction** (Limelight MegaTag) is the next step -- which is what we are building on the `limelight-odometry` branch.

---

## Quick Checklist

- [ ] Step 1: Wheel radius -- drive 3 m straight, check odometry, adjust
- [ ] Step 2: CANcoder offsets -- align wheels, read absolute positions in Tuner X, update
- [ ] Step 3: Module positions -- measure wheel spacing, rotation test
- [ ] Step 4: Gear ratio -- verify against vendor spec sheet
- [ ] Step 5: Coupling ratio -- check if turn drift remains after Steps 1-4
- [ ] Step 6: Full circle validation test
