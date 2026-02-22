"""
TalonFX (KrakenX60) motor controller implementation.
Real hardware using Phoenix 6.
"""

from .motor_controller import MotorController


class TalonFXController(MotorController):
    """Real TalonFX/KrakenX60 implementation using Phoenix 6."""

    def __init__(self, can_id: int, inverted: bool = False):
        from phoenix6.hardware import TalonFX
        from phoenix6.configs import TalonFXConfiguration
        from phoenix6.signals import InvertedValue

        self.motor = TalonFX(can_id)
        self._last_voltage = 0.0

        if inverted:
            config = TalonFXConfiguration()
            config.motor_output.inverted = InvertedValue.CLOCKWISE_POSITIVE
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

    def stop(self) -> None:
        self.set_voltage(0)
