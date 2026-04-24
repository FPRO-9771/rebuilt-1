"""
Configuration constants for Team 9771 Robot 2026.
All magic numbers go here - no hardcoded values in subsystem code.

This package is split into topic files for easier navigation:
  ids.py              - CAN IDs for motors and sensors
  shoot_hardware.py   - Turret, launcher motor configs
  shoot_distance_table.py - Distance lookup table (shared by shooting and auto-aim)
  shoot_auto_aim.py   - Turret PD controller, voltage limits, filtering
  shoot_auto_shoot.py - Movement compensation (velocity lead, distance correction)
  feed.py             - Horizontal and vertical feed configuration
  intake.py           - Intake lever arm configuration
  intake_spinner.py   - Intake spinner configuration
  intake_hopper_agitate.py - Hopper agitate command configuration
  controls.py         - Manual overrides and robot-wide settings
  simulation.py       - Sim calibration values and time step
  debug.py            - Debug logging toggles
  vision.py           - Camera names and hostnames
  match.py            - Alliance colors, starting poses, Hub positions
  pose.py             - Robot pose and turret geometry
  telemetry.py        - Telemetry dashboard configuration

You can import from the package (from constants import CON_TURRET_MINION)
or from a specific file (from constants.shoot_hardware import CON_TURRET_MINION).
"""

from constants.ids import *
from constants.shoot_hardware import *
from constants.shoot_distance_table import *
from constants.shoot_auto_aim import *
from constants.shoot_auto_shoot import *
from constants.feed import *
from constants.intake import *
from constants.intake_spinner import *
from constants.intake_hopper_agitate import *
from constants.controls import *
from constants.simulation import *
from constants.telemetry import *
from constants.debug import *
from constants.vision import *
from constants.match import *
from constants.pose import *
