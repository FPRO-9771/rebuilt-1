"""
Match setup constants.
Alliance color, starting pose, and per-alliance tag priorities for the shooter.

The kids select alliance + pose on SmartDashboard before each match.
That selection determines which AprilTags the auto-shooter tracks and
in what priority order (first visible tag in the list wins).

To add an alliance or pose, just add a dict to the list below.
The first entry with "default": True is pre-selected in SmartDashboard.
"""

# =============================================================================
# ALLIANCES
# =============================================================================
# Each alliance defines its Hub's scoring AprilTags in priority order.
# tag_priority: ordered list -- orchestrator locks onto the first visible tag.
# tag_offsets: per-tag corrections when aiming at the Hub.
#   tx_offset (degrees): positive = Hub is to the right of this tag
#   distance_offset (meters): positive = Hub is farther than this tag
#   All zeros to start -- tune on the real robot.
#
# TODO: Update tag IDs and offsets for the real 2026 field.
ALLIANCES = [
    {
        "name": "Red",
        "default": True,
        "tag_priority": [8, 9, 10, 11],
        "tag_offsets": {
            8: {"tx_offset": 0.0, "distance_offset": 0.0},
            9: {"tx_offset": 0.0, "distance_offset": 0.0},
            10: {"tx_offset": 0.0, "distance_offset": 0.0},
            11: {"tx_offset": 0.0, "distance_offset": 0.0},
        },
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
    {
        "name": "Blue",
        "tag_priority": [25, 26, 24, 27],
        "tag_offsets": {
            24: {"tx_offset": 0.0, "distance_offset": 0.0},
            25: {"tx_offset": 0.0, "distance_offset": 0.0},
            26: {"tx_offset": 0.0, "distance_offset": 0.0},
            27: {"tx_offset": 0.0, "distance_offset": 0.0},
        },
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

# =============================================================================
# TARGET LOCK BEHAVIOR
# =============================================================================
# How many consecutive cycles a locked tag must be missing before
# the orchestrator unlocks and picks a new one.
# At 50 Hz, 10 cycles = 200 ms of grace period.
TARGET_LOCK_LOST_CYCLES = 10
