"""
Intake lever arm subsystem.
Left motor is the leader; right motor follows with inverted direction.
Uses closed-loop position control for go-to-position commands.
Starts in the up position.
"""

from commands2 import Subsystem, Command

from hardware import create_motor
from constants import MOTOR_IDS, CON_INTAKE
from utils.logger import get_logger

_log = get_logger("intake")

_SLOT0 = {
    "kP": CON_INTAKE["slot0_kP"],
    "kI": CON_INTAKE["slot0_kI"],
    "kD": CON_INTAKE["slot0_kD"],
    "kS": CON_INTAKE["slot0_kS"],
    "kV": CON_INTAKE["slot0_kV"],
    "kA": CON_INTAKE["slot0_kA"],
    "kG": CON_INTAKE["slot0_kG"],
}


class Intake(Subsystem):
    """Intake lever arm -- left motor leads, right motor follows inverted."""

    def __init__(self):
        super().__init__()
        self.motor_left = create_motor(
            MOTOR_IDS["intake_left"],
            inverted=CON_INTAKE["inverted"],
            brake=True,
            slot0=_SLOT0,
        )
        self.motor_right = create_motor(
            MOTOR_IDS["intake_right"],
            inverted=False,
            brake=True,
        )
        # Right follows left with opposed direction
        leader_id = MOTOR_IDS["intake_left"]["can_id"]
        self.motor_right.set_follower(leader_id, oppose_direction=False)

    # --- Sensor reads (public) ---

    def get_position(self) -> float:
        """Get current position in rotations (from left motor)."""
        return self.motor_left.get_position()

    def is_at_position(self, target: float) -> bool:
        """Check if intake is within tolerance of target position."""
        return abs(self.get_position() - target) <= CON_INTAKE["position_tolerance"]

    # --- Motor control (internal) ---

    def _set_position(self, position: float) -> None:
        """Move leader motor to position, clamped to limits. Follower tracks."""
        lo = min(CON_INTAKE["up_position"], CON_INTAKE["down_position"])
        hi = max(CON_INTAKE["up_position"], CON_INTAKE["down_position"])
        clamped = max(lo, min(position, hi))
        self.motor_left.set_position(clamped)

    def _set_voltage(self, volts: float) -> None:
        """Apply voltage to leader motor with safety clamping. Follower tracks."""
        max_v = CON_INTAKE["max_voltage"]
        clamped = max(-max_v, min(volts, max_v))
        self.motor_left.set_voltage(clamped)

    def _stop(self) -> None:
        """Stop leader motor. Follower tracks."""
        self.motor_left.stop()

    # --- Commands (public) ---

    def go_to_position(self, position: float) -> Command:
        """Returns command to hold intake at a position. Never auto-finishes."""
        return self._GoToPositionCommand(self, position)

    def hold_down(self) -> Command:
        """Returns command to apply constant downward voltage. No PID whine."""
        return self.run(
            lambda: self._set_voltage(CON_INTAKE["hold_down_voltage"])
        ).finallyDo(lambda interrupted: self._stop())

    def go_up(self) -> Command:
        """Returns command to raise intake to fully up position."""
        return self.go_to_position(CON_INTAKE["up_position"])

    def go_down(self) -> Command:
        """Returns command to lower intake to fully down position."""
        return self.go_to_position(CON_INTAKE["down_position"])

    def stop_command(self) -> Command:
        """Returns command to stop the intake."""
        return self.runOnce(lambda: self._stop())

    # --- Inner command classes ---

    class _GoToPositionCommand(Command):
        """Hold intake at target position -- never auto-finishes."""

        def __init__(self, intake: "Intake", position: float):
            super().__init__()
            self.intake = intake
            self.position = position
            self.addRequirements(intake)

        def execute(self):
            self.intake._set_position(self.position)

        def isFinished(self) -> bool:
            return False

        def end(self, interrupted: bool):
            self.intake._stop()
