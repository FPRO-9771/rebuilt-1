"""
External system integrations.
Vision, Limelight, and other external device handlers.
"""

from constants import CON_VISION
# from .vision import VisionProvider  # COMMENTED OUT -- not using vision-based aiming (2026-03-19)

# --- Vision provider factory commented out ---
# LimelightVisionProvider spins up a background polling thread per camera.
# We only use the Limelight for camera stream (CameraServer) and
# NT-based odometry resets (limelight_helpers.py), neither of which
# needs the VisionProvider layer.  Keeping the code for future use.

# _use_mock_vision = False
# _mock_providers: dict[str, VisionProvider] | None = None
#
#
# def set_mock_vision_mode(enabled: bool) -> None:
#     """Enable mock vision for testing."""
#     global _use_mock_vision, _mock_providers
#     _use_mock_vision = enabled
#     if enabled:
#         from .mock_vision import MockVisionProvider
#         _mock_providers = {
#             key: MockVisionProvider()
#             for key in CON_VISION["cameras"]
#         }
#
#
# def get_vision_providers() -> dict[str, VisionProvider]:
#     """
#     Create one VisionProvider per camera defined in CON_VISION.
#     Returns mock providers in test mode, real Limelights otherwise.
#     """
#     if _use_mock_vision and _mock_providers is not None:
#         return _mock_providers
#     from .limelight_vision import LimelightVisionProvider
#     return {
#         key: LimelightVisionProvider(cam["host"])
#         for key, cam in CON_VISION["cameras"].items()
#     }
#
#
# def get_mock_vision(camera: str = "shooter") -> "MockVisionProvider":
#     """Get a mock provider by camera key for test setup."""
#     if not _mock_providers:
#         raise RuntimeError("Mock vision not enabled. Call set_mock_vision_mode(True) first.")
#     return _mock_providers[camera]
