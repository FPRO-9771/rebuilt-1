"""
PID turret voltage calculation.

Pure control math: takes the current aiming error, turret velocity,
and integral accumulator, and returns the voltage to apply.

Sqrt-P compresses large errors for gradual ramp instead of saturation.
I accumulates error over time to push through intermittent friction.
D damps turret velocity to prevent overshoot.
Asymmetric clamp allows harder braking than driving.
Deadband comp overcomes static friction from standstill.
"""

import math


def compute_turret_voltage(filtered_tx, turret_vel, aim_sign, config,
                           i_accumulator=0.0):
    """Compute turret voltage from aiming error and turret state.

    Args:
        filtered_tx: smoothed tx error (degrees, positive = target right)
        turret_vel: current turret velocity (rotations/sec)
        aim_sign: +1 or -1, flips voltage direction if turret is inverted
        config: CON_SHOOTER dict with PID gains and limits
        i_accumulator: running sum of past errors (caller owns this state)

    Returns:
        (voltage, p_term, i_term, d_term, raw_voltage, i_accumulator) tuple.
        voltage is clamped and deadband-compensated, ready to apply.
        The individual terms are returned for logging.
        i_accumulator is the updated integral state -- caller must store it
        and pass it back next cycle.
    """
    # --- P term: sqrt compression so large errors don't saturate ---
    abs_tx = abs(filtered_tx)
    p_term = (math.sqrt(abs_tx) * math.copysign(1, filtered_tx)
              * config["turret_p_gain"])

    # --- I term: accumulate error to overcome intermittent friction ---
    i_gain = config.get("turret_i_gain", 0.0)
    i_max = config.get("turret_i_max", 0.0)
    if i_gain > 0:
        # Reset on zero-crossing to prevent overshoot
        if i_accumulator != 0 and math.copysign(1, filtered_tx) != math.copysign(1, i_accumulator):
            i_accumulator = 0.0
        i_accumulator += filtered_tx
        # Clamp accumulator to prevent windup
        if i_max > 0:
            max_accum = i_max / i_gain
            i_accumulator = max(-max_accum, min(i_accumulator, max_accum))
    i_term = i_accumulator * i_gain * aim_sign

    # --- D term: damp turret velocity directly (not tx derivative) ---
    d_term = -turret_vel * config["turret_d_velocity_gain"]

    raw_voltage = p_term * aim_sign + i_term + d_term

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

    return voltage, p_term, i_term, d_term, raw_voltage, i_accumulator
