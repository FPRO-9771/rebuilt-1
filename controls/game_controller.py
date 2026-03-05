"""
Game controller wrapper.
Provides Xbox-style method names regardless of physical controller type.
Set CON_ROBOT["use_ps4"] to True when using PlayStation controllers in sim.
"""

from commands2.button import CommandXboxController, CommandPS4Controller

from utils.logger import get_logger

_log = get_logger("controller")


class GameController:
    """Wraps Xbox or PS4 controller with a uniform interface."""

    def __init__(self, port: int, use_ps4: bool):
        if use_ps4:
            self._ctrl = CommandPS4Controller(port)
            _log.info(f"Port {port}: using PS4 controller")
        else:
            self._ctrl = CommandXboxController(port)
            _log.info(f"Port {port}: using Xbox controller")
        self._use_ps4 = use_ps4

    # --- Buttons (differ between controllers) ---

    def y(self):
        return self._ctrl.triangle() if self._use_ps4 else self._ctrl.y()

    def a(self):
        return self._ctrl.cross() if self._use_ps4 else self._ctrl.a()

    def b(self):
        return self._ctrl.circle() if self._use_ps4 else self._ctrl.b()

    def x(self):
        return self._ctrl.square() if self._use_ps4 else self._ctrl.x()

    def leftBumper(self):
        return self._ctrl.L1() if self._use_ps4 else self._ctrl.leftBumper()

    def rightBumper(self):
        return self._ctrl.R1() if self._use_ps4 else self._ctrl.rightBumper()

    def leftTrigger(self):
        return self._ctrl.L2() if self._use_ps4 else self._ctrl.leftTrigger()

    def rightTrigger(self):
        return self._ctrl.R2() if self._use_ps4 else self._ctrl.rightTrigger()

    def back(self):
        return self._ctrl.share() if self._use_ps4 else self._ctrl.back()

    def start(self):
        return self._ctrl.options() if self._use_ps4 else self._ctrl.start()

    # --- Axes (same on both) ---

    def getLeftX(self):
        return self._ctrl.getLeftX()

    def getLeftY(self):
        return self._ctrl.getLeftY()

    def getRightX(self):
        return self._ctrl.getRightX()

    def getRightY(self):
        return self._ctrl.getRightY()
