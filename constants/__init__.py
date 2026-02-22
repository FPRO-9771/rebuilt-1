"""
Configuration constants for Team 9771 Robot 2026.
All magic numbers go here - no hardcoded values in subsystem code.

This package is split into topic files for easier navigation:
  ids.py        - CAN IDs for motors and sensors
  shooter.py    - Turret, launcher, hood, and shooter system
  conveyor.py   - Conveyor configuration
  controls.py   - Manual overrides and robot-wide settings
  simulation.py - Sim calibration values and time step

You can import from the package (from constants import CON_TURRET)
or from a specific file (from constants.shooter import CON_TURRET).
"""

from constants.ids import *
from constants.shooter import *
from constants.conveyor import *
from constants.controls import *
from constants.simulation import *
