"""
Pytest fixtures for robot testing.
Automatically enables mock hardware/vision for all tests.
"""

import pytest

from hardware import set_mock_mode
from handlers import set_mock_vision_mode


@pytest.fixture(autouse=True)
def mock_hardware():
    """Automatically use mock hardware for all tests."""
    set_mock_mode(True)
    yield
    set_mock_mode(False)


@pytest.fixture(autouse=True)
def mock_vision():
    """Automatically use mock vision for all tests."""
    set_mock_vision_mode(True)
    yield
    set_mock_vision_mode(False)
