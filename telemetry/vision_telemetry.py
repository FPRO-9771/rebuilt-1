"""
Vision telemetry publisher.
Publishes Limelight AprilTag data to SmartDashboard.
"""

import wpilib


class VisionTelemetry:
    """Publishes vision target data as dashboard-friendly values."""

    def __init__(self, vision):
        self._vision = vision

    def update(self):
        """Publish current vision data to SmartDashboard."""
        sd = wpilib.SmartDashboard

        targets = self._vision.get_all_targets()
        has_target = len(targets) > 0

        sd.putBoolean("Vision/Has Target", has_target)
        sd.putNumber("Vision/Tag Count", len(targets))

        # Formatted ASCII table — one row per visible tag
        lines = ["ID |    TX |    TY | Dist  | Yaw"]
        for t in targets:
            lines.append(
                f"{t.tag_id:>2} | {t.tx:>5.1f}\u00b0 | {t.ty:>5.1f}\u00b0 "
                f"| {t.distance:.1f} m | {t.yaw:>5.1f}\u00b0"
            )
        sd.putString("Vision/Tags", "\n".join(lines))
