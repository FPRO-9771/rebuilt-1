"""
Legacy Limelight handler.
Direct access to Limelight data without abstraction.

NOTE: Prefer using vision.py VisionProvider for new code.
This file exists for reference from phoenix-v1 patterns.

TODO: Remove or integrate into VisionProvider once fully migrated.
"""

import math
from typing import Optional, Dict, Any


class LimelightHandler:
    """
    Direct Limelight wrapper.

    TODO: Migrate to LimelightVisionProvider in vision.py for testability.
    """

    def __init__(self, debug: bool = True):
        """
        Initialize Limelight connection.

        Args:
            debug: Enable debug output during discovery
        """
        # TODO: Implement when Limelight is connected
        # import limelight
        # import limelightresults
        # discovered = limelight.discover_limelights(debug=debug)
        # if discovered:
        #     self.limelight = limelight.Limelight(discovered[0])
        #     self.limelight.pipeline_switch(0)  # AprilTag pipeline
        #     self.limelight.enable_websocket()
        # else:
        #     self.limelight = None
        #     print("WARNING: No Limelight found!")
        self.limelight = None

    def get_target_data(self, target_tag_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get processed data for a specific AprilTag or closest one.

        Args:
            target_tag_id: Specific tag to look for, or None for closest

        Returns:
            Dict with tag_id, tx, ty, distance, yaw, pitch, roll, x_pos, y_pos, z_pos
            or None if no target found
        """
        if not self.limelight:
            return None

        # TODO: Implement actual Limelight parsing
        # result = self.limelight.get_latest_results()
        # parsed = limelightresults.parse_results(result)
        # ... find tag and build data dict
        return None
