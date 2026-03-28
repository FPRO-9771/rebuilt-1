"""
Distance lookup table and manual stick mapping.

The distance table is shared across multiple systems:
  - Regular shooting: get_shooter_settings() looks up launcher RPS
    for a given distance.
  - Auto-aim / auto-shoot: get_flight_time() looks up ball flight
    time for velocity lead and distance correction calculations.

Table format: (distance_m, launcher_rps, flight_time_s)
  - distance_m: measured distance from shooter to Hub (meters)
  - launcher_rps: flywheel speed (rotations per second)
  - flight_time_s: ball travel time (seconds) -- measure with a stopwatch
    from launch to landing in the Hub. Used by auto-shoot compensation.

Sorted by distance -- interpolated at runtime by shooter_lookup.py.
"""

CON_DISTANCE_TABLE = {
    "distance_table": [
        # (distance_m, launcher_rps, flight_time_s)
        (1.5, 33.0, 0.95),
        (2.0, 37.0, 1),
        (3.0, 47.0, 1),
        (3.5, 51.5, 1.1),
        (4.0, 58.0, 1.2),
        (4.5, 62.0, 1.3),
        (5.0, 66.0, 2),
    ],

    # Manual shoot stick mapping -- maps joystick Y to virtual distance,
    # then looks up RPS from the distance table above.
    # Stick -1 = min, stick 0 = center, stick +1 = max.
    "manual_min_distance": 1.5,     # Stick full back
    "manual_center_distance": 2.0,  # Stick at rest
    "manual_max_distance": 5.0,     # Stick full forward
}
