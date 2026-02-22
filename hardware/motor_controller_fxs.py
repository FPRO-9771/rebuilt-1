"""
TalonFXS motor controller implementation.
Used for WCP motors connected via a TalonFXS controller.
"""

from .motor_controller import MotorController


class TalonFXSController(MotorController):
    """
    Real TalonFXS implementation using Phoenix 6.
    Used for motors like WCP that connect through a TalonFXS.
    """

    def __init__(self, can_id: int, inverted: bool = False):
        from phoenix6.hardware import TalonFXS
        from phoenix6.configs import TalonFXSConfiguration
        from phoenix6.signals import InvertedValue

        self.motor = TalonFXS(can_id)
        self._last_voltage = 0.0

        if inverted:
            config = TalonFXSConfiguration()
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
