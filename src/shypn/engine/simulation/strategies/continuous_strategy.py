"""Continuous ODE-based simulation strategy.

Week 4 - Phase 4: Pure continuous simulation strategy.

Implements continuous simulation using ordinary differential equations
(ODEs) for Petri nets with continuous transitions.

Algorithm:
- Use RK4 (Runge-Kutta 4th order) integration
- Handle rate functions for continuous transitions
- Suitable for high copy number chemical systems

Best for models where all species have high abundances and can be
approximated as continuous variables.
"""

from .base_strategy import SimulationStrategy


class ContinuousStrategy(SimulationStrategy):
    """Pure continuous ODE simulation strategy.
    
    Best for:
    - Models with only continuous/timed transitions
    - High copy numbers (> 1000 molecules per species)
    - When stochastic effects are negligible
    - Fast simulation required
    
    Not suitable for:
    - Models with stochastic transitions
    - Low copy numbers
    - When stochastic effects are important
    """
    
    def execute_step(self, time_step: float) -> bool:
        """Execute continuous ODE integration step.
        
        Uses controller's existing continuous execution logic.
        
        Args:
            time_step: Time increment for integration
        
        Returns:
            bool: True if step executed, False if no enabled transitions
        """
        # Check if we have enabled continuous transitions
        enabled_continuous = self._get_enabled_continuous_transitions()
        
        if not enabled_continuous:
            # No continuous transitions can execute
            return False
        
        # Use controller's continuous executor
        if hasattr(self.controller, '_continuous_executor'):
            try:
                # Execute one step using continuous dynamics
                self.controller._step(time_step)
                return True
            except Exception:
                return False
        else:
            # Fallback: manual step execution
            try:
                self.controller._step(time_step)
                return True
            except Exception:
                return False
    
    def can_execute(self) -> bool:
        """Check if continuous strategy can execute on this model.
        
        Requirements:
        - At least one continuous or timed transition
        - No stochastic transitions (pure continuous)
        
        Returns:
            bool: True if model has only continuous/timed transitions
        """
        has_continuous = False
        has_stochastic = False
        
        for transition in self.model.transitions:
            if hasattr(transition, 'transition_type'):
                t_type = transition.transition_type
                if t_type in ('continuous', 'timed'):
                    has_continuous = True
                elif t_type == 'stochastic':
                    has_stochastic = True
        
        # Pure continuous: has continuous but not stochastic
        return has_continuous and not has_stochastic
    
    def _get_enabled_continuous_transitions(self):
        """Get list of enabled continuous/timed transitions.
        
        Returns:
            List: Enabled continuous transitions
        """
        enabled = []
        for transition in self.model.transitions:
            if hasattr(transition, 'transition_type'):
                t_type = transition.transition_type
                if t_type in ('continuous', 'timed'):
                    if self.controller._is_enabled(transition):
                        enabled.append(transition)
        return enabled
    
    def get_description(self) -> str:
        """Get strategy description."""
        return "Continuous ODE - Deterministic simulation (fast, no stochastic effects)"
