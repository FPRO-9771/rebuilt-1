# Power Monitor

**Team 9771 FPRO - 2026**

Post-match power logging for brownout diagnosis. Accumulates per-subsystem current draw and battery voltage during auto/teleop, then writes two CSVs on disable.

> **When to read this:** You just browned out and want to know why, or you're pulling logs to feed to Claude for a multi-match assessment.

---

## What gets logged

Four subsystem groups are tracked:

| Group | Motors |
|-------|--------|
| `drivetrain` | 4 drive + 4 steer swerve motors (KrakenX60) |
| `intake_arms` | intake-left + intake-right |
| `intake_spinner` | intake spinner |
| `shooting` | h-feed + v-feed + turret (Minion) + launcher |

Plus battery voltage from `RobotController.getBatteryVoltage()`.

Sampled every loop (50 ms) during `autonomousPeriodic` and `teleopPeriodic`. Dumped on `disabledInit`.

Turn the whole thing on/off with `DEBUG["power_monitor"]` in `constants/debug.py`.

---

## Files produced

On the robot, everything lands in `/home/lvuser/power_logs/`.

| File | When written | Purpose |
|------|--------------|---------|
| `summary.csv` | Appended on every disable | One row per match -- compare many matches at a glance |
| `match_<YYYYMMDD_HHMMSS>.csv` | New file on every disable | Per-match time-series -- correlate current spikes to battery dips |

The DS console also prints a text summary via `_log.warning`, so it lands in the `.dsevents` file the DS records on your laptop.

---

## Pulling the logs from the roboRIO

From your laptop, with the robot on the same network:

```bash
# Copy every log to ./power_logs on your laptop
scp -r admin@10.97.71.2:/home/lvuser/power_logs .

# Or just the summary (lighter, for quick comparison)
scp admin@10.97.71.2:/home/lvuser/power_logs/summary.csv .

# Or a specific match by timestamp
scp admin@10.97.71.2:/home/lvuser/power_logs/match_20261101_143025.csv .
```

To look around first:

```bash
ssh admin@10.97.71.2
ls -lh /home/lvuser/power_logs/
```

To clear the logs (e.g. after a practice block):

```bash
ssh admin@10.97.71.2 "rm -f /home/lvuser/power_logs/*"
```

---

## Column reference

### `summary.csv`

One row per match. Units: amps (A), volts (V), seconds (s), watt-hours (Wh).

| Column | Meaning |
|--------|---------|
| `started_at` | Wall-clock time of the first sample |
| `<phase>_samples` | Number of loops sampled in that phase |
| `<phase>_duration_s` | `samples * 0.050` |
| `<phase>_batt_start_v` | Battery voltage at first sample of phase |
| `<phase>_batt_min_v` | Minimum battery voltage seen in phase |
| `<phase>_batt_min_t_s` | Phase-relative time of the battery minimum |
| `<phase>_batt_avg_v` | Mean battery voltage across phase |
| `<phase>_brownouts` | Count of distinct dips below 6.8 V |
| `<phase>_time_below_brownout_s` | Total time spent below 6.8 V |
| `<group>_<phase>_peak_a` | Highest instantaneous single-motor current in the group |
| `<group>_<phase>_peak_motor` | Which motor hit `peak_a` (e.g. `fr_drive`) |
| `<group>_<phase>_peak_t_s` | Phase-relative time of that peak |
| `<group>_<phase>_avg_a` | Mean group-total current (sum of motors in group) |
| `<group>_<phase>_wh` | Energy burned by the group (V x A integrated) |

`<phase>` is `auto` or `teleop`. `<group>` is `drivetrain`, `intake_arms`, `intake_spinner`, or `shooting`.

### `match_<timestamp>.csv`

One row per 50 ms loop.

