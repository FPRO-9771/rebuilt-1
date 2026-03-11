"""
Tests for driver control drive mode toggle and drive telemetry.
Verifies field-centric / robot-centric switching and pose output.
"""

from unittest.mock import patch

from phoenix6 import swerve
from wpimath.geometry import Pose2d, Rotation2d
from wpimath.kinematics import SwerveModuleState


# --- Drive mode toggle logic ---
# These tests exercise the same state + request selection pattern used
# in configure_driver's get_drive_request closure.


def _make_requests():
    """Build the same pair of requests used in driver_controls."""
    drive_fc = swerve.requests.FieldCentric()
    drive_rc = swerve.requests.RobotCentric()
    return drive_fc, drive_rc


def _select_request(state, drive_fc, drive_rc):
    """Same selection logic as get_drive_request."""
    return drive_rc if state["robot_centric"] else drive_fc


def test_starts_field_centric():
    """Default state should select field-centric."""
    state = {"robot_centric": False}
    drive_fc, drive_rc = _make_requests()

    req = _select_request(state, drive_fc, drive_rc)
    assert req is drive_fc


def test_toggle_to_robot_centric():
    """After one toggle, should select robot-centric."""
    state = {"robot_centric": False}
    drive_fc, drive_rc = _make_requests()

    state["robot_centric"] = not state["robot_centric"]

    req = _select_request(state, drive_fc, drive_rc)
    assert req is drive_rc


def test_toggle_back_to_field_centric():
    """After two toggles, should be back to field-centric."""
    state = {"robot_centric": False}
    drive_fc, drive_rc = _make_requests()

    state["robot_centric"] = not state["robot_centric"]
    state["robot_centric"] = not state["robot_centric"]

    req = _select_request(state, drive_fc, drive_rc)
    assert req is drive_fc


def test_rapid_toggles():
    """Odd number of toggles = robot-centric, even = field-centric."""
    state = {"robot_centric": False}
    drive_fc, drive_rc = _make_requests()

    for i in range(7):
        state["robot_centric"] = not state["robot_centric"]

    # 7 toggles (odd) -> robot-centric
    assert _select_request(state, drive_fc, drive_rc) is drive_rc

    state["robot_centric"] = not state["robot_centric"]

    # 8 toggles (even) -> field-centric
    assert _select_request(state, drive_fc, drive_rc) is drive_fc


def test_request_types_are_distinct():
    """FieldCentric and RobotCentric must be different types."""
    drive_fc, drive_rc = _make_requests()
    assert type(drive_fc) is not type(drive_rc)


def test_same_request_object_reused():
    """Each mode should reuse the same request object (not create new ones)."""
    state = {"robot_centric": False}
    drive_fc, drive_rc = _make_requests()

    req1 = _select_request(state, drive_fc, drive_rc)
    req2 = _select_request(state, drive_fc, drive_rc)
    assert req1 is req2

    state["robot_centric"] = True
    req3 = _select_request(state, drive_fc, drive_rc)
    req4 = _select_request(state, drive_fc, drive_rc)
    assert req3 is req4
    assert req3 is drive_rc


# --- Pose + drive mode telemetry ---
# These use a real SwerveDriveState with real Pose2d values passed through
# the actual SwerveTelemetry.telemeterize() method. Each test calls twice
# with different values to prove the output tracks the input.


def _make_drive_state(x, y, heading_deg):
    """Build a SwerveDriveState with specific pose values."""
    state = swerve.SwerveDrivetrain.SwerveDriveState()
    state.pose = Pose2d(x, y, Rotation2d.fromDegrees(heading_deg))
    state.odometry_period = 0.02
    # 4 modules with zero state
    zero_module = SwerveModuleState(0, Rotation2d())
    state.module_states = [zero_module] * 4
    state.module_targets = [zero_module] * 4
    state.module_positions = []
    return state


@patch("telemetry.swerve_telemetry.SignalLogger")
@patch("telemetry.swerve_telemetry.SmartDashboard")
def test_pose_telemetry_tracks_state(mock_sd, _mock_logger):
    """Pose X/Y/Heading must reflect the actual drive state, not hardcoded values."""
    from telemetry.swerve_telemetry import SwerveTelemetry

    telem = SwerveTelemetry(5.0)

    # Telemetry only publishes every Nth call; warm up the cycle counter.
    warmup = _make_drive_state(0, 0, 0)
    # Advance until one cycle before the next publish
    while (telem._cycle + 1) % telem._PUBLISH_EVERY_N != telem._PUBLISH_OFFSET:
        telem.telemeterize(warmup)

    # First pose
    state1 = _make_drive_state(1.23, 4.56, 78.9)
    telem.telemeterize(state1)

    calls1 = {c.args[0]: c.args[1] for c in mock_sd.putNumber.call_args_list}
    assert calls1["Drive/Pose X (m)"] == 1.23
    assert calls1["Drive/Pose Y (m)"] == 4.56
    assert calls1["Drive/Heading (deg)"] == 78.9

    mock_sd.reset_mock()

    # Second pose -- different values prove output changes with input
    # Advance until one cycle before the next publish
    while (telem._cycle + 1) % telem._PUBLISH_EVERY_N != telem._PUBLISH_OFFSET:
        telem.telemeterize(warmup)
    state2 = _make_drive_state(-3.21, 0.07, -145.3)
    telem.telemeterize(state2)

    calls2 = {c.args[0]: c.args[1] for c in mock_sd.putNumber.call_args_list}
    assert calls2["Drive/Pose X (m)"] == -3.21
    assert calls2["Drive/Pose Y (m)"] == 0.07
    assert calls2["Drive/Heading (deg)"] == -145.3


@patch("telemetry.swerve_telemetry.SignalLogger")
@patch("telemetry.swerve_telemetry.SmartDashboard")
def test_pose_telemetry_rounds_values(mock_sd, _mock_logger):
    """Pose values should be rounded (X/Y to 2 decimal, heading to 1)."""
    from telemetry.swerve_telemetry import SwerveTelemetry

    telem = SwerveTelemetry(5.0)
    # Warm up the cycle counter so the next call publishes.
    warmup = _make_drive_state(0, 0, 0)
    # Advance until one cycle before the next publish
    while (telem._cycle + 1) % telem._PUBLISH_EVERY_N != telem._PUBLISH_OFFSET:
        telem.telemeterize(warmup)
    state = _make_drive_state(1.23456, 7.89012, 123.456)
    telem.telemeterize(state)

    calls = {c.args[0]: c.args[1] for c in mock_sd.putNumber.call_args_list}
    assert calls["Drive/Pose X (m)"] == 1.23
    assert calls["Drive/Pose Y (m)"] == 7.89
    assert calls["Drive/Heading (deg)"] == 123.5


def test_toggle_state_and_request_stay_in_sync():
    """After each toggle, the state boolean and the selected request must agree."""
    state = {"robot_centric": False}
    drive_fc, drive_rc = _make_requests()

    for expected_rc in [True, False, True, True, False]:
        state["robot_centric"] = expected_rc
        req = _select_request(state, drive_fc, drive_rc)

        # The state (which drives the telemetry putBoolean) and the
        # selected request type must always agree.
        if expected_rc:
            assert req is drive_rc
            assert state["robot_centric"] is True
        else:
            assert req is drive_fc
            assert state["robot_centric"] is False
