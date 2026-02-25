"""
Vision telemetry publisher.
Publishes per-camera Limelight AprilTag data to SmartDashboard.
"""

import wpilib

from utils.logger import get_logger

_log = get_logger("vision_telemetry")


class VisionTelemetry:
    """Publishes vision target data for each camera with prefixed keys."""

    _LOG_EVERY_N = 250  # log once per ~5 seconds at 50 Hz
    _MAX_TAG_SLOTS = 4  # max tags shown on dashboard per camera

    def __init__(self, cameras: dict):
        self._cameras = cameras
        self._cycle = 0

    def update(self):
        """Publish current vision data to SmartDashboard."""
        sd = wpilib.SmartDashboard
        self._cycle += 1
        should_log = False
        # should_log = self._cycle % self._LOG_EVERY_N == 0

        if should_log:
            _log.debug("---- vision telemetry start ----")

        for name, vision in self._cameras.items():
            prefix = f"Vision/{name.title()}"

            targets = vision.get_all_targets()
            has_target = len(targets) > 0

            if should_log:
                _log.debug(
                    f"{prefix}: {len(targets)} target(s), "
                    f"has_target={has_target}"
                )
                for t in targets:
                    _log.debug(
                        f"  tag {t.tag_id}: tx={t.tx:.1f} ty={t.ty:.1f} "
                        f"dist={t.distance:.2f} yaw={t.yaw:.1f}"
                    )

            sd.putBoolean(f"{prefix}/Has Target", has_target)
            sd.putNumber(f"{prefix}/Tag Count", len(targets))

            # Publish each tag to its own key; clear unused slots
            for i in range(self._MAX_TAG_SLOTS):
                key = f"{prefix}/Tag {i + 1}"
                if i < len(targets):
                    t = targets[i]
                    val = (
                        f"ID {t.tag_id}: tx={t.tx:.1f} ty={t.ty:.1f} "
                        f"dist={t.distance:.1f}m yaw={t.yaw:.1f}"
                    )
                else:
                    val = ""
                sd.putString(key, val)
            if should_log:
                _log.debug(
                    f"{prefix}/Tags: {len(targets)} published, "
                    f"{max(0, self._MAX_TAG_SLOTS - len(targets))} cleared"
                )

        if should_log:
            _log.debug("---- vision telemetry end ----")
