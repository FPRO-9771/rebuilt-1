"""
Match setup -- SmartDashboard choosers for alliance and starting pose.

Creates SendableChoosers from the ALLIANCES config in constants/match.py.
The kids set these in SmartDashboard/Elastic before each match.
The rest of the code reads the active config at runtime.
"""

from wpilib import DriverStation, SendableChooser, SmartDashboard

from constants.match import ALLIANCES
from utils.logger import get_logger

_log = get_logger("match_setup")


def _find_default(items):
    """Return the first item with 'default': True, or the first item."""
    for item in items:
        if item.get("default"):
            return item
    return items[0]


class MatchSetup:
    """Publishes alliance/pose choosers and provides the active config."""

    def __init__(self):
        # --- Alliance chooser ---
        self._alliance_chooser = SendableChooser()
        default_alliance = _find_default(ALLIANCES)
        for alliance in ALLIANCES:
            if alliance is default_alliance:
                self._alliance_chooser.setDefaultOption(
                    alliance["name"], alliance
                )
            else:
                self._alliance_chooser.addOption(
                    alliance["name"], alliance
                )
        SmartDashboard.putData("Alliance", self._alliance_chooser)
        self._update_cycle = 0

        # --- Pose chooser ---
        # Pose names are the same across alliances (Left/Center/Right),
        # so one chooser works. At runtime we look up the pose by name
        # within the selected alliance.
        self._pose_chooser = SendableChooser()
        default_pose = _find_default(default_alliance["poses"])
        pose_names_added = set()
        for alliance in ALLIANCES:
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

        _log.info("Match choosers published to SmartDashboard")

    def get_alliance(self) -> dict:
        """Return the currently selected alliance dict."""
        return self._alliance_chooser.getSelected()

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
        is_red = self.get_alliance()["name"] == "Red"
        SmartDashboard.putBoolean("Match/Is Red Alliance", is_red)
