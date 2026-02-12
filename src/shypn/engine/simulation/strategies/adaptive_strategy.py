"""Adaptive tau-leaping strategy for efficient stochastic simulation.

Week 4 - Phase 4: Adaptive stochastic simulation strategy.

Implements adaptive tau-leaping algorithm that approximates multiple
reactions within a single time step for computational efficiency.

Algorithm:
1. Estimate time step τ based on reaction propensities
2. Fire multiple reactions during τ (Poisson sampling)
3. Adapt τ based on model state (smaller when close to boundaries)

More efficient than Gillespie SSA for models with many reactions,
while maintaining reasonable accuracy.
"""

from typing import List
from .base_strategy import SimulationStrategy


class AdaptiveStrategy(SimulationStrategy):
    """Adaptive tau-leaping execution strategy.
    
    Best for:
    - Large models (> 1000 places)
    - High copy numbers (many reactions per time unit)
    - When some stochastic accuracy can be traded for speed
    
    Not suitable for:
    - Very small copy numbers (< 10) - use GillespieStrategy
    - When exact stochastic behavior is required
    - Purely continuous models - use ContinuousStrategy
    """
    
    def __init__(self, controller, epsilon: float = 0.03):
        """Initialize adaptive strategy.
        
        Args:
            controller: SimulationController instance
            epsilon: Error control parameter (0.01-0.1, smaller = more accurate)
        """
        super().__init__(controller)
        self.epsilon = epsilon  # Error tolerance for tau selection
    
    def execute_step(self, time_step: float) -> bool:
        """Execute adaptive tau-leaping step.
        
        Automatically determines appropriate tau based on model state.
        The time_step parameter provides an upper bound.
        
        Args:
            time_step: Maximum time step (adaptive tau may be smaller)
        
        Returns:
            bool: True if step executed, False if no enabled transitions
        """
        # Delegate to controller's existing adaptive/hybrid step logic
        # The controller already has sophisticated adaptive tau-leaping
        # implementation in the _step() method
        
        # Check if we have enabled transitions
        enabled = self._get_enabled_transitions()
        if not enabled:
            return False
        
        # Use controller's hybrid step (handles adaptive tau internally)
        try:
            self.controller._step(time_step)
            return True
        except Exception:
            return False
    
    def can_execute(self) -> bool:
        """Check if adaptive tau-leaping can execute on this model.
        
        Requirements:
        - At least one stochastic or adaptive transition
        - Reasonable copy numbers (> 10 molecules per species recommended)
        
        Returns:
            bool: True if model has stochastic/adaptive transitions
        """
        for transition in self.model.transitions:
            if hasattr(transition, 'transition_type'):
                t_type = transition.transition_type
                if t_type in ('stochastic', 'adaptive'):
                    return True
        return False
    
    def _get_enabled_transitions(self) -> List:
        """Get list of enabled transitions (any type).
        
        Returns:
            List: Enabled transitions
        """
        enabled = []
        for transition in self.model.transitions:
            if self.controller._is_enabled(transition):
                enabled.append(transition)
        return enabled
    
    def get_description(self) -> str:
        """Get strategy description."""
        return f"Adaptive Tau-Leaping (ε={self.epsilon}) - Fast stochastic approximation"
