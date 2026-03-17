"""
Turret subsystem (Minion variant).
Rotating turret powered by a Minion motor via TalonFXS with soft position limits.

Drop-in replacement for Turret (Kraken). Same public interface so all commands,
controls, and tests work with either version.  To switch, change the import
in robot_container.py and flip the wired flags in constants/ids.py.
"""

from typing import Callable
from commands2 import Subsystem, Command

from hardware import create_motor
from constants import MOTOR_IDS
from constants.shooter import CON_TURRET_MINION
from utils.logger import get_logger

_log = get_logger("turret_minion")


class TurretMinion(Subsystem):
    """
    Rotating turret for aiming the shooter (Minion / TalonFXS variant).
    Uses voltage control with software position limits.
    """

    def __init__(self):
        super().__init__()
        self.motor = create_motor(
            MOTOR_IDS["turret_minion"],
            inverted=CON_TURRET_MINION["inverted"],
            brake=CON_TURRET_MINION["brake"],
            slot0={
                "kP": CON_TURRET_MINION["slot0_kP"],
                "kI": CON_TURRET_MINION["slot0_kI"],
                "kD": CON_TURRET_MINION["slot0_kD"],
                "kS": CON_TURRET_MINION["slot0_kS"],
                "kV": CON_TURRET_MINION["slot0_kV"],
                "kA": CON_TURRET_MINION["slot0_kA"],
                "kG": CON_TURRET_MINION["slot0_kG"],
            },
        )
        self.setDefaultCommand(self.hold_position())

    # --- Sensor reads (public) ---

    def get_position(self) -> float:
        """Get current turret position in rotations."""
        return self.motor.get_position()

    def get_velocity(self) -> float:
        """Get current turret velocity in rotations per second."""
        return self.motor.get_velocity()

    def is_at_position(self, target: float) -> bool:
        """Check if turret is within tolerance of target position."""
        return abs(self.get_position() - target) <= CON_TURRET_MINION["position_tolerance"]

    def is_within_limits(self) -> bool:
        """Check if turret is within soft limits."""
        pos = self.get_position()
        return CON_TURRET_MINION["min_position"] <= pos <= CON_TURRET_MINION["max_position"]

    # --- Motor control (internal) ---

    def _set_voltage(self, volts: float) -> None:
        """Apply voltage with safety clamping, soft limit ramp-down, and hard stop."""
        max_v = CON_TURRET_MINION["max_voltage"]
        clamped = max(-max_v, min(volts, max_v))

        pos = self.get_position()
        min_pos = CON_TURRET_MINION["min_position"]
        max_pos = CON_TURRET_MINION["max_position"]
        ramp = CON_TURRET_MINION["soft_limit_ramp"]

        # Hard stop -- block voltage that would push past limits
        if pos >= max_pos and clamped > 0:
            clamped = 0
        elif pos <= min_pos and clamped < 0:
            clamped = 0

        # Ramp down voltage when approaching a limit from inside
        if ramp > 0 and clamped != 0:
            if clamped > 0 and pos > max_pos - ramp:
                scale = max(0.5, (max_pos - pos) / ramp)
                clamped *= scale
            elif clamped < 0 and pos < min_pos + ramp:
                scale = max(0.5, (pos - min_pos) / ramp)
                clamped *= scale

        # # TEMPORARY: log position for soft limit tuning
        # _log.info(f"pos={pos:.4f} volts={clamped:.3f}")
        self.motor.set_voltage(clamped)

    def _stop(self) -> None:
        """Stop the turret."""
        self.motor.stop()

    # --- Commands (public) ---

    def manual(self, speed_supplier: Callable[[], float]) -> Command:
        """
        Returns command for joystick control.

        Args:
            speed_supplier: Lambda returning -1.0 to 1.0 from joystick
        """
        return self._ManualCommand(self, speed_supplier)

    def hold_position(self) -> Command:
        """Returns command that holds current position via closed-loop."""
        return self._HoldPositionCommand(self)

    def stop_command(self) -> Command:
        """Returns command to stop the turret."""
        return self.runOnce(lambda: self._stop())

    # --- Inner command classes ---

    class _ManualCommand(Command):
        """Joystick control of turret."""

        def __init__(self, turret: "TurretMinion", speed_supplier: Callable[[], float]):
            super().__init__()
            self.turret = turret
            self.speed_supplier = speed_supplier
            self.addRequirements(turret)

        def execute(self):
            raw = self.speed_supplier()
            # Exponential curve: preserves sign, small inputs give fine control
            exp = CON_TURRET_MINION["manual_exponent"]
            speed = abs(raw) ** exp * (1.0 if raw >= 0 else -1.0)
            voltage = speed * CON_TURRET_MINION["max_voltage"] * CON_TURRET_MINION["manual_speed_factor"]
            self.turret._set_voltage(voltage)

        def end(self, interrupted: bool):
            self.turret._stop()

    class _HoldPositionCommand(Command):
        """Hold turret at current position."""

        def __init__(self, turret: "TurretMinion"):
            super().__init__()
            self.turret = turret
            self._target = 0.0
            self.addRequirements(turret)

        def initialize(self):
            self._target = self.turret.get_position()

        def execute(self):
            self.turret.motor.set_position(self._target)

        def end(self, interrupted: bool):
            self.turret._stop()
