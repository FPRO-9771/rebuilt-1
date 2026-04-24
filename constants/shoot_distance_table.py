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
        (2.0, 43, 1),
        (2.5, 48, 1),
        (3.0, 53, 1),
        (3.5, 59, 1.1),
        (4.0, 64, 1.2),
        (4.5, 71, 1.3),
        (5.0, 77, 2),
        (8, 100, 2),
    ],

    # Manual shoot stick mapping -- maps joystick Y to virtual distance,
    # then looks up RPS from the distance table above.
    # Stick -1 = min, stick 0 = center, stick +1 = max.
    "manual_min_distance": 2,     # Stick full back
    "manual_center_distance": 3,  # Stick at rest
    "manual_max_distance": 4,     # Stick full forward
}
