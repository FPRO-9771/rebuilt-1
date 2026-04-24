"""
ResyncTurret: in-match recalibration for turret drift.

The operator manually lines up the turret on the Hub (left stick X),
then presses the Resync button. This command reads the current robot
pose and Hub position, computes the turret angular error at the
current motor position, and folds that error into a runtime offset
on CON_POSE["center_position"]. Subsequent CoordinateAim cycles use
the adjusted center, snapping the aim back on target.

Cause-agnostic: corrects for encoder slip, odometry drift, or a
slightly mis-tuned center_position. One-shot and non-blocking --
does not require the turret subsystem, so it runs alongside manual
aim or CoordinateAim.
"""

from typing import Callable, Optional

from commands2 import InstantCommand

from calculations.shooter_position import get_shooter_field_position
from calculations.target_state import compute_target_state
from constants.pose import CON_POSE
from utils.logger import get_logger

_log = get_logger("resync_turret")


class ResyncTurret(InstantCommand):
    """Recalibrate the turret's effective center to the current aim."""

    def __init__(
        self,
        turret,
        pose_supplier: Callable,
        alliance_supplier: Callable,
        coord_aim=None,
    ):
        """
        Args:
            turret: turret subsystem (must expose get/set_center_position_offset
                    and get_effective_center_position)
            pose_supplier: callable returning robot Pose2d
            alliance_supplier: callable returning the alliance dict
                               (must have "target_x", "target_y")
            coord_aim: optional CoordinateAim instance; when provided its
                       filter + I accumulator are cleared so it does not
                       lurch on residual windup.
        """
        super().__init__(self._resync)
        self._turret = turret
        self._pose_supplier = pose_supplier
        self._alliance_supplier = alliance_supplier
        self._coord_aim = coord_aim

    def _resync(self) -> None:
        pose = self._pose_supplier()
        shooter_xy = get_shooter_field_position(
            pose,
            CON_POSE["shooter_offset_x"],
            CON_POSE["shooter_offset_y"],
        )
        alliance = self._alliance_supplier()
        hub_xy = (alliance["target_x"], alliance["target_y"])
        deg_per_rot = CON_POSE["degrees_per_rotation"]

        # Measure the current aim error with zero velocity (no lead).
        state = compute_target_state(
            pose.rotation().degrees(),
            shooter_xy,
            hub_xy,
            (0.0, 0.0),
            self._turret.get_position(),
            self._turret.get_effective_center_position(),
            deg_per_rot,
        )

        # Fold the current error into the offset so the next target_state
        # call returns error_deg = 0 for the same motor position.
        old_offset = self._turret.get_center_position_offset()
        delta = state.error_deg / deg_per_rot
        new_offset = old_offset + delta
        self._turret.set_center_position_offset(new_offset)

        if self._coord_aim is not None:
            self._coord_aim.reset_state()

        new_offset_deg = new_offset * deg_per_rot
        _log.warning(
            f"Turret resync: corrected {state.error_deg:+.2f} deg, "
            f"offset now {new_offset_deg:+.2f} deg "
            f"(pose=({pose.X():.2f},{pose.Y():.2f}) "
            f"hub=({hub_xy[0]:.2f},{hub_xy[1]:.2f}))"
        )

    # InstantCommand runs in the scheduler without requirements, so it
    # fires while CoordinateAim or manual aim is active.
