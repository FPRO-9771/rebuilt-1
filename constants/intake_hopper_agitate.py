"""
Intake hopper agitate configuration.

Used by commands/intake_hopper_agitate.py. The command cycles the intake
arm between down_position and a point `up_offset_rotations` above it while
running the spinner at `spin_voltage`. The motion agitates Fuel in the
hopper to help unjam balls when the robot is stationary and shooting.

Tuning knobs:
  - Too slow / arm never reaches peak?   Raise arm_voltage.
  - Too jerky / rapid reversal?          Raise dwell_cycles (or lower arm_voltage).
  - Peak too high / too low?             Adjust up_offset_rotations.
  - Spinner pulling balls out of hopper? Lower spin_voltage.

All values here are TUNE-on-robot. Tests derive from
TEST_CON_INTAKE_HOPPER_AGITATE in tests/conftest.py, not these production values.
"""

CON_INTAKE_HOPPER_AGITATE = {
    # --- Motion shape ---
    "up_offset_rotations": 0.5,     # How far above down_position the arm peaks (arm rotations).
                                    # 1.0 is about 20% of full travel with down_position = -4.91.
    "position_tolerance": 0.05,     # Distance from a target where direction flips (rotations).

    # --- Speed knobs ---
    # Jerkiness = (arm_voltage high) + (dwell_cycles low). Dial either down to smooth out.
    "arm_voltage": 1,             # Magnitude of voltage applied to arm during a swing.
                                    # Sign is set by code: + toward up_position, - toward down_position.
    "dwell_cycles": 3,              # Cycles (20 ms each) to hold 0V brake at each end of a swing
                                    # before reversing. 3 = 60 ms pause. Higher = smoother + slower.

    # --- Spinner ---
    "spin_voltage": 4.0,            # Slower than normal intake spin so balls jostle rather than feed.

    # --- Gating (used by the operator_controls binding, not the command itself) ---
    "stationary_speed_threshold": 0.15,  # m/s. Robot is "stationary" below this speed.
                                         # Only when stationary + auto-shooting does agitate run.
}
