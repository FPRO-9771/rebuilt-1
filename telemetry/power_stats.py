"""
Running stat accumulators for PowerMonitor.

One GroupStats per (subsystem group, phase). One BatteryStats per phase.
All stats are updated in-place each loop with fixed-size state (no growing
lists) so cost stays O(1) regardless of match length.
"""

BROWNOUT_THRESHOLD_V = 6.8


class GroupStats:
    """Running current/energy stats for one subsystem group, one phase."""

    __slots__ = ("samples", "sum_amps", "peak_amps", "peak_motor",
                 "peak_time_s", "sum_volt_amp_s")

    def __init__(self):
        self.samples = 0
        self.sum_amps = 0.0
        self.peak_amps = 0.0
        self.peak_motor = ""
        self.peak_time_s = 0.0
        self.sum_volt_amp_s = 0.0  # battery_v * total_amps * dt, integrated

    def accumulate(self, total_amps: float, peak_amps: float, peak_label: str,
                   battery_v: float, t_s: float, dt_s: float) -> None:
        self.samples += 1
        self.sum_amps += total_amps
        if peak_amps > self.peak_amps:
            self.peak_amps = peak_amps
            self.peak_motor = peak_label
            self.peak_time_s = t_s
        self.sum_volt_amp_s += battery_v * total_amps * dt_s

    @property
    def avg_amps(self) -> float:
        return self.sum_amps / self.samples if self.samples else 0.0

    @property
    def wh(self) -> float:
        return self.sum_volt_amp_s / 3600.0


class BatteryStats:
    """Running battery voltage stats for one phase."""

    __slots__ = ("samples", "sum_v", "min_v", "min_time_s", "start_v",
                 "time_below_brownout_s", "brownout_events", "_in_brownout")

    def __init__(self):
        self.samples = 0
        self.sum_v = 0.0
        self.min_v = float("inf")
        self.min_time_s = 0.0
        self.start_v = 0.0
        self.time_below_brownout_s = 0.0
        self.brownout_events = 0
        self._in_brownout = False

    def accumulate(self, v: float, t_s: float, dt_s: float) -> None:
        if self.samples == 0:
            self.start_v = v
        self.samples += 1
        self.sum_v += v
        if v < self.min_v:
            self.min_v = v
            self.min_time_s = t_s
        if v < BROWNOUT_THRESHOLD_V:
            self.time_below_brownout_s += dt_s
            if not self._in_brownout:
                self._in_brownout = True
                self.brownout_events += 1
        else:
            self._in_brownout = False

    @property
    def avg_v(self) -> float:
        return self.sum_v / self.samples if self.samples else 0.0
