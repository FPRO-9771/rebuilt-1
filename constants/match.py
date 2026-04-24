"""
Match setup constants.
Alliance color, starting pose, and Hub target positions.

Alliance color comes from the Driver Station (FMS or manual setting).
The kids select the starting pose on Elastic before each match.
That selection determines which auto routine runs and which Hub the
auto-aimer targets.

Starting coordinates (x, y, heading) are set by PathPlanner -- each
.auto file has resetOdom: true, so the first waypoint of the first
path becomes the odometry origin. No need to duplicate those here.

To add a pose, just add a dict to _POSES below.
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
# corners: 2026 scoring-zone corners used by Assist mode. When the shooter
#   is inside the neutral zone in teleop, the turret re-targets whichever
#   corner is closest so we can lob Fuel back to our side for later
#   collection.
#
# TODO: Replace with measured 2026 Hub coordinates from the game manual.

# Shared pose list -- both alliances use the same names.
# PathPlanner handles starting coordinates via the path's first waypoint.
_POSES = [
    {"name": "Center", "default": True},
    {"name": "Center Depot"},
    {"name": "Left"},
    {"name": "Right"},
]

ALLIANCES = {
    "Red": {
        "name": "Red",
        "target_x": 12.0,
        "target_y": 4.0,
        "tag_priority": [8, 10, 11],
        "poses": _POSES,
        "corners": [(14, 6), (14, 2)],
    },
    "Blue": {
        "name": "Blue",
        "target_x": 4.6,
        "target_y": 4.0,
        "tag_priority": [25, 26, 24, 27],
        "poses": _POSES,
        "corners": [(2, 6), (2, 2)],
    },
}

# =============================================================================
# NEUTRAL ZONE ASSIST MODE
# =============================================================================
# When the shooter's field X is between these values, we consider the robot
# in the neutral zone. In teleop with auto-aim engaged, the turret switches
# to Assist mode and aims at the closest alliance scoring-zone corner
# instead of the Hub, so we can lob Fuel back to our partners.
NEUTRAL_ZONE_X_MIN = 4.8
NEUTRAL_ZONE_X_MAX = 11.5

# Hysteresis buffer (meters). Once Assist mode is latched, the shooter must
# leave the neutral zone by this much before Hub aim resumes. Prevents
# target flicker when the robot straddles the boundary.
NEUTRAL_ZONE_HYSTERESIS_M = 0.3

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
