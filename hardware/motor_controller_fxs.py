"""
TalonFXS motor controller implementation.
Used for WCP motors connected via a TalonFXS controller.
"""

from .motor_controller import MotorController
from utils.logger import get_logger

_log = get_logger("TalonFXS")


class TalonFXSController(MotorController):
    """
    Real TalonFXS implementation using Phoenix 6.
    Used for motors like WCP that connect through a TalonFXS.
    """

    def __init__(self, can_id: int, inverted: bool = False, brake: bool = False,
                 slot0: dict | None = None, bus: str = "", current_limit: dict | None = None):
        from phoenix6.hardware import TalonFXS
        from phoenix6.configs import TalonFXSConfiguration, CurrentLimitsConfigs
        from phoenix6.signals import InvertedValue, MotorArrangementValue, NeutralModeValue

        self._can_id = can_id
        self.motor = TalonFXS(can_id, bus)
        self._last_voltage = 0.0
        self._last_pos_target = None

        _log.info(f"CAN {can_id}: TalonFXS created, inverted={inverted}")

        config = TalonFXSConfiguration()
        config.commutation.motor_arrangement = MotorArrangementValue.MINION_JST
        config.motor_output.neutral_mode = NeutralModeValue.BRAKE if brake else NeutralModeValue.COAST
        needs_apply = True
        _log.info(f"CAN {can_id}: Motor arrangement set to Minion JST, brake={brake}")

        if inverted:
            config.motor_output.inverted = InvertedValue.CLOCKWISE_POSITIVE
            _log.info(f"CAN {can_id}: Inversion configured")

        if slot0:
            config.slot0.k_p = slot0.get("kP", 0)
            config.slot0.k_i = slot0.get("kI", 0)
            config.slot0.k_d = slot0.get("kD", 0)
            config.slot0.k_s = slot0.get("kS", 0)
            config.slot0.k_v = slot0.get("kV", 0)
            config.slot0.k_a = slot0.get("kA", 0)
            config.slot0.k_g = slot0.get("kG", 0)
            needs_apply = True
            _log.info(
                f"CAN {can_id}: Slot0 gains configured "
                f"kP={config.slot0.k_p} kI={config.slot0.k_i} kD={config.slot0.k_d} "
                f"kS={config.slot0.k_s} kV={config.slot0.k_v} "
                f"kA={config.slot0.k_a} kG={config.slot0.k_g}"
            )

        if current_limit:
            limits = CurrentLimitsConfigs()
            if "stator" in current_limit:
                limits.stator_current_limit = current_limit["stator"]
                limits.stator_current_limit_enable = True
            if "supply" in current_limit:
                limits.supply_current_limit = current_limit["supply"]
                limits.supply_current_limit_enable = True
            config.current_limits = limits
            needs_apply = True
            _log.info(f"CAN {can_id}: Current limits -- stator={current_limit.get('stator', 'off')}A, supply={current_limit.get('supply', 'off')}A")

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

        self._last_pos_target = position
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
