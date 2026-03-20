"""
Movement compensation constants.
Controls how the shooter adjusts for robot movement while shooting.

Two compensations exist:
  - Angle compensation: aims the turret ahead of the Hub so the ball
    curves into it during flight (lateral/tangential movement).
  - Distance compensation: adjusts the lookup distance so the launcher
    fires harder or softer based on closing/retreating speed (radial movement).

Both use flight_time_s from the distance table in shooter.py to
determine how long the ball is in the air. Longer flight time =
larger corrections.

To tune:
  1. Measure flight times with a stopwatch at each distance and
     update flight_time_s in the distance table (shooter.py).
  2. If shots still miss laterally while strafing, adjust
     velocity_lead_gain (below 1.0 = less lead, above 1.0 = more).
"""

CON_COMPENSATION = {
    # Master on/off for angle compensation (velocity lead).
    # When False, the turret aims directly at the Hub with no lead.
    # Distance compensation is always active.
    "velocity_lead_enabled": True,

    # Multiplier on the physics-based lead angle.
    # 1.0 = trust the physics (tangential velocity * flight time).
    # Increase if balls miss in the direction of travel.
    # Decrease if balls miss opposite to the direction of travel.
    "velocity_lead_gain": 1.0,

    # Minimum distance (meters) for compensation to activate.
    # Below this range, flight time is negligible and lead/distance
    # corrections would be noisy. Both modules skip correction when
    # distance is at or below this value.
    "min_distance": 0.5,
}
