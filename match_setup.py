"""
Match setup -- alliance from Driver Station, pose chooser on Elastic.

Alliance color is read live from the Driver Station (set by FMS during
competition, or manually in the DS app during practice). Changes take
effect immediately -- no restart needed.

The starting pose is still a SendableChooser on Elastic.
"""

from wpilib import DriverStation, SendableChooser, SmartDashboard

from constants.match import ALLIANCES, DEFAULT_ALLIANCE
from utils.logger import get_logger

_log = get_logger("match_setup")


def _find_default(items):
    """Return the first item with 'default': True, or the first item."""
    for item in items:
        if item.get("default"):
            return item
    return items[0]


class MatchSetup:
    """Reads alliance from DS, publishes pose chooser, provides config."""

    def __init__(self):
        self._update_cycle = 0
        self._last_alliance_name = None

        # --- Pose chooser ---
        self._pose_chooser = SendableChooser()
        default_pose = _find_default(
            ALLIANCES[DEFAULT_ALLIANCE]["poses"])
        pose_names_added = set()
        for alliance in ALLIANCES.values():
            for pose in alliance["poses"]:
                if pose["name"] not in pose_names_added:
                    if pose["name"] == default_pose["name"]:
                        self._pose_chooser.setDefaultOption(
                            pose["name"], pose["name"]
                        )
                    else:
                        self._pose_chooser.addOption(
                            pose["name"], pose["name"]
                        )
                    pose_names_added.add(pose["name"])
        SmartDashboard.putData("Starting Pose", self._pose_chooser)

        _log.info("Pose chooser published to SmartDashboard")

    def get_alliance(self) -> dict:
        """Return the alliance dict based on the DS setting.

        Reads DriverStation.getAlliance() every call so changes in
        the DS take effect immediately. Falls back to DEFAULT_ALLIANCE
        if the DS hasn't connected yet.
        """
        ds_color = DriverStation.getAlliance()
        if ds_color == DriverStation.Alliance.kRed:
            return ALLIANCES["Red"]
        elif ds_color == DriverStation.Alliance.kBlue:
            return ALLIANCES["Blue"]
        return ALLIANCES[DEFAULT_ALLIANCE]

    def get_pose_name(self) -> str:
        """Return the currently selected pose name."""
        return self._pose_chooser.getSelected()

    def get_pose(self) -> dict:
        """Return the full pose dict for the selected alliance + pose."""
        alliance = self.get_alliance()
        pose_name = self.get_pose_name()
        _log.info(f"get_pose: alliance='{alliance['name']}' pose='{pose_name}'")
        for pose in alliance["poses"]:
            if pose["name"] == pose_name:
                _log.info(
                    f"get_pose: resolved -> x={pose['start_x']} "
                    f"y={pose['start_y']} heading={pose['start_heading']} "
                    f"path='{pose.get('auto_path', 'none')}'"
                )
                return pose
        _log.warning(
            f"get_pose: pose '{pose_name}' not found in alliance "
            f"'{alliance['name']}' -- using first pose"
        )
        return alliance["poses"][0]

    def get_tag_priority(self) -> list[int]:
        """Return the ordered tag list for the selected alliance."""
        return self.get_alliance()["tag_priority"]

    def update(self):
        """Publish alliance indicator while disabled (pre-match only)."""
        if DriverStation.isEnabled():
            return
        self._update_cycle += 1
        if self._update_cycle % 50 != 1:
            return
        alliance = self.get_alliance()
        is_red = alliance["name"] == "Red"
        SmartDashboard.putBoolean("Match/Is Red Alliance", is_red)
        # Log once when alliance changes so drive team can confirm
        if alliance["name"] != self._last_alliance_name:
            _log.info(f"Alliance from DS: {alliance['name']}")
            self._last_alliance_name = alliance["name"]
        pose_name = self.get_pose_name()
        SmartDashboard.putString("Match/Auto Routine", f"Auto {alliance['name']} {pose_name}")
