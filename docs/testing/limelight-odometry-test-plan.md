# Limelight MegaTag2 Odometry Reset -- Test Plan

## What you need

- Robot powered on with Limelight 4 ("limelight-shooter") connected
- At least one AprilTag visible to the Limelight
- Driver Station + Shuffleboard/SmartDashboard open
- Driver Xbox controller plugged in

## SmartDashboard keys to watch

Open Shuffleboard and add these keys (all under the `Limelight/` prefix):

| Key | Type | What it tells you |
|-----|------|-------------------|
| `Limelight/Tag Visible` | Boolean | Is the Limelight seeing any tags right now? |
| `Limelight/Tag Count` | Number | How many tags it sees |
| `Limelight/Reset Enabled` | Boolean | Is the B-button toggle on or off? |
| `Limelight/Reset Applied` | Boolean | Did a correction actually happen this loop? |
| `Limelight/EstPose X` | Number | Current odometry X (meters) |
| `Limelight/EstPose Y` | Number | Current odometry Y (meters) |
| `Limelight/EstPose Rot` | Number | Current odometry rotation (degrees) |
| `Limelight/MT2 Pose X` | Number | Raw Limelight MegaTag2 X (meters) |
| `Limelight/MT2 Pose Y` | Number | Raw Limelight MegaTag2 Y (meters) |
| `Limelight/MT2 Pose Rot` | Number | Raw Limelight MegaTag2 rotation (degrees) |
| `Limelight/Latency ms` | Number | Limelight pipeline latency |

## Test 1: Verify dashboard keys appear

1. Deploy code and enable the robot (teleop)
2. Open Shuffleboard
3. **Check:** All 11 keys above should appear under `Limelight/`
4. **Check:** `Reset Enabled` should be `false` (default off)
5. **Check:** `Reset Applied` should be `false`

**If keys don't appear:** The drivetrain periodic isn't running. Check for import errors in the console.

## Test 2: Verify tag detection

1. Point the Limelight at an AprilTag
2. **Check:** `Tag Visible` goes `true`, `Tag Count` shows >= 1
3. **Check:** `MT2 Pose X/Y/Rot` show non-zero values that look reasonable
4. Block the camera or point away from tags
5. **Check:** `Tag Visible` goes `false`, `Tag Count` shows 0

**If Tag Visible never goes true:** Check that the Limelight's NT name is exactly `limelight-shooter` in the Limelight web UI. Also check that pipeline 0 is set to AprilTag detection.

## Test 3: Toggle on/off with B button

1. Press **B** on the driver controller
2. **Check:** `Reset Enabled` flips to `true`
3. Press **B** again
4. **Check:** `Reset Enabled` flips back to `false`
5. Check the console/Driver Station for log messages like `Limelight odometry reset ENABLED` / `DISABLED`

## Test 4: Odometry correction works

This is the main test. You need at least one visible AprilTag.

1. With the robot disabled, note the `EstPose X/Y/Rot` values
2. Enable teleop
3. Drive the robot around for 10-15 seconds, then stop
4. Note the `EstPose` values -- this is pure wheel odometry (may have drifted)
5. Note the `MT2 Pose` values -- this is what the Limelight thinks the pose is
6. Press **B** to enable the reset
7. **Check:** `Reset Enabled` goes `true`
8. **Check:** `Reset Applied` goes `true` (only if `Tag Visible` is also `true`)
9. **Watch:** `EstPose X/Y/Rot` should gradually move toward `MT2 Pose X/Y/Rot`
10. Press **B** again to disable
11. **Check:** `EstPose` values stay where they are (corrections are NOT undone)

## Test 5: No correction without tags

1. Press **B** to enable the reset
2. Block the camera or point away from all tags
3. **Check:** `Tag Visible` is `false`
4. **Check:** `Reset Applied` stays `false` even though `Reset Enabled` is `true`
5. Unblock the camera so tags are visible again
6. **Check:** `Reset Applied` goes `true`

## Test 6: Drive behavior unchanged

1. With reset disabled, drive the robot around -- confirm normal driving works
2. Enable the reset (press B), drive around again
3. **Check:** Driving feels exactly the same -- speed, turning, field-centric all unchanged
4. The only difference should be that `EstPose` values are being corrected

## Test 7: Gyro heading sent to Limelight

This verifies `SetRobotOrientation` is working (needed for MegaTag2 accuracy).

1. In the Limelight web UI, check the "Robot Orientation" display
2. Rotate the robot by hand
3. **Check:** The orientation value updates in the Limelight UI, matching the Pigeon2 yaw

## Troubleshooting

| Problem | Likely cause | Fix |
|---------|-------------|-----|
| No SmartDashboard keys at all | Import error in drivetrain | Check console for `ImportError` |
| `Tag Visible` always false | Wrong NT name or wrong pipeline | Verify `limelight-shooter` name and pipeline 0 = AprilTag |
| `MT2 Pose` values look wrong | Field origin mismatch | Limelight must be set to Blue origin in the web UI |
| `Reset Applied` true but `EstPose` doesn't change | Pose values already close | Drive further away from tags, then come back |
| `Latency ms` very high (>100) | Limelight overloaded | Reduce resolution or check USB bandwidth |
| B button does nothing | Controller port wrong | Check `CON_ROBOT["driver_controller_port"]` matches your controller |

## Console logging

If `DEBUG["verbose"]` is enabled, you'll also see console messages like:

```
[drivetrain] MT2 reset applied: x=1.23 y=4.56 rot=90.0 tags=2
[drivetrain] Limelight odometry reset ENABLED
[drivetrain] Limelight odometry reset DISABLED
```

The toggle messages (`ENABLED`/`DISABLED`) always print. The per-loop reset messages only print at debug level.
