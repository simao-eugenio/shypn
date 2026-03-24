"""Base strategy interface for simulation execution.

Week 4 - Phase 4: Strategy pattern base class.

Defines the contract that all simulation strategies must implement.
This enables polymorphic execution - the controller doesn't need to
know which specific algorithm is being used.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shypn.engine.simulation.controller import SimulationController


class SimulationStrategy(ABC):
    """Abstract base class for simulation execution strategies.
    
    Each concrete strategy implements a different simulation algorithm:
    - GillespieStrategy: Exact stochastic simulation (SSA)
    - AdaptiveStrategy: Adaptive tau-leaping for efficiency
    - HybridStrategy: Mixed deterministic/stochastic
    - ContinuousStrategy: Pure ODE-based continuous simulation
    
    Strategy Pattern Benefits:
    - Easy to add new algorithms without modifying controller
    - Clear separation of algorithm logic from controller state
    - Runtime strategy switching for adaptive simulation
    - Each strategy can be tested independently
    """
    
    def __init__(self, controller: 'SimulationController'):
        """Initialize strategy with reference to controller.
        
        Args:
            controller: SimulationController instance for accessing model and state
        """
        self.controller = controller
        self.model = controller.model
        self.model_adapter = controller.model_adapter
    
    @abstractmethod
    def execute_step(self, time_step: float) -> bool:
        """Execute one simulation step using this strategy's algorithm.
        
        Args:
            time_step: Time increment for this step (ignored by some strategies)
        
        Returns:
            bool: True if step executed successfully, False if simulation should stop
        
        Raises:
            NotImplementedError: If strategy doesn't implement this method
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement execute_step()")
    
    @abstractmethod
    def can_execute(self) -> bool:
        """Check if this strategy can execute on the current model.
        
        Different strategies have different requirements:
        - Gillespie: Requires stochastic transitions
        - Continuous: Requires continuous/timed transitions
        - Adaptive: Requires sufficient transitions for tau-leaping
        - Hybrid: Can handle mixed models
        
        Returns:
            bool: True if strategy is applicable to current model
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement can_execute()")
    
    def get_name(self) -> str:
        """Get human-readable strategy name.
        
        Returns:
            str: Strategy display name
        """
        return self.__class__.__name__.replace('Strategy', '')
    
    def get_description(self) -> str:
        """Get strategy description for UI display.
        
        Returns:
            str: Strategy description
        """
        return self.__doc__.split('\n')[0] if self.__doc__ else "Simulation strategy"
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"{self.__class__.__name__}(controller={id(self.controller)})"
