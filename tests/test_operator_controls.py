"""
Tests for operator controls wiring.
Individual command behavior is tested in dedicated test files
(test_coordinate_aim, test_auto_shoot, test_manual_launcher).
This file tests the configure_operator function itself.
"""

from unittest.mock import MagicMock

from controls.operator_controls import configure_operator


def _make_mock_operator():
    """Create a mock operator controller with numeric return values."""
    operator = MagicMock()
    operator.getLeftX.return_value = 0.0
    operator.getRightY.return_value = 0.0
    return operator


def test_configure_operator_returns_state():
    """configure_operator returns mutable state dict."""
    operator = _make_mock_operator()
    turret = MagicMock()
    launcher = MagicMock()
    hood = MagicMock()
    vision = MagicMock()
    match_setup = MagicMock()

    state = configure_operator(
        operator, None, turret, launcher, hood, vision, match_setup
    )

    assert "intake_down" in state
    assert state["intake_down"] is False
