"""
Physics simulation engine.
Automatically models all wired motors from MOTOR_IDS so that
encoders move in sim when voltage is applied.

Run with: python -m robotpy sim
"""

from phoenix6.hardware import TalonFX, TalonFXS

from constants.ids import MOTOR_IDS
from utils.logger import get_logger

_log = get_logger("physics")

# Map "type" string from MOTOR_IDS to the Phoenix 6 device class
_SIM_DEVICE_CLASS = {
    "talon_fx": TalonFX,
    "talon_fxs": TalonFXS,
}

# Fallback if a motor config doesn't specify sim_rps_per_volt
_DEFAULT_RPS_PER_VOLT = 6.0


class PhysicsEngine:
    """
    robotpy sim calls this automatically every timestep.
    Reads motor voltage -> models movement -> writes back position/velocity.
    """

    def __init__(self, physics_controller):
        self.physics_controller = physics_controller
        self._sim_motors = []

        for name, config in MOTOR_IDS.items():
            if not config.get("wired", True):
                continue

            device_cls = _SIM_DEVICE_CLASS.get(config["type"])
            if device_cls is None:
                _log.warning(f"No sim device for type '{config['type']}' ({name})")
                continue

            device = device_cls(config["can_id"])
            device.sim_state.set_supply_voltage(12.0)

            rps_per_volt = config.get("sim_rps_per_volt", _DEFAULT_RPS_PER_VOLT)
            self._sim_motors.append({
                "name": name,
                "sim": device.sim_state,
                "rps_per_volt": rps_per_volt,
            })
            _log.info(f"Sim motor: {name} (CAN {config['can_id']}, {rps_per_volt} rps/V)")

    def update_sim(self, now, tm_diff):
        """Called every sim timestep — update motor positions from voltage."""
        for m in self._sim_motors:
            voltage = m["sim"].motor_voltage
            velocity = voltage * m["rps_per_volt"]
            m["sim"].add_rotor_position(velocity * tm_diff)
            m["sim"].set_rotor_velocity(velocity)
