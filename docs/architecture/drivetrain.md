# Swerve Drivetrain Setup

**Team 9771 FPRO - 2026**

This doc covers configuring and wrapping the Phoenix 6 swerve drivetrain.

> **When to read this:** You're setting up, configuring, or tuning the swerve drivetrain.

---

## Phoenix Tuner X Workflow

1. **Configure each module in Phoenix Tuner X:**
   - Set CAN IDs for drive motor, steer motor, CANcoder
   - Calibrate CANcoder offset (wheels straight forward)

2. **Use Swerve Generator:**
   - Enter physical dimensions
   - Enter gear ratios
   - Export to `generated/tuner_constants.py`

3. **Don't edit the generated file by hand.** If you need to change something, re-run the generator.

---

## Drivetrain Wrapper

```python
# subsystems/drivetrain.py

from generated.tuner_constants import TunerConstants
from phoenix6 import swerve
from phoenix6.swerve.requests import FieldCentric, RobotCentric, SwerveDriveBrake

class Drivetrain(TunerConstants.create_drivetrain().__class__):
    """Wrapper around generated swerve drivetrain."""

    def __init__(self):
        super().__init__()
        self.field_centric = FieldCentric()
        self.robot_centric = RobotCentric()
        self.brake = SwerveDriveBrake()

    def drive_with_joystick(self, x_supplier, y_supplier, rot_supplier):
        """Default command for teleop driving."""
        return self.apply_request(lambda: (
            self.field_centric
                .with_velocity_x(x_supplier() * CON_ROBOT["max_speed_mps"])
                .with_velocity_y(y_supplier() * CON_ROBOT["max_speed_mps"])
                .with_rotational_rate(rot_supplier() * CON_ROBOT["max_angular_rate"])
        ))

    def stop(self):
        return self.apply_request(lambda: self.brake)
```

**From phoenix-v1:** The Phoenix 6 swerve implementation worked well. The key is trusting the generated config and not fighting it.

---

**See also:**
- [Hardware & Subsystems](hardware-and-subsystems.md) - Hardware abstraction layer used by the drivetrain
- [Commands & Controls](commands-and-controls.md) - Wiring joystick controls to drivetrain
- [Testing & Simulation](testing-and-simulation.md) - Physics simulation for drivetrain testing
