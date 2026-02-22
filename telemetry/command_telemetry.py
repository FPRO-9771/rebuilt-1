"""
Command telemetry publisher.
Tracks running commands and recent command events via scheduler callbacks.
"""

import time
from collections import deque

import wpilib
from commands2 import CommandScheduler

from constants import CON_TELEMETRY

# Internal command names to filter out of the log
_FILTERED_PREFIXES = ("_", "Instant", "PerpetualCommand", "RunCommand")


class CommandTelemetry:
    """Publishes active commands and a recent-events table."""

    def __init__(self):
        max_events = CON_TELEMETRY["max_recent_commands"]
        self._recent_events = deque(maxlen=max_events)

    def setup(self):
        """Register scheduler callbacks. Call once during robot init."""
        scheduler = CommandScheduler.getInstance()
        scheduler.onCommandInitialize(lambda cmd: self._on_event("START", cmd))
        scheduler.onCommandFinish(lambda cmd: self._on_event("END", cmd))

    def _on_event(self, event_type, command):
        """Record a command event, filtering noisy internals."""
        name = command.getName()
        if name.startswith(_FILTERED_PREFIXES):
            return
        timestamp = time.strftime("%H:%M:%S")
        self._recent_events.appendleft((timestamp, event_type, name))

    def update(self):
        """Publish command data to SmartDashboard."""
        sd = wpilib.SmartDashboard

        # Active commands — comma-separated list
        scheduled = CommandScheduler.getInstance()._scheduledCommands
        names = [c.getName() for c in scheduled
                 if not c.getName().startswith(_FILTERED_PREFIXES)]
        sd.putString("Commands/Active", ", ".join(names) if names else "(none)")

        # Recent events — formatted ASCII table
        lines = ["Time     | Event | Command"]
        for ts, event, name in self._recent_events:
            lines.append(f"{ts} | {event:<5} | {name}")
        sd.putString("Commands/Recent", "\n".join(lines))
