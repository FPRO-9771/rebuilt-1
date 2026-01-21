"""
Autonomous-specific configuration.
AprilTag IDs, drive paths, and timing constants.

TODO: Update these values based on 2026 Rebuilt field layout.
"""

# =============================================================================
# APRILTAG IDS BY FIELD POSITION
# =============================================================================
# TODO: Update with actual 2026 Rebuilt AprilTag IDs
APRILTAG_IDS = {
    "blue_left": {"score": 1, "intake": 2},
    "blue_center": {"score": 3},
    "blue_right": {"score": 4, "intake": 5},
    "red_left": {"score": 6, "intake": 7},
    "red_center": {"score": 8},
    "red_right": {"score": 9, "intake": 10},
}

# =============================================================================
# DRIVE PATHS
# =============================================================================
# Each path is a list of (vx, vy, omega, duration) tuples
# vx, vy in m/s, omega in rad/s, duration in seconds
DRIVE_PATHS = {
    "exit_zone": [
        (2.0, 0, 0, 1.5),  # Drive forward at 2 m/s for 1.5 seconds
    ],
    "to_intake": [
        (1.5, 0, 0, 1.0),  # Forward
        (0, 0, 1.5, 0.5),  # Rotate
        (1.0, 0, 0, 0.5),  # Forward again
    ],
}

# =============================================================================
# VISION DATA CALIBRATION
# =============================================================================
# TODO: Calibrate these multipliers on real robot with Limelight mounted
LL_DATA_SETTINGS = {
    "yaw": {"multiplier": 0.115},
    "tx": {"multiplier": 0.222},
    "distance": {},
}

# =============================================================================
# DRIVING BEHAVIOR
# =============================================================================
DRIVING = {
    "speed_x": {
        "max": 3.0,
        "multiplier": 0.5,
        "target_tolerance": 0.3,
    },
    "speed_y": {
        "max": 1.5,
        "multiplier": 0.4,
        "target_tolerance": 0.5,
    },
    "rotation": {
        "max": 0.8,
        "multiplier": 0.2,
        "target_tolerance": 0.08,
    },
}
