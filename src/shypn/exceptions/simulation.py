"""Simulation execution exceptions."""

from shypn.exceptions.base import ShypnError


class SimulationError(ShypnError):
    """Base class for errors during simulation execution.

    Raised when simulation cannot complete successfully.
    """
    pass


class SimulationSetupError(SimulationError):
    """Errors during simulation setup/initialization.

    Raised when:
    - Simulation parameters are invalid
    - Initial state is invalid
    - Required resources are unavailable
    """
    pass


class SimulationRuntimeError(SimulationError):
    """Errors during simulation execution.

    Raised when:
    - Numerical instability occurs
    - Deadlock detected
    - Invalid state transition
    - Integration fails
    """
    pass


class SimulationTimeoutError(SimulationError):
    """Simulation exceeded time limit.

    Raised when simulation takes longer than configured timeout.
    """
    pass
