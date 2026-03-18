"""
Intake lever arm subsystem.
Two independent motors (left and right) each run their own PID.
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
    """Intake lever arm -- two independent motors, each with own PID."""

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
            slot0=_SLOT0,
        )

    # --- Sensor reads (public) ---

    def get_position(self) -> float:
        """Get average position in rotations from both motors."""
        left = self.motor_left.get_position()
        right = self.motor_right.get_position()
        return (left + right) / 2.0

    def is_at_position(self, target: float) -> bool:
        """Check if both motors are within tolerance of target position."""
        left = self.motor_left.get_position()
        right = self.motor_right.get_position()
        return (abs(left - target) <= CON_INTAKE["position_tolerance"]
                and abs(right - target) <= CON_INTAKE["position_tolerance"])

    # --- Motor control (internal) ---

    def _set_position(self, position: float) -> None:
        """Command both motors to position, clamped to limits."""
        lo = min(CON_INTAKE["up_position"], CON_INTAKE["down_position"])
        hi = max(CON_INTAKE["up_position"], CON_INTAKE["down_position"])
        clamped = max(lo, min(position, hi))
        _log.debug(f"_set_position: requested={position:.4f} clamped={clamped:.4f}")
        self.motor_left.set_position(clamped)
        self.motor_right.set_position(clamped)

    def _set_voltage(self, volts: float) -> None:
        """Apply voltage to both motors with safety clamping."""
        max_v = CON_INTAKE["max_voltage"]
        clamped = max(-max_v, min(volts, max_v))
        if clamped != 0:
            _log.debug(f"_set_voltage: requested={volts:.3f} clamped={clamped:.3f}")
        self.motor_left.set_voltage(clamped)
        self.motor_right.set_voltage(clamped)

    def _stop(self) -> None:
        """Stop both motors."""
        _log.debug("_stop: motors to 0V")
        self.motor_left.stop()
        self.motor_right.stop()

    # --- Commands (public) ---

    def go_to_position(self, position: float,
                       hold_condition=None) -> Command:
        """Returns command to move to position, then light-hold.

        hold_condition: optional callable returning bool. When provided,
        the light hold only applies voltage if the condition is True.
        Otherwise motors rest in brake mode (0V).
        """
        return self._GoToPositionCommand(self, position, hold_condition)

    def hold_down(self) -> Command:
        """Returns command to apply constant downward voltage. No PID whine."""
        return self.run(
            lambda: self._set_voltage(CON_INTAKE["hold_down_voltage"])
        ).finallyDo(lambda interrupted: self._stop())

    def go_up(self) -> Command:
        """Returns command to raise intake to fully up position."""
        return self.go_to_position(CON_INTAKE["up_position"])

    def go_down(self, hold_condition=None) -> Command:
        """Returns command to lower intake to fully down position.

        hold_condition: optional callable returning bool. When provided,
        the light hold only applies voltage if the condition is True.
        """
        return self.go_to_position(CON_INTAKE["down_position"],
                                   hold_condition)

    def stop_command(self) -> Command:
        """Returns command to stop the intake."""
        return self.runOnce(lambda: self._stop())

    # --- Inner command classes ---

    # Number of consecutive stalled cycles before cutting power (50 = ~1 second)
    _STALL_CYCLES = 50
    # Position must change by at least this much per cycle to not be "stalled"
    _STALL_THRESHOLD = 0.001

    class _GoToPositionCommand(Command):
        """Move to target, then switch to light hold to save power.

        Safety features:
        - Stall detection: if motor is commanded but not moving, cut power
        - Hold deadband: no power when drift is small
        - Hold condition: optional gate for when hold should be active
        """

        def __init__(self, intake: "Intake", position: float,
                     hold_condition=None):
            super().__init__()
            self.intake = intake
            self.position = position
            self._hold_condition = hold_condition
            self._at_target = False
            self._stall_count = 0
            self._stalled = False
            self._last_pos = 0.0
            self.addRequirements(intake)

        def initialize(self):
            self._at_target = False
            self._stall_count = 0
            self._stalled = False
            self._last_pos = self.intake.get_position()
            direction = "DOWN" if self.position < 0 else "UP"
            _log.info(f"Intake moving {direction} to {self.position:.4f}")

        def _check_stall(self, pos: float) -> bool:
            """Track consecutive cycles with no movement. Return True if stalled."""
            if self._stalled:
                return True
            if abs(pos - self._last_pos) < Intake._STALL_THRESHOLD:
                self._stall_count += 1
            else:
                self._stall_count = 0
            self._last_pos = pos
            if self._stall_count >= Intake._STALL_CYCLES:
                self._stalled = True
                _log.warning(
                    f"Intake stall detected at pos={pos:.4f} "
                    f"target={self.position:.4f} -- cutting power"
                )
                self.intake._stop()
                return True
            return False

        def execute(self):
            pos = self.intake.get_position()
            left = self.intake.motor_left.get_position()
            right = self.intake.motor_right.get_position()

            if self._at_target:
                # If hold condition exists and is False, rest in brake mode
                if self._hold_condition and not self._hold_condition():
                    self.intake._set_voltage(0)
                    return

                # Light P-hold -- only correct if drift exceeds deadband
                error = self.position - pos
                if abs(error) < CON_INTAKE["hold_deadband"]:
                    self.intake._set_voltage(0)
                    return

                # Clear stall state when hold starts correcting
                self._stalled = False
                self._stall_count = 0

                hold_kP = CON_INTAKE["hold_kP"]
                max_v = CON_INTAKE["hold_max_voltage"]
                volts = max(-max_v, min(hold_kP * error, max_v))
                _log.debug(f"hold: L={left:.4f} R={right:.4f} err={error:.4f} v={volts:.2f}")
                self.intake._set_voltage(volts)

                # Stall protect during hold too
                self._check_stall(pos)
            else:
                # Stall protect during PID move
                if self._check_stall(pos):
                    return

                # Full PID to reach target
                self.intake._set_position(self.position)
                _log.debug(f"moving: L={left:.4f} R={right:.4f} target={self.position:.4f}")
                if self.intake.is_at_position(self.position):
                    _log.info(f"Intake reached target {self.position:.4f}")
                    self._at_target = True
                    self._stall_count = 0

        def isFinished(self) -> bool:
            return False

        def end(self, interrupted: bool):
            _log.info(f"Intake stopped (interrupted={interrupted})")
            self.intake._stop()
