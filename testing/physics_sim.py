"""
Physics simulation models.
Calibrate from real robot measurements, then use for testing.

TODO: Implement after drivetrain is built and calibration is done.

Workflow:
1. Run calibration scripts on real robot (calibration/measure_drivetrain.py)
2. Record max speed, rotation rate, acceleration in constants.SIM_CALIBRATION
3. Use these models in tests to verify autonomous reaches expected positions

See docs/architecture/testing-and-simulation.md for detailed examples.
"""

import math
from dataclasses import dataclass, field
from typing import Optional

from constants import SIM_CALIBRATION, SIM_DT


@dataclass
class Pose2D:
    """Robot position and heading on the field."""
    x: float = 0.0       # meters, +X is toward opposing alliance
    y: float = 0.0       # meters, +Y is to the left
    heading: float = 0.0 # degrees, 0 = facing +X, 90 = facing +Y

    def distance_to(self, other: 'Pose2D') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

    def __repr__(self):
        return f"Pose2D(x={self.x:.2f}, y={self.y:.2f}, heading={self.heading:.1f})"


@dataclass
class DrivetrainState:
    """Current state of simulated drivetrain."""
    pose: Pose2D = field(default_factory=Pose2D)
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    rotation_rate: float = 0.0
    commanded_vx: float = 0.0
    commanded_vy: float = 0.0
    commanded_rotation: float = 0.0


class DrivetrainPhysicsSim:
    """
    Simulates drivetrain physics based on calibrated measurements.

    TODO: Implement step() and integrate with mock drivetrain.
    """

    def __init__(self):
        self.state = DrivetrainState()
        self.cal = SIM_CALIBRATION.get("drivetrain", {})
        self.command_history: list[dict] = []
        self.pose_history: list[Pose2D] = []

    def set_command(self, velocity_x: float, velocity_y: float, rotation: float) -> None:
        """Set drive command."""
        self.state.commanded_vx = velocity_x
        self.state.commanded_vy = velocity_y
        self.state.commanded_rotation = rotation

    def step(self, dt: float = SIM_DT) -> None:
        """Advance simulation by one time step."""
        # TODO: Implement physics model
        pass

    def reset(self, pose: Optional[Pose2D] = None) -> None:
        """Reset simulation to starting state."""
        self.state = DrivetrainState()
        if pose:
            self.state.pose = pose
        self.command_history.clear()
        self.pose_history.clear()

    @property
    def pose(self) -> Pose2D:
        return self.state.pose


@dataclass
class MechanismState:
    """State of a single-axis mechanism."""
    position: float = 0.0
    velocity: float = 0.0
    commanded_voltage: float = 0.0


class MechanismPhysicsSim:
    """
    Simulates a single-axis mechanism based on calibration.

    TODO: Implement step() for mechanism physics.
    """

    def __init__(self, name: str, min_pos: float, max_pos: float):
        self.name = name
        self.state = MechanismState()
        self.min_pos = min_pos
        self.max_pos = max_pos
        self.cal = SIM_CALIBRATION.get(name, {"voltage_to_speed": 1.0})

    def set_voltage(self, voltage: float) -> None:
        """Set commanded voltage."""
        self.state.commanded_voltage = voltage

    def step(self, dt: float = SIM_DT) -> None:
        """Advance simulation by one time step."""
        # TODO: Implement physics model
        pass

    def reset(self, position: float = 0.0) -> None:
        self.state = MechanismState(position=position)

    @property
    def position(self) -> float:
        return self.state.position
