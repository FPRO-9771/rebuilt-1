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
