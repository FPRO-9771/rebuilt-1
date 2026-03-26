"""
Tests for the telemetry dashboard module.
Uses mock hardware and patches SmartDashboard (requires HAL).
"""

from unittest.mock import patch, MagicMock

from handlers.mock_vision import MockVisionProvider
from subsystems.conveyor import Conveyor
from subsystems.turret import Turret
from subsystems.launcher import Launcher
from telemetry.motor_telemetry import MotorTelemetry
from telemetry.command_telemetry import CommandTelemetry
from telemetry.vision_telemetry import VisionTelemetry


# --- Motor telemetry ---

@patch("telemetry.motor_telemetry.wpilib")
def test_motor_telemetry_publishes_all_keys(mock_wpilib):
    """All motor keys should be published on update()."""
    sd = mock_wpilib.SmartDashboard

    conveyor = Conveyor()
    turret = Turret()
    launcher = Launcher()

    publisher = MotorTelemetry(conveyor, turret, launcher)
    # Call with each stagger offset so all keys get published
    for cycle in range(MotorTelemetry._PERIOD):
        publisher.update(cycle)

    expected_number_keys = [
        "Motors/Conveyor Velocity",
        "Motors/Turret Position",
        "Motors/Turret Velocity",
        "Motors/Launcher Target RPS",
        "Motors/Launcher Actual RPS",
    ]
    published_number_keys = [call.args[0] for call in sd.putNumber.call_args_list]
    for key in expected_number_keys:
        assert key in published_number_keys, f"Missing key: {key}"

    published_boolean_keys = [call.args[0] for call in sd.putBoolean.call_args_list]
    assert "Motors/Launcher At Speed" in published_boolean_keys


# --- Command telemetry ---

@patch("telemetry.command_telemetry.CommandScheduler")
@patch("telemetry.command_telemetry.wpilib")
def test_command_telemetry_publishes_active_and_recent(mock_wpilib, mock_scheduler_cls):
    """Active and Recent command keys should be published on update()."""
    sd = mock_wpilib.SmartDashboard
    mock_scheduler_cls.getInstance.return_value._scheduledCommands = {}

    publisher = CommandTelemetry()
    publisher.update()

    published_keys = [call.args[0] for call in sd.putString.call_args_list]
    assert "Commands/Active" in published_keys
    assert "Commands/Recent" in published_keys


@patch("telemetry.command_telemetry.CommandScheduler")
@patch("telemetry.command_telemetry.wpilib")
def test_command_telemetry_records_events(mock_wpilib, mock_scheduler_cls):
    """Events added via _on_event should appear in Recent output."""
    sd = mock_wpilib.SmartDashboard
    mock_scheduler_cls.getInstance.return_value._scheduledCommands = {}

    publisher = CommandTelemetry()

    # Simulate command events
    mock_cmd = MagicMock()
    mock_cmd.getName.return_value = "ShooterOrchestrator"
    publisher._on_event("START", mock_cmd)

    publisher.update()

    recent_call = [c for c in sd.putString.call_args_list
                   if c.args[0] == "Commands/Recent"]
    assert len(recent_call) == 1
    assert "ShooterOrchestrator" in recent_call[0].args[1]
    assert "START" in recent_call[0].args[1]


@patch("telemetry.command_telemetry.wpilib")
def test_command_telemetry_filters_internals(mock_wpilib):
    """Commands starting with _ or InstantCommand should be filtered."""
    publisher = CommandTelemetry()

    internal_cmd = MagicMock()
    internal_cmd.getName.return_value = "InstantCommand"
    publisher._on_event("START", internal_cmd)

    private_cmd = MagicMock()
    private_cmd.getName.return_value = "_SchedulerInternal"
    publisher._on_event("START", private_cmd)

    assert len(publisher._recent_events) == 0


# --- Vision telemetry ---

@patch("telemetry.vision_telemetry.wpilib")
def test_vision_telemetry_no_targets(mock_wpilib):
    """When no targets visible, Has Target should be false for each camera."""
    sd = mock_wpilib.SmartDashboard

    cameras = {
        "shooter": MockVisionProvider(),
        "front": MockVisionProvider(),
    }
    publisher = VisionTelemetry(cameras)
    publisher.update()

    boolean_keys = [c.args[0] for c in sd.putBoolean.call_args_list]
    number_keys = [c.args[0] for c in sd.putNumber.call_args_list]

    assert "Vision/Shooter/Has Target" in boolean_keys
    assert "Vision/Front/Has Target" in boolean_keys
    assert "Vision/Shooter/Tag Count" in number_keys
    assert "Vision/Front/Tag Count" in number_keys


@patch("telemetry.vision_telemetry.wpilib")
def test_vision_telemetry_with_targets(mock_wpilib):
    """When targets are visible, data should be published with prefixed keys."""
    sd = mock_wpilib.SmartDashboard

    shooter = MockVisionProvider()
    shooter.simulate_target_left(tag_id=4, offset_degrees=3.2, distance=2.4)

    front = MockVisionProvider()
    front.simulate_target_right(tag_id=7, offset_degrees=1.0, distance=3.1)

    cameras = {"shooter": shooter, "front": front}
    publisher = VisionTelemetry(cameras)
    publisher.update()

    # Check shooter camera published with prefix
    boolean_calls = {c.args[0]: c.args[1] for c in sd.putBoolean.call_args_list}
    assert boolean_calls["Vision/Shooter/Has Target"] is True
    assert boolean_calls["Vision/Front/Has Target"] is True

    number_calls = {c.args[0]: c.args[1] for c in sd.putNumber.call_args_list}
    assert number_calls["Vision/Shooter/Tag Count"] == 1
    assert number_calls["Vision/Front/Tag Count"] == 1

    # Check individual tag slot keys
    string_calls = {c.args[0]: c.args[1] for c in sd.putString.call_args_list}
    assert "ID 4" in string_calls["Vision/Shooter/Tag 1"]
    assert string_calls["Vision/Shooter/Tag 2"] == ""
    assert "ID 7" in string_calls["Vision/Front/Tag 1"]
    assert string_calls["Vision/Front/Tag 2"] == ""
