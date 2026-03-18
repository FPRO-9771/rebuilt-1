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
        """Apply voltage to both motors."""
        if volts != 0:
            _log.debug(f"_set_voltage: {volts:.3f}V")
        self.motor_left.set_voltage(volts)
        self.motor_right.set_voltage(volts)

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
        """Snapshot current position and hold it with soft P-control."""
        return self._HoldDownCommand(self)

    def go_up(self) -> Command:
        """Two-phase raise: fight gravity hard, then ease into position."""
        return self._TwoPhaseMove(
            self,
            target=CON_INTAKE["up_position"],
            transition=self._transition_position(going_down=False),
            phase1_voltage=CON_INTAKE["up_fight_voltage"],
            phase2_voltage=CON_INTAKE["up_ease_voltage"],
            going_down=False,
        )

    def go_down(self) -> Command:
        """Two-phase lower: push down, then brake against gravity."""
        return self._TwoPhaseMove(
            self,
            target=CON_INTAKE["down_position"],
            transition=self._transition_position(going_down=True),
            phase1_voltage=CON_INTAKE["down_push_voltage"],
            phase2_voltage=CON_INTAKE["down_brake_voltage"],
            going_down=True,
        )

    def stop_command(self) -> Command:
        """Returns command to stop the intake."""
        return self.runOnce(lambda: self._stop())

    # --- Helpers (internal) ---

    @staticmethod
    def _transition_position(going_down: bool) -> float:
        """Position where phase 2 begins, computed from constants."""
        up = CON_INTAKE["up_position"]
        down = CON_INTAKE["down_position"]
        key = "down_transition_fraction" if going_down else "up_transition_fraction"
        frac = CON_INTAKE[key]
        return up + frac * (down - up)

    # --- Inner command classes ---

    # Number of consecutive stalled cycles before cutting power (50 = ~1 second)
    _STALL_CYCLES = 50
    # Phase 2 stall: fewer cycles -- arm settling at target is expected and fast
    _PHASE2_STALL_CYCLES = 20
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

    class _HoldDownCommand(Command):
        """Hold intake at whatever position it was in when command started.

        Uses soft P-control with deadband -- same tuning constants as the
        light hold in _GoToPositionCommand (hold_kP, hold_max_voltage,
        hold_deadband).
        """

        def __init__(self, intake: "Intake"):
            super().__init__()
            self.intake = intake
            self.target = 0.0
            self.addRequirements(intake)

        def initialize(self):
            self.target = self.intake.get_position()
            _log.info(f"Hold-down: locking at {self.target:.4f}")

        def execute(self):
            error = self.target - self.intake.get_position()
            if abs(error) < CON_INTAKE["hold_deadband"]:
                self.intake._set_voltage(0)
                return
            hold_kP = CON_INTAKE["hold_kP"]
            max_v = CON_INTAKE["hold_max_voltage"]
            volts = max(-max_v, min(hold_kP * error, max_v))
            self.intake._set_voltage(volts)

        def isFinished(self) -> bool:
            return False

        def end(self, interrupted: bool):
            _log.info(f"Intake stopped (interrupted={interrupted})")
            self.intake._stop()

    class _TwoPhaseMove(Command):
        """Two-phase move with different voltages before/after transition.

        Going DOWN:
          Phase 1 -- push the arm down (gravity not helping yet)
          Phase 2 -- brake against gravity so the arm doesn't slam

        Going UP (opposite):
          Phase 1 -- fight gravity hard (arm is horizontal, heaviest)
          Phase 2 -- ease off as gravity stops fighting near vertical

        Finishes when the arm reaches the target position.

        TUNING (all values in constants/intake.py):
          Arm won't start moving down? -> increase down_push_voltage (more negative)
          Arm slams at the bottom?     -> increase down_brake_voltage (more positive)
          Arm won't start moving up?   -> increase up_fight_voltage (more positive)
          Arm slams at the top?        -> increase up_ease_voltage (more negative)
          Phase switch too early/late going down? -> adjust down_transition_fraction
          Phase switch too early/late going up?   -> adjust up_transition_fraction
        """

        def __init__(self, intake: "Intake", target: float,
                     transition: float, phase1_voltage: float,
                     phase2_voltage: float, going_down: bool):
            super().__init__()
            self.intake = intake
            self.target = target
            self.transition = transition
            self.phase1_voltage = phase1_voltage
            self.phase2_voltage = phase2_voltage
            self.going_down = going_down
            self.in_phase2 = False
            self._phase2_start_pos = 0.0
            self._phase2_stall_count = 0
            self._phase2_last_pos = 0.0
            self._phase2_stalled = False
            self.addRequirements(intake)

        def initialize(self):
            self.in_phase2 = False
            self._phase2_start_pos = 0.0
            self._phase2_stall_count = 0
            self._phase2_last_pos = 0.0
            self._phase2_stalled = False
            self._direction = "DOWN" if self.going_down else "UP"
            _log.info(
                f"TwoPhaseMove {self._direction}: "
                f"target={self.target:.4f} transition={self.transition:.4f} "
                f"phase1={self.phase1_voltage:.2f}V "
                f"phase2={self.phase2_voltage:.2f}V"
            )

        def execute(self):
            pos = self.intake.get_position()
            left = self.intake.motor_left.get_position()
            right = self.intake.motor_right.get_position()

            if not self.in_phase2:
                # Check if we've reached the transition point
                if self.going_down:
                    past_transition = pos <= self.transition
                else:
                    past_transition = pos >= self.transition

                if past_transition:
                    self.in_phase2 = True
                    self._phase2_start_pos = pos
                    _log.info(
                        f"TwoPhaseMove {self._direction}: "
                        f"-> phase 2 at pos={pos:.4f} "
                        f"L={left:.4f} R={right:.4f}"
                    )
                else:
                    _log.debug(
                        f"TwoPhaseMove {self._direction} phase1: "
                        f"pos={pos:.4f} L={left:.4f} R={right:.4f} "
                        f"v={self.phase1_voltage:.2f}V"
                    )
                    self.intake._set_voltage(self.phase1_voltage)
                    return

            # Phase 2: controlled voltage until at target
            _log.debug(
                f"TwoPhaseMove {self._direction} phase2: "
                f"pos={pos:.4f} L={left:.4f} R={right:.4f} "
                f"v={self.phase2_voltage:.2f}V"
            )
            self.intake._set_voltage(self.phase2_voltage)

            # Stall detection: arm settled (hit hard stop or equilibrated)
            if abs(pos - self._phase2_last_pos) < Intake._STALL_THRESHOLD:
                self._phase2_stall_count += 1
                if self._phase2_stall_count >= Intake._PHASE2_STALL_CYCLES:
                    self._phase2_stalled = True
                    _log.info(
                        f"TwoPhaseMove {self._direction}: "
                        f"settled at pos={pos:.4f} target={self.target:.4f}"
                    )
            else:
                self._phase2_stall_count = 0
            self._phase2_last_pos = pos

        def isFinished(self) -> bool:
            if self.intake.is_at_position(self.target):
                return True
            if self._phase2_stalled:
                return True
            if self.in_phase2:
                pos = self.intake.get_position()
                # Finish the moment the arm passes through (or reaches) the target.
                # This fires even if the arm is still moving, which is fine --
                # motors cut to brake mode and the arm coasts to a stop.
                if self.going_down and pos <= self.target:
                    return True
                if not self.going_down and pos >= self.target:
                    return True
                # Safety: if phase 2 has reversed us all the way back past the
                # phase 2 start position, the brake is fighting the wrong way -- stop.
                overshoot = CON_INTAKE["position_tolerance"] * 3
                if self.going_down and pos > self._phase2_start_pos + overshoot:
                    _log.warning(
                        f"TwoPhaseMove DOWN: phase2 reversed past start "
                        f"(pos={pos:.4f} start={self._phase2_start_pos:.4f}) -- stopping"
                    )
                    return True
                if not self.going_down and pos < self._phase2_start_pos - overshoot:
                    _log.warning(
                        f"TwoPhaseMove UP: phase2 reversed past start "
                        f"(pos={pos:.4f} start={self._phase2_start_pos:.4f}) -- stopping"
                    )
                    return True
            return False

        def end(self, interrupted: bool):
            self.intake._stop()
            pos = self.intake.get_position()
            if interrupted:
                _log.info(
                    f"TwoPhaseMove {self._direction}: "
                    f"interrupted at pos={pos:.4f}"
                )
            else:
                _log.info(
                    f"TwoPhaseMove {self._direction}: "
                    f"reached target at pos={pos:.4f}"
                )
