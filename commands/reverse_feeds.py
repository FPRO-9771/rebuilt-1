"""
Reverse all feed subsystems to clear a jam.

Provides a shared helper function and a Command wrapper. The helper is
called directly by ShootWhenReady (auto unjam). The Command is bound
to the operator right bumper (manual unjam).
"""

from commands2 import Command

from subsystems.h_feed import HFeed
from subsystems.v_feed import VFeed
from constants import CON_H_FEED, CON_V_FEED


def reverse_all_feeds(h_feed, v_feed):
    """Reverse H feed and V feed to clear a jam."""
    h_feed._set_voltage(CON_H_FEED["reverse_voltage"])
    v_feed._set_voltage(CON_V_FEED["reverse_voltage"])


def stop_all_feeds(h_feed, v_feed):
    """Stop H feed and V feed."""
    h_feed._stop()
    v_feed._stop()


class ReverseFeeds(Command):
    """Hold to reverse all feed subsystems (H feed, V feed)."""

    def __init__(self, h_feed: HFeed, v_feed: VFeed):
        super().__init__()
        self.h_feed = h_feed
        self.v_feed = v_feed
        self.addRequirements(h_feed, v_feed)

    def execute(self):
        reverse_all_feeds(self.h_feed, self.v_feed)

    def isFinished(self) -> bool:
        return False

    def end(self, interrupted: bool):
        stop_all_feeds(self.h_feed, self.v_feed)
