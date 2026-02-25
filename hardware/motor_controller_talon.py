"""
TalonFX (KrakenX60) motor controller implementation.
Real hardware using Phoenix 6.
"""

from .motor_controller import MotorController


class TalonFXController(MotorController):
    """Real TalonFX/KrakenX60 implementation using Phoenix 6."""

    def __init__(self, can_id: int, inverted: bool = False, slot0: dict | None = None):
        from phoenix6.hardware import TalonFX
        from phoenix6.configs import TalonFXConfiguration
        from phoenix6.signals import InvertedValue

        self.motor = TalonFX(can_id)
        self._last_voltage = 0.0

        config = TalonFXConfiguration()
        needs_apply = False

        if inverted:
            config.motor_output.inverted = InvertedValue.CLOCKWISE_POSITIVE
            needs_apply = True

        if slot0:
            config.slot0.k_p = slot0.get("kP", 0)
            config.slot0.k_i = slot0.get("kI", 0)
            config.slot0.k_d = slot0.get("kD", 0)
            config.slot0.k_s = slot0.get("kS", 0)
            config.slot0.k_v = slot0.get("kV", 0)
            config.slot0.k_a = slot0.get("kA", 0)
            config.slot0.k_g = slot0.get("kG", 0)
            needs_apply = True

        if needs_apply:
            self.motor.configurator.apply(config)

    def set_voltage(self, volts: float) -> None:
        from phoenix6.controls import VoltageOut

        self._last_voltage = volts
        self.motor.set_control(VoltageOut(volts))

    def set_velocity(self, velocity: float, feedforward: float = 0) -> None:
        from phoenix6.controls import VelocityVoltage

        self.motor.set_control(
            VelocityVoltage(velocity).with_feed_forward(feedforward)
        )

    def set_position(self, position: float, feedforward: float = 0) -> None:
        from phoenix6.controls import PositionVoltage

        self.motor.set_control(
            PositionVoltage(position).with_feed_forward(feedforward)
        )

    def get_position(self) -> float:
        return self.motor.get_position().value

    def get_velocity(self) -> float:
        return self.motor.get_velocity().value

    def zero_position(self) -> None:
        self.motor.set_position(0)

    def stop(self) -> None:
        self.set_voltage(0)
