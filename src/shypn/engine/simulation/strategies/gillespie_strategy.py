"""Gillespie SSA (Stochastic Simulation Algorithm) strategy.

Week 4 - Phase 4: Exact stochastic simulation strategy.

Implements the Gillespie Stochastic Simulation Algorithm (SSA) for
exact stochastic simulation of chemical reaction networks.

Algorithm:
1. Calculate propensities for all enabled transitions
2. Sample time to next reaction (exponential distribution)
3. Select which reaction fires (weighted by propensities)
4. Update marking and advance time

Reference: Gillespie, D. T. (1977). Exact stochastic simulation of
coupled chemical reactions. J. Phys. Chem., 81(25), 2340-2361.
"""

import random
import math
from typing import Any, Optional, List
from .base_strategy import SimulationStrategy


class GillespieStrategy(SimulationStrategy):
    """Gillespie SSA execution strategy for exact stochastic simulation.
    
    Best for:
    - Small to medium-sized models (< 1000 places)
    - Models with low copy numbers
    - When exact stochastic behavior is required
    
    Not suitable for:
    - Large models (slow due to recalculating propensities)
    - High copy numbers (many reactions → small time steps)
    - Continuous/hybrid models (use AdaptiveStrategy or HybridStrategy)
    """
    
    def execute_step(self, time_step: float) -> bool:
        """Execute one Gillespie SSA step.
        
        Ignores time_step parameter - Gillespie advances time based on
        exponential distribution of reaction propensities.
        
        Args:
            time_step: Ignored (Gillespie determines its own time advance)
        
        Returns:
            bool: True if step executed, False if no enabled transitions
        """
        # Get enabled stochastic transitions
        enabled = self._get_enabled_stochastic_transitions()
        
        if not enabled:
            # No reactions can fire - simulation stuck
            return False
        
        # Calculate propensities (reaction rates)
        propensities = []
        total_propensity = 0.0
        
        for transition in enabled:
            propensity = self._calculate_propensity(transition)
            propensities.append(propensity)
            total_propensity += propensity
        
        if total_propensity <= 0:
            # No reactions have positive rate
            return False
        
        # Sample time to next reaction (exponential distribution)
        tau = self._sample_reaction_time(total_propensity)
        
        # Select which reaction fires (weighted by propensities)
        fired_transition = self._select_reaction(enabled, propensities, total_propensity)
        
        # Advance time
        self.controller.time += tau
        
        # Fire the selected transition
        self.controller._fire_transition(fired_transition)
        
        return True
    
    def can_execute(self) -> bool:
        """Check if Gillespie SSA can execute on this model.
        
        Requirements:
        - At least one stochastic transition exists
        - Model must be discrete (no continuous transitions in pure SSA)
        
        Returns:
            bool: True if model has stochastic transitions
        """
        for transition in self.model.transitions:
            if hasattr(transition, 'transition_type') and transition.transition_type == 'stochastic':
                return True
        return False
    
    def _get_enabled_stochastic_transitions(self) -> List:
        """Get list of enabled stochastic transitions using dirty-place index when available.

        Returns:
            List: Enabled stochastic transitions
        """
        dirty = self.controller._dirty_since_last_check
        self.controller._dirty_since_last_check = set()
        candidates = self.controller.get_enabled_transitions(dirty)
        return [t for t in candidates
                if hasattr(t, 'transition_type') and t.transition_type == 'stochastic']
    
    def _calculate_propensity(self, transition: Any) -> float:
        """Calculate propensity (stochastic rate) for a transition.
        
        Propensity = rate × (product of reactant marking combinations)
        
        Args:
            transition: Transition to calculate propensity for
        
        Returns:
            float: Propensity value (>= 0)
        """
        # Get behavior for this transition
        behavior = self.controller._get_behavior(transition)
        
        # Calculate propensity using behavior's rate function
        if hasattr(behavior, 'calculate_propensity'):
            return behavior.calculate_propensity()
        elif hasattr(behavior, 'calculate_rate'):
            return behavior.calculate_rate()
        else:
            # Fallback: use transition's rate property
            return getattr(transition, 'rate', 1.0)
    
    def _sample_reaction_time(self, total_propensity: float) -> float:
        """Sample time to next reaction from exponential distribution.
        
        τ ~ Exp(a₀) where a₀ = Σ propensities
        
        Args:
            total_propensity: Sum of all propensities
        
        Returns:
            float: Time to next reaction
        """
        if total_propensity <= 0:
            return float('inf')
        
        # Exponential distribution: τ = -ln(r) / a₀
        r = random.random()
        while r == 0:  # Avoid log(0)
            r = random.random()
        
        return -math.log(r) / total_propensity
    
    def _select_reaction(self, transitions: List, propensities: List[float], total: float) -> None:
        """Select which reaction fires using weighted sampling.
        
        Uses linear search with cumulative propensities.
        
        Args:
            transitions: List of enabled transitions
            propensities: Propensity for each transition
            total: Sum of all propensities
        
        Returns:
            Selected transition
        """
        # Random number in [0, total_propensity)
        r = random.random() * total
        
        # Linear search through cumulative propensities
        cumulative = 0.0
        for i, propensity in enumerate(propensities):
            cumulative += propensity
            if r < cumulative:
                return transitions[i]
        
        # Fallback (shouldn't reach here due to floating point precision)
        return transitions[-1]
    
    def get_description(self) -> str:
        """Get strategy description."""
        return "Gillespie SSA - Exact stochastic simulation (best for small models)"
