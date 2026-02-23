"""
Vision telemetry publisher.
Publishes per-camera Limelight AprilTag data to SmartDashboard.
"""

import wpilib


class VisionTelemetry:
    """Publishes vision target data for each camera with prefixed keys."""

    def __init__(self, cameras: dict):
        self._cameras = cameras

    def update(self):
        """Publish current vision data to SmartDashboard."""
        sd = wpilib.SmartDashboard

        for name, vision in self._cameras.items():
            prefix = f"Vision/{name.title()}"

            targets = vision.get_all_targets()
            has_target = len(targets) > 0

            sd.putBoolean(f"{prefix}/Has Target", has_target)
            sd.putNumber(f"{prefix}/Tag Count", len(targets))

            # Formatted ASCII table — one row per visible tag
            lines = ["ID |    TX |    TY | Dist  | Yaw"]
            for t in targets:
                lines.append(
                    f"{t.tag_id:>2} | {t.tx:>5.1f}\u00b0 | {t.ty:>5.1f}\u00b0 "
                    f"| {t.distance:.1f} m | {t.yaw:>5.1f}\u00b0"
                )
            sd.putString(f"{prefix}/Tags", "\n".join(lines))
