"""
Vision system configuration.
Camera list defined once here -- everything else flows from this.

Each camera entry has:
  name     -- human-readable label (shown in CameraServer / dashboards)
  nt_name  -- NetworkTables table name. Must match the name configured
              in the Limelight's web UI, or MegaTag2 will not find it.
  host     -- static IP address. Used for the MJPEG stream URL and for
              reaching the web UI at http://<host>:5801.

Two Limelights point left and right off the back of the robot so that
between them they cover a wide arc for continuous AprilTag-based
odometry corrections.
"""

CON_VISION = {
    "cameras": {
        "left": {
            "name": "Limelight Left",
            "nt_name": "limelight-left",
            "host": "10.97.71.11",
        },
        "right": {
            "name": "Limelight Right",
            "nt_name": "limelight-right",
            "host": "10.97.71.12",
        },
    },
}

# How often vision_pose_correct() runs inside drivetrain.periodic().
# 1 = every loop (~50 Hz), 2 = every other loop (~25 Hz), etc.
# Bump this up if the driver station reports loop overruns.
VISION_POSE_CORRECT_PERIOD_LOOPS = 1

# Master kill switch for the continuous soft pose correction. Flip this
# False between matches if vision is feeding the estimator garbage and
# you want to fly on pure wheel odometry. The B-button hard reset still
# works -- it does not read this flag.
VISION_POSE_CORRECT_ENABLED = True

# How often vision_pose_correct() emits a debug line when
# DEBUG["vision_pose_correct_logging"] is on. 10 = ~5 Hz at a 50 Hz loop.
# Logging is off entirely unless the DEBUG flag is set.
VISION_POSE_LOG_PERIOD_LOOPS = 10

# Which Limelight bot-pose estimate vision_pose_correct() feeds into
# the WPILib pose estimator.
#   "mt2" -- MegaTag2, gyro-fused. Handles single-tag PnP automatically
#            via gyro disambiguation. What most FRC teams use, and the
#            default here.
#   "mt1" -- MegaTag1, pure AprilTag PnP, no gyro. Requires 2+ tags
#            per camera per measurement (single-tag MT1 has unresolved
#            PnP ambiguity). Use when MT2 shows a systematic position
#            bias on your setup that MT1 does not.
# The B-button hard reset always uses MT1 regardless of this setting;
# that is the whole point of the escape hatch.
VISION_POSE_CORRECT_MODE = "mt2"

# Minimum tags per camera when MODE is "mt1". Cameras with fewer tags
# are skipped that loop -- no measurement fed to the estimator. Does
# not apply in "mt2" mode; MT2 uses the gyro to disambiguate single
# tags.
VISION_POSE_CORRECT_MT1_MIN_TAGS = 2
