"""
External system integrations.
Vision, Limelight, and other external device handlers.

TODO: Implement vision abstraction for testability.
"""

from typing import Optional

# Placeholder for vision provider
_use_mock_vision = False
_mock_provider = None


def set_mock_vision_mode(enabled: bool) -> None:
    """Enable mock vision for testing."""
    global _use_mock_vision, _mock_provider
    _use_mock_vision = enabled
    if enabled:
        from .mock_vision import MockVisionProvider
        _mock_provider = MockVisionProvider()


def get_vision_provider():
    """
    Get the appropriate vision provider.
    Returns mock in test mode, real Limelight otherwise.
    """
    if _use_mock_vision:
        return _mock_provider
    from .limelight_vision import LimelightVisionProvider
    return LimelightVisionProvider()


def get_mock_vision():
    """Get the mock provider for test setup."""
    if not _mock_provider:
        raise RuntimeError("Mock vision not enabled. Call set_mock_vision_mode(True) first.")
    return _mock_provider
