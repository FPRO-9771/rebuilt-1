"""
Match setup constants.
Alliance color, starting pose, and Hub target positions.

Alliance color comes from the Driver Station (FMS or manual setting).
The kids select the starting pose on Elastic before each match.
That selection determines which Hub the auto-aimer targets.

To add a pose, just add a dict to the "poses" list below.
"""

# =============================================================================
# ALLIANCES
# =============================================================================
# Each alliance defines its Hub target position (field coordinates, meters).
# target_x, target_y: center of the alliance's Hub on the field.
#   Origin (0, 0) = bottom-left corner (blue driver station right corner).
#   X = toward red alliance wall, Y = toward left side of blue driver station.
# tag_priority: ordered list of AprilTags for vision-based distance lookup
#   (used by ShootWhenReady, not by turret aiming).
#
# TODO: Replace with measured 2026 Hub coordinates from the game manual.
ALLIANCES = {
    "Red": {
        "name": "Red",
        "target_x": 12.0,
        "target_y": 4.0,
        "tag_priority": [8, 10, 11],
        "poses": [
            {
                "name": "Center",
                "default": True,
                "start_x": 13.0,
                "start_y": 4.0,
                "start_heading": 180.0,
                "auto_path": "TEST PATH FPRO",
            },
            {
                "name": "Left",
                "start_x": 0.0,
                "start_y": 0.0,
                "start_heading": 180.0,
                "auto_path": "",
            },
            {
                "name": "Right",
                "start_x": 0.0,
                "start_y": 0.0,
                "start_heading": 180.0,
                "auto_path": "",
            },
        ],
    },
    "Blue": {
        "name": "Blue",
        "target_x": 4.6,
        "target_y": 4.0,
        "tag_priority": [25, 26, 24, 27],
        "poses": [
            {
                "name": "Center",
                "default": True,
                "start_x": 3.6,
                "start_y": 4.0,
                "start_heading": 0.0,
                "auto_path": "",
            },
            {
                "name": "Left",
                "start_x": 0.0,
                "start_y": 0.0,
                "start_heading": 0.0,
                "auto_path": "",
            },
            {
                "name": "Right",
                "start_x": 0.0,
                "start_y": 0.0,
                "start_heading": 0.0,
                "auto_path": "",
            },
        ],
    },
}

# Default alliance when the DS hasn't connected yet.
DEFAULT_ALLIANCE = "Red"

# =============================================================================
# MANUAL HUB RESET POSES
# =============================================================================
# "When all else fails" odometry reset. The driver drives to the front of
# their alliance's Hub, centers the robot, and presses A to hard-reset
# odometry to these known coordinates.
#
# Measure X/Y from the field origin (blue driver station right corner).
# Heading: 0 for blue (facing red wall), 180 for red (facing blue wall).
HUB_RESET_POSES = {
    "Blue": {"x": 4.6, "y": 4.0, "heading": 0.0},
    "Red":  {"x": 12.0, "y": 4.0, "heading": 180.0},
}
