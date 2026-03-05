"""
Controller binding modules.
Keeps robot_container short by grouping bindings by role.
"""

from .operator_controls import configure_operator
from .driver_controls import configure_driver

__all__ = ["configure_operator", "configure_driver"]
