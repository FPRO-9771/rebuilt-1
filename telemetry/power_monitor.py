"""
Power monitor: accumulates per-subsystem current draw and battery voltage
during auto/teleop, dumps a summary table to the log on disable.

Purpose is post-match brownout diagnosis. Read the log after a match to see
which group drew the most, when the battery dipped lowest, and whether
brownouts clustered in auto or teleop.

Gated by DEBUG["power_monitor"]. When False, sample() and dump() are no-ops.
"""

import time
from typing import Callable, Dict, List, Tuple, Optional

from constants.debug import DEBUG
from telemetry.power_stats import GroupStats, BatteryStats, BROWNOUT_THRESHOLD_V
from utils.logger import get_logger

_log = get_logger("power_monitor")

# Fixed loop-period assumption -- matches robot.py _LOOP_PERIOD (50 ms).
# Used for time-below-brownout and Wh integration. Keeping it fixed (rather
# than measuring per-loop dt) avoids one monotonic() subtraction per sample.
_LOOP_PERIOD_S = 0.050

_PHASES = ("auto", "teleop")

CurrentReader = Callable[[], float]
MotorHandle = Tuple[str, CurrentReader]


class PowerMonitor:
    """
    Usage:
        monitor = PowerMonitor({
            "drivetrain":      [("drive_fl", reader), ("steer_fl", reader), ...],
            "intake_arms":     [...],
            "intake_spinner":  [...],
            "shooting":        [...],
        })
        # robot.py autonomousPeriodic: monitor.sample("auto")
        # robot.py teleopPeriodic:     monitor.sample("teleop")
        # robot.py disabledInit:       monitor.dump()
    """

    def __init__(self, groups: Dict[str, List[MotorHandle]],
                 battery_voltage_supplier: Optional[Callable[[], float]] = None,
                 csv_writer: Optional[Callable[["PowerMonitor"], None]] = None):
        self._groups = groups
        self._group_names: Tuple[str, ...] = tuple(groups.keys())
        self._stats: Dict[str, Dict[str, GroupStats]] = {
            g: {p: GroupStats() for p in _PHASES} for g in groups
        }
        self._battery: Dict[str, BatteryStats] = {
            p: BatteryStats() for p in _PHASES
        }
        self._phase_start_s: Dict[str, Optional[float]] = {p: None for p in _PHASES}
        # Per-loop time-series row: (t_s, phase, battery_v, *group_totals_amps)
        self._time_series: List[tuple] = []
        self._csv_writer = csv_writer
        self._match_started_epoch: Optional[float] = None

        if battery_voltage_supplier is None:
            from wpilib import RobotController
            battery_voltage_supplier = RobotController.getBatteryVoltage
        self._read_battery = battery_voltage_supplier

        total_motors = sum(len(m) for m in groups.values())
        _log.info(
            f"PowerMonitor init: {len(groups)} groups, {total_motors} motors, "
            f"enabled={DEBUG['power_monitor']}"
        )

    def sample(self, phase: str) -> None:
        """Sample current + battery once. Called from auto/teleop periodic."""
        if not DEBUG["power_monitor"]:
            return
        if phase not in _PHASES:
            return

        now = time.monotonic()
        if self._phase_start_s[phase] is None:
            self._phase_start_s[phase] = now
        if self._match_started_epoch is None:
            self._match_started_epoch = time.time()
        t_s = now - self._phase_start_s[phase]

        battery_v = self._read_battery()
        self._battery[phase].accumulate(battery_v, t_s, _LOOP_PERIOD_S)

        totals_by_group: Dict[str, float] = {}
        for group_name, motors in self._groups.items():
            total_a = 0.0
            peak_a = 0.0
            peak_label = ""
            for label, reader in motors:
                try:
                    a = reader()
                except Exception:
                    # Missing hardware, mock, or transient read error -- skip.
                    continue
                total_a += a
                if a > peak_a:
                    peak_a = a
                    peak_label = label
            totals_by_group[group_name] = total_a
            self._stats[group_name][phase].accumulate(
                total_a, peak_a, peak_label, battery_v, t_s, _LOOP_PERIOD_S
            )

        # Per-loop time-series row (fixed group column order).
        self._time_series.append(
            (t_s, phase, battery_v)
            + tuple(totals_by_group[g] for g in self._group_names)
        )

    def dump(self) -> None:
        """Format and log the summary. Resets state so the next match starts clean."""
        if not DEBUG["power_monitor"]:
            return
        if not any(self._battery[p].samples > 0 for p in _PHASES):
            return

        _log.warning("=== POWER MONITOR MATCH SUMMARY ===")
        for phase in _PHASES:
            b = self._battery[phase]
            if b.samples == 0:
                continue
            _log.warning(
                f"[{phase}] duration={b.samples * _LOOP_PERIOD_S:.1f}s  "
                f"battery: min={b.min_v:.2f}V @ t={b.min_time_s:.1f}s  "
                f"avg={b.avg_v:.2f}V  brownouts={b.brownout_events}  "
                f"time<{BROWNOUT_THRESHOLD_V}V={b.time_below_brownout_s:.2f}s"
            )
            _log.warning(
                f"[{phase}] {'group':<16} {'peak A':>7} {'avg A':>7} "
                f"{'Wh':>6}  peak_motor"
            )
            for group_name in self._groups:
                s = self._stats[group_name][phase]
                if s.samples == 0:
                    continue
                peak_tail = (
                    f"{s.peak_motor} @ t={s.peak_time_s:.1f}s"
                    if s.peak_motor else ""
                )
                _log.warning(
                    f"[{phase}] {group_name:<16} "
                    f"{s.peak_amps:>7.1f} {s.avg_amps:>7.1f} {s.wh:>6.2f}  "
                    f"{peak_tail}"
                )
        _log.warning("=== END POWER SUMMARY ===")

        if self._csv_writer is not None:
            try:
                self._csv_writer(self)
            except Exception as e:
                _log.warning(f"CSV write failed: {e}")

        self._reset()

    def _reset(self) -> None:
        for group_name in self._groups:
            for phase in _PHASES:
                self._stats[group_name][phase] = GroupStats()
        for phase in _PHASES:
            self._battery[phase] = BatteryStats()
            self._phase_start_s[phase] = None
        self._time_series = []
        self._match_started_epoch = None

    # --- Accessors for the CSV writer ---

    @property
    def group_names(self) -> Tuple[str, ...]:
        return self._group_names

    @property
    def time_series(self) -> List[tuple]:
        return self._time_series

    def phase_stats(self, group: str, phase: str) -> GroupStats:
        return self._stats[group][phase]

    def phase_battery(self, phase: str) -> BatteryStats:
        return self._battery[phase]

    @property
    def match_started_epoch(self) -> Optional[float]:
        return self._match_started_epoch
