"""
Auto-aim constants: turret PD controller, voltage limits, and filtering.

These control how CoordinateAim drives the turret toward the Hub.
The PD controller, EMA filter, deadband compensation, and on-target
logic are all tuned here.

The distance table (constants/shoot_distance_table.py) is shared with
regular shooting -- auto-aim uses flight_time_s from that table
for velocity lead calculations.
"""

CON_AUTO_AIM = {
    # -- PD gains --
    "turret_p_gain": 0.47,               # Modest bump from 0.44 -- mid-range speed without spiking peak tvel
    "turret_i_gain": 0.008,              # Reduced -- much less friction to push through
    "turret_i_max": 0.4,                 # Low cap -- ~4x static friction (kS=0.10)
    "turret_d_velocity_gain": 0.19,      # Pulled back from 0.22 -- 0.22 sustained near-target oscillation
    "turret_aim_inverted": True,         # Motor direction is opposite to angle convention

    # -- On-target thresholds --
    "turret_alignment_tolerance": 1.5,   # Degrees of error considered "aligned"
    "turret_on_target_max_vel": 2.0,     # Max turret velocity (rot/s) to be on-target

    # -- Voltage limits --
    "turret_max_auto_voltage": 4,     # Modest bump from 2.2 -- limits peak speed so D can brake in time
    "turret_max_brake_voltage": 0.5,     # Bumped from 2.6 -- significantly more brake capacity
    "turret_min_move_voltage": 0.18,     # Just above kS (0.10) -- avoids jolt from old 0.60

    # -- EMA filter --
    "turret_tx_filter_alpha": 0.90,      # Modest bump from 0.88 -- slightly faster response
}
