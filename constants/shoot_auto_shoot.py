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
  3. If shots miss while driving toward the hub, tune
     distance_correction_gain_closing. If they miss while driving
     away, tune distance_correction_gain_retreating.
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

    # Radial motion compensation is split into two gains because ball range
    # scales roughly with v^2, so a given closing speed and retreating speed
    # require slightly different corrections for the RPS lookup to land the
    # ball on target. Applied as:
    #   corrected = distance - closing_speed * flight_time * gain
    # where gain is closing when closing_speed > 0, retreating otherwise.
    #
    # Tune closing first: drive straight at the hub at a steady speed (~1 m/s)
    # from a known distance and shoot.
    #   - Shots fall short -> gain too high (lower it)
    #   - Shots go long    -> gain too low (raise it)
    # Then repeat for retreating with the other gain. Expect retreating to
    # end up a bit higher than closing.
    "distance_correction_gain_closing": 0.7,
    "distance_correction_gain_retreating": 0.3,

    # Minimum distance (meters) for compensation to activate.
    # Below this range, flight time is negligible and lead/distance
    # corrections would be noisy. Both modules skip correction when
    # distance is at or below this value.
    "min_distance": 0.5,

    # Cycles off-target before stopping feed (~400ms at 50Hz).
    # Prevents feeder stutter when turret oscillates near the threshold.
    "feed_off_target_debounce": 20,
}
