"""Hybrid simulation strategy for mixed deterministic/stochastic models.

Week 4 - Phase 4: Hybrid execution strategy.

Combines deterministic and stochastic simulation approaches for models
with both continuous and discrete dynamics.

Algorithm:
1. Execute continuous transitions (ODE integration)
2. Execute stochastic transitions (SSA or tau-leaping)
3. Synchronize time between both modes

Best for metabolic networks where some reactions are deterministic
(high copy numbers) and others are stochastic (low copy numbers).
"""

from .base_strategy import SimulationStrategy


class HybridStrategy(SimulationStrategy):
    """Hybrid deterministic/stochastic execution strategy.
    
    Best for:
    - Models with mixed transition types
    - Biochemical networks (metabolism + gene expression)
    - When some species have high copy numbers (continuous)
      and others have low copy numbers (stochastic)
    
    Algorithm:
    - Continuous/timed transitions: Use ODE integration
    - Stochastic transitions: Use Gillespie or tau-leaping
    - Coordination: Synchronized time stepping
    """
    
    def execute_step(self, time_step: float) -> bool:
        """Execute hybrid simulation step.
        
        Handles both continuous and discrete dynamics in a single step.
        The controller's _step() method already implements sophisticated
        hybrid logic.
        
        Args:
            time_step: Time increment for this step
        
        Returns:
            bool: True if step executed, False if simulation should stop
        """
        # Delegate to controller's existing hybrid step logic
        # The _step() method handles:
        # - Immediate transitions (priority-based)
        # - Continuous transitions (RK4 integration)
        # - Stochastic transitions (SSA or tau-leaping)
        # - Proper time synchronization
        
        try:
            self.controller._step(time_step)
            return True
        except Exception:
            return False
    
    def can_execute(self) -> bool:
        """Check if hybrid strategy can execute on this model.
        
        Hybrid strategy is the most flexible - can handle any model type.
        
        Returns:
            bool: Always True (hybrid handles all model types)
        """
        # Hybrid strategy can execute on any model
        # It gracefully handles pure continuous, pure stochastic,
        # or mixed models
        return len(self.model.transitions) > 0
    
    def get_description(self) -> str:
        """Get strategy description."""
        return "Hybrid - Mixed deterministic/stochastic simulation (most flexible)"
