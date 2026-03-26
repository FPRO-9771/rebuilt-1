"""
Auto-shoot constants: movement compensation while shooting.

Controls how the shooter adjusts for robot movement. Two compensations:
  - Angle compensation (velocity lead): aims the turret ahead of the
    Hub so the ball curves into it during flight (lateral movement).
  - Distance compensation: adjusts the lookup distance so the launcher
    fires harder or softer based on closing/retreating speed.

Both use flight_time_s from the distance table (constants/shoot_distance_table.py)
to determine how long the ball is in the air. Longer flight time = larger
corrections.

To tune:
  1. Measure flight times with a stopwatch at each distance and update
     flight_time_s in the distance table (constants/shoot_distance_table.py).
  2. If shots still miss laterally while strafing, adjust
     velocity_lead_gain (below 1.0 = less lead, above 1.0 = more).
"""

CON_AUTO_SHOOT = {
    # Master on/off for angle compensation (velocity lead).
    # When False, the turret aims directly at the Hub with no lead.
    # Distance compensation is always active.
    "velocity_lead_enabled": True,

    # Multiplier on the physics-based lead angle.
    # 1.0 = trust the physics (tangential velocity * flight time).
    # Increase if balls miss in the direction of travel.
    # Decrease if balls miss opposite to the direction of travel.
    "velocity_lead_gain": 1.0,

    # Multiplier on the distance correction for closing/retreating speed.
    # 1.0 = bare physics (closing_speed * flight_time). This under-corrects
    # because ball range grows faster than linearly with speed (projectile
    # physics + drag on foam balls). Increase until shots at 2-3m while
    # retreating no longer fall short.
    # Start at 2.0 and tune down if shots overshoot while retreating.
    "distance_correction_gain": 2.0,

    # Minimum distance (meters) for compensation to activate.
    # Below this range, flight time is negligible and lead/distance
    # corrections would be noisy. Both modules skip correction when
    # distance is at or below this value.
    "min_distance": 0.5,

    # Cycles off-target before stopping feed (~400ms at 50Hz).
    # Prevents feeder stutter when turret oscillates near the threshold.
    "feed_off_target_debounce": 20,
}
