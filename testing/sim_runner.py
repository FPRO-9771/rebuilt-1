"""
Simulation test runner.
Coordinates stepping through time for all simulated components.

TODO: Implement after physics models are ready.

Example usage:
```
sim = SimulationRunner()
sim.register(drivetrain)
sim.register(arm)

# Run a command and verify outcome
cmd = auto_modes.simple_score("blue_left")
finished = sim.run_command(cmd, timeout=15.0)

assert finished
assert drivetrain.pose.x > 2.0  # Verify robot moved forward
```
"""

from constants import SIM_DT


class SimulationRunner:
    """
    Coordinates stepping through time for all simulated components.
    """

    def __init__(self):
        self.components = []
        self.time = 0.0

    def register(self, component) -> None:
        """Register a component to be stepped."""
        if hasattr(component, 'step'):
            self.components.append(component)

    def step(self, dt: float = SIM_DT) -> None:
        """Advance all components by one time step."""
        for comp in self.components:
            comp.step(dt)
        self.time += dt

    def run_for(self, seconds: float, dt: float = SIM_DT) -> None:
        """Run simulation for specified duration."""
        steps = int(seconds / dt)
        for _ in range(steps):
            self.step(dt)

    def run_command(self, command, timeout: float = 10.0, dt: float = SIM_DT) -> bool:
        """
        Run a command until it finishes or times out.

        Returns:
            True if command finished, False if timed out
        """
        command.initialize()
        elapsed = 0.0

        while elapsed < timeout:
            command.execute()
            self.step(dt)
            elapsed += dt

            if command.isFinished():
                command.end(False)
                return True

        command.end(True)  # Interrupted
        return False

    def reset(self) -> None:
        """Reset simulation time."""
        self.time = 0.0
        for comp in self.components:
            if hasattr(comp, 'reset'):
                comp.reset()
