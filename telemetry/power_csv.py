"""
CSV writers for PowerMonitor.

Two files land in the output dir on every disable:
  summary.csv              - one row appended per match, aggregate stats
  match_<YYYYMMDD_HHMMSS>.csv - per-match time-series (one row per 50 ms loop)

Feed the CSVs to Claude with docs/power-monitor.md's intro prompt.
"""

import csv
import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from utils.logger import get_logger

if TYPE_CHECKING:
    from telemetry.power_monitor import PowerMonitor

_log = get_logger("power_monitor")

_PHASES = ("auto", "teleop")
_LOOP_PERIOD_S = 0.050


def resolve_log_dir() -> Path:
    """/home/lvuser/power_logs on the real robot, ./power_logs elsewhere."""
    try:
        import wpilib
        if wpilib.RobotBase.isReal():
            return Path("/home/lvuser/power_logs")
    except Exception:
        pass
    return Path.cwd() / "power_logs"


def make_csv_writer(output_dir: Path) -> Callable[["PowerMonitor"], None]:
    """Return a callable suitable for PowerMonitor(csv_writer=...)."""
    def write(monitor: "PowerMonitor") -> None:
        if not _ensure_dir(output_dir):
            return
        epoch = monitor.match_started_epoch or time.time()
        human = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(epoch))
        file_stamp = time.strftime("%Y%m%d_%H%M%S", time.localtime(epoch))
        _append_summary(output_dir / "summary.csv", monitor, human)
        _write_time_series(output_dir / f"match_{file_stamp}.csv", monitor)
        _log.warning(f"power logs written to {output_dir}")
    return write


# --- File utilities ---

def _ensure_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        _log.warning(f"could not create power log dir {path}: {e}")
        return False


# --- Summary CSV ---

def _summary_headers(group_names) -> list[str]:
    headers = ["started_at"]
    for phase in _PHASES:
        headers += [
            f"{phase}_samples", f"{phase}_duration_s",
            f"{phase}_batt_start_v", f"{phase}_batt_min_v",
            f"{phase}_batt_min_t_s", f"{phase}_batt_avg_v",
            f"{phase}_brownouts", f"{phase}_time_below_brownout_s",
        ]
        for g in group_names:
            headers += [
                f"{g}_{phase}_peak_a",
                f"{g}_{phase}_peak_motor",
                f"{g}_{phase}_peak_t_s",
                f"{g}_{phase}_avg_a",
                f"{g}_{phase}_wh",
            ]
    return headers


def _summary_row(monitor: "PowerMonitor", started_at: str) -> list:
    row: list = [started_at]
    for phase in _PHASES:
        b = monitor.phase_battery(phase)
        row += [
            b.samples,
            f"{b.samples * _LOOP_PERIOD_S:.2f}",
            f"{b.start_v:.2f}" if b.samples else "",
            f"{b.min_v:.2f}" if b.samples else "",
            f"{b.min_time_s:.2f}" if b.samples else "",
            f"{b.avg_v:.2f}" if b.samples else "",
            b.brownout_events,
            f"{b.time_below_brownout_s:.3f}",
        ]
        for g in monitor.group_names:
            s = monitor.phase_stats(g, phase)
            row += [
                f"{s.peak_amps:.1f}" if s.samples else "",
                s.peak_motor,
                f"{s.peak_time_s:.2f}" if s.samples else "",
                f"{s.avg_amps:.1f}" if s.samples else "",
                f"{s.wh:.3f}" if s.samples else "",
            ]
    return row


def _append_summary(path: Path, monitor: "PowerMonitor", started_at: str) -> None:
    need_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="") as f:
        w = csv.writer(f)
        if need_header:
            w.writerow(_summary_headers(monitor.group_names))
        w.writerow(_summary_row(monitor, started_at))


# --- Time-series CSV ---

def _time_series_headers(group_names) -> list[str]:
    return ["t_s", "phase", "battery_v"] + [f"{g}_a" for g in group_names]


def _write_time_series(path: Path, monitor: "PowerMonitor") -> None:
    headers = _time_series_headers(monitor.group_names)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for row in monitor.time_series:
            # row = (t_s, phase, battery_v, *group_totals)
            t_s, phase, batt_v, *groups = row
            w.writerow(
                [f"{t_s:.3f}", phase, f"{batt_v:.3f}"]
                + [f"{a:.1f}" for a in groups]
            )
