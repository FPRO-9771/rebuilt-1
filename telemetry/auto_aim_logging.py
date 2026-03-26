"""
Shooter system debug logging.
Structured log output showing the full auto-aim and auto-shoot pipeline.
Called by CoordinateAim and ShootWhenReady commands.

Toggle with DEBUG["auto_aim_logging"] in constants/debug.py.
This flag is independent of DEBUG["verbose"] -- you can see shooter
system logs without turning on all other debug output.
"""

from constants.debug import DEBUG
from utils.logger import get_logger

_log = get_logger("auto_aim")


def _enabled():
    """Check if auto-aim logging is active."""
    return DEBUG["verbose"] or DEBUG["auto_aim_logging"]


def _emit(msg):
    """Log at the right level depending on which flag is on.

    When auto_aim_logging is on (but verbose is off), use INFO so
    the message appears without requiring DEBUG level globally.
    When verbose is on, use DEBUG to keep it with other debug output.
    """
    if DEBUG["verbose"]:
        _log.debug(msg)
    else:
        _log.info(msg)


def log_hold(cycle, pose_x, pose_y, heading_deg,
             shooter_x, shooter_y, target_x, target_y,
             turret_pos, error_deg, distance_m, closing_mps):
    """Log when turret is on-target and holding still. Every other cycle.

    Shows inputs (where we think we are) and why we're holding.
    """
    if not _enabled() or cycle % 2 != 0:
        return
    _emit(
        f"[AIM HOLD] "
        f"pose=({pose_x:.2f},{pose_y:.2f}) hdg={heading_deg:.1f} "
        f"shooter=({shooter_x:.2f},{shooter_y:.2f}) "
        f"tgt=({target_x:.1f},{target_y:.1f}) "
        f"tpos={turret_pos:.3f} "
        f"err={error_deg:.2f} dist={distance_m:.2f} cls={closing_mps:.2f} "
        f"-- HOLD (within tolerance)"
    )


def log_drive(cycle, pose_x, pose_y, heading_deg,
              shooter_x, shooter_y, target_x, target_y,
              turret_pos, error_deg, distance_m, closing_mps,
              lead_deg, routed_error, filtered_error,
              p_term, i_term, d_term, raw_voltage, voltage,
              turret_vel, vx, vy):
    """Log PID control output when actively driving. Every other cycle.

    Shows the full pipeline: inputs -> lead -> PID terms -> voltage.
    """
    if not _enabled() or cycle % 2 != 0:
        return
    sat = "SAT" if abs(raw_voltage) > abs(voltage) else "ok"
    _emit(
        f"[AIM DRIVE] "
        f"pose=({pose_x:.2f},{pose_y:.2f}) hdg={heading_deg:.1f} "
        f"shooter=({shooter_x:.2f},{shooter_y:.2f}) "
        f"tgt=({target_x:.1f},{target_y:.1f}) "
        f"tpos={turret_pos:.3f} "
        f"| err={error_deg:.2f} dist={distance_m:.2f} cls={closing_mps:.2f} "
        f"| lead={lead_deg:.2f} "
        f"rte={routed_error:.2f} flt={filtered_error:.2f} "
        f"| P={p_term:.3f} I={i_term:.3f} D={d_term:.3f} "
        f"rv={raw_voltage:.3f} v={voltage:.3f} [{sat}] "
        f"tvel={turret_vel:.3f} "
        f"| vel=({vx:.2f},{vy:.2f})"
    )


def log_shoot(cycle, ctx, rps,
              actual_rps=None, at_speed=False, reached_speed=False,
              on_target=False, feeding=False):
    """Log auto-shoot pipeline: pose -> distance -> lookup -> motor outputs.

    Args:
        ctx: ShootContext namedtuple with pose, shooter, target, distance info
        rps: commanded launcher RPS from lookup table
        actual_rps: current launcher velocity (None if unknown)
        at_speed: True if launcher is within speed tolerance right now
        reached_speed: True if launcher has passed the one-time speed gate
        on_target: True if turret is aimed at Hub
        feeding: True if feeders are running

    Every other cycle, offset from aim logs so they interleave.
    """
    if not _enabled() or cycle % 2 != 1:
        return
    speed_str = f"actual={actual_rps:.1f}" if actual_rps is not None else "actual=--"
    flags = []
    if reached_speed:
        flags.append("UNLOCKED")
    if at_speed:
        flags.append("AT_SPEED")
    if on_target:
        flags.append("ON_TARGET")
    if feeding:
        flags.append("FEEDING")
    flag_str = " ".join(flags) if flags else "WAITING"
    _emit(
        f"[SHOOT] "
        f"pose=({ctx.pose_x:.2f},{ctx.pose_y:.2f}) hdg={ctx.heading_deg:.1f} "
        f"shooter=({ctx.shooter_x:.2f},{ctx.shooter_y:.2f}) "
        f"tgt=({ctx.target_x:.1f},{ctx.target_y:.1f}) "
        f"| rawDist={ctx.raw_distance:.2f} corrDist={ctx.corrected_distance:.2f} "
        f"cls={ctx.closing_speed_mps:.2f} "
        f"vel=({ctx.vx:.2f},{ctx.vy:.2f}) "
        f"| rps={rps:.1f} {speed_str} "
        f"| {flag_str}"
    )
