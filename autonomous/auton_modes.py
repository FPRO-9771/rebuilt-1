"""
Autonomous mode factory.

Loads pre-built .auto files from PathPlanner. Each .auto file defines
the full command composition (AimStart, path following with event
markers, ShooterStart, waits, etc.) -- see deploy/pathplanner/autos/.

Named commands must be registered BEFORE this class is constructed
(see autonomous/named_commands.py).

All .auto files are pre-loaded at construction time (during robotInit)
so autonomousInit does a dict lookup instead of file I/O.
"""

from typing import Optional

from commands2 import Command, WaitCommand
from pathplannerlib.auto import AutoBuilder, PathPlannerAuto
from pathplannerlib.util import FlippingUtil
from wpimath.geometry import Pose2d

from constants.debug import DEBUG
from utils.logger import get_logger

_log = get_logger("auton_modes")

# Every .auto file we might use. Pre-loaded at construction so the
# expensive file I/O happens during robotInit, NOT during the
# 20-second auto period.
_ALL_AUTO_NAMES = [
    "Auto Blue Left", "Auto Blue Center", "Auto Blue Center Depot", "Auto Blue Center 2", "Auto Blue Right",
    "Mini Test",
]


class AutonModes:
    """
    Factory for autonomous routines.
    Each routine is a PathPlannerAuto loaded from a .auto file.
    """

    def __init__(self, **kwargs):
        # Validate all .auto files at construction (during robotInit).
        # This catches missing/broken files early, before the match starts.
        # We do NOT cache the command objects -- they are single-use.
        for name in _ALL_AUTO_NAMES:
            try:
                AutoBuilder.buildAuto(name)
                _log.info(f"validated auto '{name}' OK")
            except Exception as e:
                _log.warning(f"could not validate auto '{name}': {e}")

    def do_nothing(self) -> Command:
        """Auto that does nothing -- safe default."""
        _log.info("do_nothing: auto routine selected -- waiting 15s")
        return WaitCommand(15.0)

    def get_starting_pose(self, pose_name: str) -> Optional[Pose2d]:
        """Return the starting pose for the selected routine, alliance-flipped.

        Reads the first waypoint of the first path in "Auto Blue <pose_name>"
        via PathPlannerLib -- PathPlanner stays the single source of truth for
        starting positions. If the DS alliance is Red, FlippingUtil mirrors
        the pose, matching what AutoBuilder does when it actually runs the
        auto. Returns None on any failure so callers can skip the reset
        instead of crashing autonomousInit.
        """
        auto_name = f"Auto Blue {pose_name}"
        try:
            paths = PathPlannerAuto.getPathGroupFromAutoFile(auto_name)
            if not paths:
                _log.warning(f"get_starting_pose: '{auto_name}' has no paths")
                return None
            start = paths[0].getStartingHolonomicPose()
            if start is None:
                _log.warning(
                    f"get_starting_pose: '{auto_name}' first path has no holonomic start"
                )
                return None
            if AutoBuilder.shouldFlip():
                start = FlippingUtil.flipFieldPose(start)
            return start
        except Exception as e:
            _log.warning(f"get_starting_pose: failed to read '{auto_name}': {e}")
            return None

    def get_auto_command(self, alliance_name: str, pose_name: str) -> Command:
        """
        Return the auto routine for the given alliance + starting pose.

        Args:
            alliance_name: "Blue" or "Red"
            pose_name: "Left", "Center", or "Right"
        """
        # Always load Blue paths -- PathPlanner flips them for Red.
        auto_name = f"Auto Blue {pose_name}"
        return self._load_auto(auto_name)

    def mini_test(self) -> Command:
        """Test routine -- Mini Test path."""
        return self._load_auto("Mini Test")

    def _load_auto(self, auto_name: str) -> Command:
        """Build a fresh auto command each time.

        WPILib commands are single-use -- a finished command immediately
        exits if re-scheduled.  So we must call buildAuto() every time,
        not return a cached instance.  The .auto files were already read
        from disk during __init__; buildAuto() is fast on repeat calls.
        """
        _log.info(f"auto '{auto_name}' selected")
        if DEBUG["auto_sequence_logging"]:
            _log.info(f"AUTO SEQ: building '{auto_name}'")
        try:
            return AutoBuilder.buildAuto(auto_name)
        except Exception as e:
            _log.error(f"FAILED to load auto '{auto_name}': {e}")
            return WaitCommand(15.0)