| Column | Meaning |
|--------|---------|
| `t_s` | Phase-relative elapsed seconds (resets when phase changes) |
| `phase` | `auto` or `teleop` |
| `battery_v` | Instantaneous battery voltage |
| `drivetrain_a` | Sum of all 8 drivetrain motor supply currents |
| `intake_arms_a` | Sum of both intake arm motors |
| `intake_spinner_a` | Spinner motor supply current |
| `shooting_a` | Sum of h-feed + v-feed + turret + launcher |

**Note on `t_s`:** phase-relative, not match-absolute. When the `phase` column flips from `auto` to `teleop`, `t_s` resets to 0.

---

## Feeding to Claude

Copy everything below the `--- BEGIN PROMPT ---` line into a chat, then paste the CSV contents (summary first, then one or more `match_*.csv` files).

```
--- BEGIN PROMPT ---

I'm diagnosing brownouts on FRC Team 9771's 2026 robot (codename FPRO/Rebuilt).
Help me figure out what is causing them and what we should change.

Context on the robot:
- Swerve drivetrain: 4 drive + 4 steer Kraken X60 motors, 80 A stator / 50 A
  supply limit on drive, 60 A stator / 35 A supply on steer.
- Intake arms: two motors (left/right) raising/lowering a lever arm, 30 A
  stator / 10 A supply limit.
- Intake spinner: one Kraken pulling Fuel in, 30 A / 10 A limits.
- Shooting: h-feed + v-feed (transport), turret (Minion via TalonFXS, small
  motor), launcher flywheel (Kraken, 60 A / 40 A limits).
- Match is 160 s: 20 s auto, 10 s transition, 4 x 25 s shifts, 30 s endgame.
- Brownout threshold in this log is battery < 6.8 V.

Files attached:
  summary.csv        - one row per match, aggregate stats
  match_*.csv        - per-match time-series, one row per 50 ms loop.
                       t_s is phase-relative (auto = 0..~20, teleop = 0..~140).

What I want from you:

1. Which subsystem is the biggest power culprit? Rank them by peak current,
   average current, and Wh consumed. Note any match-to-match outliers.

2. For each match that had a brownout event, pinpoint what was happening in
   the time-series right before the battery dipped below 6.8 V:
   - Which groups were drawing significant current?
   - Were multiple groups spiking simultaneously?
   - Was it a sudden spike or a slow climb?

3. Are the brownouts correlated with a phase (auto vs teleop), a particular
   match condition (tired battery? see batt_start_v), or a subsystem pattern?

4. Recommend concrete changes, ranked by expected brownout reduction vs.
   cost to implement. Categorize each as:
   - Driving habit (e.g. "don't hold drivetrain against obstacles")
   - Code tuning (e.g. "lower current limit on X", "stagger spin-up")
   - Mechanical (e.g. "gearing, wiring, belts")
   - Power budget (e.g. "battery health / management")

5. Flag anything unusual or unexplained you notice in the data.

Keep the analysis specific and data-driven -- cite match filenames, timestamps,
and numeric values from the CSVs.

--- END PROMPT ---
```

---

## Turning it off

If you suspect the monitor is causing loop overruns, flip the flag:

```python
# constants/debug.py
DEBUG = {
    ...
    "power_monitor": False,  # was True
    ...
}
```

`sample()` becomes a single dict lookup and early return. `dump()` skips. Nothing else in the monitor runs.

---

## Overhead

Per loop at 50 ms:
- 1 `RobotController.getBatteryVoltage()` call (no CAN traffic)
- ~14 `motor.get_supply_current()` reads (cached Phoenix 6 signals, no CAN traffic)
- ~4 accumulator updates + 1 tuple append

Under 1 ms on the Rio. If you see loop overruns appear or worsen after enabling this, check that `DEBUG["verbose"]` isn't also on (the logger is the more common culprit).

---

## See also

- `constants/debug.py` - the toggle flag
- `telemetry/power_monitor.py` - main class
- `telemetry/power_csv.py` - CSV writers
- `telemetry/power_stats.py` - accumulator classes
- `telemetry/power_monitor_setup.py` - how groups are wired
- `tests/test_power_monitor.py`, `tests/test_power_monitor_csv.py` - tests
