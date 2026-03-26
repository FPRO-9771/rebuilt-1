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
    "turret_p_gain": 0.40,               # Proportional gain (volts per degree) -- drives toward target
    "turret_i_gain": 0.015,              # Integral gain -- accumulates error to push through friction
    "turret_i_max": 1.0,                 # Max integral voltage -- caps windup to prevent overshoot
    "turret_d_velocity_gain": 0.08,      # Velocity damping -- counterbalances P to prevent oscillation
    "turret_aim_inverted": True,         # Motor direction is opposite to angle convention

    # -- On-target thresholds --
    "turret_alignment_tolerance": 1.5,   # Degrees of error considered "aligned"
    "turret_on_target_max_vel": 2.0,     # Max turret velocity (rot/s) to be on-target -- prevents feeding during swing-through

    # -- Voltage limits --
    "turret_max_auto_voltage": 2,        # Max driving voltage during auto-aim
    "turret_max_brake_voltage": 2.5,     # Brake limit -- higher than drive to stop quickly
    "turret_min_move_voltage": 0.60,     # Deadband comp -- minimum voltage to overcome static friction

    # -- EMA filter --
    "turret_tx_filter_alpha": 0.85,      # EMA smoothing for tx (0=max smooth, 1=no filter)
}
