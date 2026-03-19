"""
Vision telemetry publisher.
Publishes per-camera Limelight AprilTag data to SmartDashboard.
"""

import wpilib


class VisionTelemetry:
    """Publishes vision target data for each camera with prefixed keys."""

    _MAX_TAG_SLOTS = 4  # max tags shown on dashboard per camera

    def __init__(self, cameras: dict):
        self._cameras = cameras
        self._cycle = 0

    _TELEMETRY_RATE = 5  # publish vision telemetry every N cycles (~3 Hz at 13 Hz loop)

    def update(self):
        """Publish current vision data to SmartDashboard."""
        sd = wpilib.SmartDashboard

        # Skip heavy Limelight network calls on most cycles -- get_all_targets()
        # is a blocking network request that causes loop overruns if called every cycle.
        if self._cycle % self._TELEMETRY_RATE != 0:
            self._cycle += 1
            return
        self._cycle += 1

        for name, vision in self._cameras.items():
            prefix = f"Vision/{name.title()}"

            targets = vision.get_all_targets()
            has_target = len(targets) > 0

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
