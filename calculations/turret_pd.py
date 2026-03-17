"""
PD + feedforward turret voltage calculation.

Pure control math: takes the current aiming error, turret velocity,
and robot lateral speed, and returns the voltage to apply.

Sqrt-P compresses large errors for gradual ramp instead of saturation.
D damps turret velocity to prevent overshoot.
Feedforward pre-compensates for lateral robot motion.
Asymmetric clamp allows harder braking than driving.
Deadband comp overcomes static friction from standstill.
"""

import math


def compute_turret_voltage(filtered_tx, turret_vel, vy, aim_sign, config):
    """Compute turret voltage from aiming error and turret state.

    Args:
        filtered_tx: smoothed tx error (degrees, positive = target right)
        turret_vel: current turret velocity (rotations/sec)
        vy: robot lateral velocity (m/s), used for feedforward
        aim_sign: +1 or -1, flips voltage direction if turret is inverted
        config: CON_SHOOTER dict with PD gains and limits

    Returns:
        (voltage, p_term, d_term, ff_term, raw_voltage) tuple.
        voltage is clamped and deadband-compensated, ready to apply.
        The individual terms are returned for logging.
    """
    # --- P term: sqrt compression so large errors don't saturate ---
    abs_tx = abs(filtered_tx)
    p_term = (math.sqrt(abs_tx) * math.copysign(1, filtered_tx)
              * config["turret_p_gain"])

    # --- D term: damp turret velocity directly (not tx derivative) ---
    d_term = -turret_vel * config["turret_d_velocity_gain"]

    # --- Feedforward: pre-compensate for lateral robot movement ---
    ff_term = vy * config["turret_velocity_ff_gain"] * aim_sign

    raw_voltage = p_term * aim_sign + d_term + ff_term

    # --- Clamp: asymmetric limits (brake harder than drive) ---
    if turret_vel != 0 and (raw_voltage * turret_vel) < 0:
        max_v = config["turret_max_brake_voltage"]
    else:
        max_v = config["turret_max_auto_voltage"]
    voltage = max(-max_v, min(raw_voltage, max_v))

    # --- Deadband comp: ensure voltage meets static friction threshold ---
    # Use higher velocity threshold to avoid kick-stop-kick oscillation.
    # Once moving above this speed the normal PD output takes over smoothly.
    min_move = config["turret_min_move_voltage"]
    if (abs(turret_vel) < 0.4
            and abs(voltage) > 0.01
            and abs(voltage) < min_move):
        voltage = math.copysign(min_move, voltage)

    return voltage, p_term, d_term, ff_term, raw_voltage
