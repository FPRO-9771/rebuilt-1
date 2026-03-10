"""
Find-target command -- sweep the turret until vision acquires an AprilTag.

Spins the turret in one direction until either:
  a) vision picks up a priority tag (success -- command ends), or
  b) the turret hits a soft limit (brake briefly, then reverse).

If both soft limits are hit without finding a target, the command ends
(found_target() returns False).

Standalone usage:
    FindTarget(turret, vision, tag_priority_supplier, initial_direction=1.0)

Integration with AutoAim (future):
    # Sequence: find the target first, then track it.
    #   find_cmd = FindTarget(turret, vision, tag_priority_supplier)
    #   aim_cmd  = AutoAim(turret, vision, tag_priority_supplier, ...)
    #   combined = find_cmd.andThen(aim_cmd)
    #
    # To handle AutoAim losing the target at a soft limit, AutoAim
    # could set isFinished() = True when it detects a soft-limit stall,
    # and the whole thing can be wrapped in a RepeatCommand:
    #   RepeatCommand(find_cmd.andThen(aim_cmd))
"""

from typing import Callable

from commands2 import Command

from handlers.vision import VisionProvider
from subsystems.turret import Turret
from constants import CON_TURRET
from utils.logger import get_logger

_log = get_logger("find_target")


class FindTarget(Command):
    """Sweep the turret to find a visible AprilTag."""

    def __init__(
        self,
        turret: Turret,
        vision: VisionProvider,
        tag_priority_supplier: Callable[[], list[int]],
        initial_direction: float = 1.0,
    ):
        super().__init__()
        self.turret = turret
        self.vision = vision
        self._tag_priority_supplier = tag_priority_supplier
        self._direction = 1.0 if initial_direction >= 0 else -1.0

        self._found = False
        self._reversals = 0
        self._brake_counter = 0
        self._braking = False

        self.addRequirements(turret)

    def initialize(self):
        self._found = False
        self._reversals = 0
        self._brake_counter = 0
        self._braking = False
        _log.info(f"FindTarget started, direction={self._direction}")

    def execute(self):
        # Check if any priority tag is visible
        for tag_id in self._tag_priority_supplier():
            if self.vision.has_target(tag_id):
                self._found = True
                _log.info(f"FindTarget found tag {tag_id}")
                return

        pos = self.turret.get_position()
        min_pos = CON_TURRET["min_position"]
        max_pos = CON_TURRET["max_position"]
        tol = CON_TURRET["position_tolerance"]

        # Braking state -- apply opposing voltage to kill momentum
        if self._braking:
            brake_v = CON_TURRET["search_brake_voltage"]
            # Brake opposes the direction we were traveling
            self.turret._set_voltage(-self._direction * brake_v)
            self._brake_counter += 1
            if self._brake_counter >= CON_TURRET["search_brake_cycles"]:
                self._braking = False
                self._direction *= -1.0
                self._reversals += 1
                _log.info(
                    f"FindTarget reversed, now direction={self._direction} "
                    f"(reversal {self._reversals})"
                )
            return

        # Check if we hit a soft limit
        at_max = pos >= max_pos - tol and self._direction > 0
        at_min = pos <= min_pos + tol and self._direction < 0

        if at_max or at_min:
            # Start braking before reversing
            self._braking = True
            self._brake_counter = 0
            _log.debug(f"FindTarget hit limit at pos={pos:.2f}, braking")
            brake_v = CON_TURRET["search_brake_voltage"]
            self.turret._set_voltage(-self._direction * brake_v)
            return

        # Normal sweep -- drive in current direction
        voltage = self._direction * CON_TURRET["search_voltage"]
        self.turret._set_voltage(voltage)

    def isFinished(self) -> bool:
        if self._found:
            return True
        # Two reversals = swept both directions fully without finding a target
        if self._reversals >= 2:
            _log.warning("FindTarget exhausted both directions, no target found")
            return True
        return False

    def end(self, interrupted: bool):
        self.turret._stop()
        _log.info(
            f"FindTarget ended (found={self._found}, "
            f"interrupted={interrupted})"
        )

    def found_target(self) -> bool:
        """Did the sweep find a target? Check after command ends."""
        return self._found
