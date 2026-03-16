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
# tag_offsets: where each tag is relative to the Hub center.
#   Uses field coordinates:
#     Y axis: driver station wall = 0, positive = deeper into field.
#     X axis: positive = right, negative = left (from driver station).
#   Tags are always closer to the wall than the Hub, so tag_y_offset_m
#   is always negative.
#
#   tag_y_offset_m: tag's Y position relative to Hub center (meters).
#     Negative = tag is closer to driver station than Hub.
#   tag_x_offset_m: tag's X position relative to Hub center (meters).
#     Positive = tag is to the right of Hub, negative = to the left.
#
#   Used for parallax correction -- computing the angle between
#   "pointing at tag" and "pointing at Hub center" from the robot's
#   position. Set parallax_correction_enabled in CON_SHOOTER to use.
#
# TODO: Measure real offsets on the 2026 field.
ALLIANCES = [
    {
        "name": "Red",
        "default": True,
        "tag_priority": [8, 10, 11],
        "tag_offsets": {
            8: {"tag_y_offset_m": -0.4, "tag_x_offset_m": -0.4},
            10: {"tag_y_offset_m": -0.6, "tag_x_offset_m": 0.0},
            11: {"tag_y_offset_m": -0.4, "tag_x_offset_m": 0.4},
        },
        "poses": [
            {
                "name": "Center",
                "default": True,
                "start_x": 13.0,
                "start_y": 4.0,
                "start_heading": 0.0,
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
        "tag_priority": [25, 26, 24, 27],
        "tag_offsets": {
            24: {"tag_y_offset_m": -0.4, "tag_x_offset_m": -0.4},
            25: {"tag_y_offset_m": -0.6, "tag_x_offset_m": 0.0},
            26: {"tag_y_offset_m": -0.6, "tag_x_offset_m": 0.0},
            27: {"tag_y_offset_m": -0.4, "tag_x_offset_m": 0.4},
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
