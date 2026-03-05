"""
Tests for GameController button wrappers.
Verifies that back() and start() delegate to the correct underlying method.
"""

from unittest.mock import MagicMock, patch
from controls.game_controller import GameController


def _make_controller(use_ps4):
    """Create a GameController with a mocked underlying controller."""
    with patch(
        "controls.game_controller.CommandPS4Controller" if use_ps4
        else "controls.game_controller.CommandXboxController"
    ) as MockCtrl:
        mock_instance = MagicMock()
        MockCtrl.return_value = mock_instance
        gc = GameController(port=0, use_ps4=use_ps4)
    return gc, mock_instance


def test_back_xbox():
    """Xbox back() delegates to underlying back()."""
    gc, mock = _make_controller(use_ps4=False)
    gc.back()
    mock.back.assert_called_once()


def test_back_ps4():
    """PS4 back() delegates to underlying share()."""
    gc, mock = _make_controller(use_ps4=True)
    gc.back()
    mock.share.assert_called_once()


def test_start_xbox():
    """Xbox start() delegates to underlying start()."""
    gc, mock = _make_controller(use_ps4=False)
    gc.start()
    mock.start.assert_called_once()


def test_start_ps4():
    """PS4 start() delegates to underlying options()."""
    gc, mock = _make_controller(use_ps4=True)
    gc.start()
    mock.options.assert_called_once()
