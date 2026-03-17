"""
Match setup constants.
Alliance color, starting pose, and Hub target positions.

The kids select alliance + pose on Elastic before each match.
That selection determines which Hub the auto-aimer targets.

To add an alliance or pose, just add a dict to the list below.
The first entry with "default": True is pre-selected in SmartDashboard.
"""

# =============================================================================
# ALLIANCES
# =============================================================================
# Each alliance defines its Hub target position (field coordinates, meters).
# target_x, target_y: center of the alliance's Hub on the field.
#   Origin (0, 0) = bottom-left corner (blue driver station right corner).
#   X = toward red alliance wall, Y = toward left side of blue driver station.
# tag_priority: ordered list of AprilTags for vision-based distance lookup
#   (used by AutoShoot, not by turret aiming).
#
# TODO: Replace with measured 2026 Hub coordinates from the game manual.
ALLIANCES = [
    {
        "name": "Red",
        "default": True,
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
    {
        "name": "Blue",
        "target_x": 4.6,
        "target_y": 4.0,
        "tag_priority": [25, 26, 24, 27],
        "poses": [
            {
                "name": "Center",
                "default": True,
                "start_x": 0.0,
                "start_y": 0.0,
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
]
