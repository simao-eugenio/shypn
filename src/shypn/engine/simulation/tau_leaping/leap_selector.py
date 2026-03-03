"""Adaptive Leap Size Selector for τ-Leaping.

Implements the leap condition from Cao et al. (2006) to ensure propensities
remain approximately constant during the leap.

The key insight: Limit relative change in each propensity to ε (typically 0.03).
This gives bounded error in the approximation.

References:
    Cao, Y., Gillespie, D. T., & Petzold, L. R. (2006). Efficient step size
    selection for the tau-leaping simulation method. J. Chem. Phys., 124(4).
"""

import math
from typing import Dict, List, Tuple, Any, Optional
import logging


class LeapSelector:
    """Adaptive τ selection based on leap condition.
    
    Selects time leap τ such that propensities change by at most ε (relative).
    
    Leap Condition (simplified):
        For each transition j with propensity aⱼ:
            τ ≤ ε × aⱼ / |daⱼ/dt|
        
        Take minimum across all transitions.
    
    Practical Implementation:
        τ = ε × min(μᵢ / σᵢ²) for each species i
        where μᵢ = current population, σᵢ² = variance of change rate
    
    Parameters:
        epsilon: Leap condition tolerance (default 0.03 = 3% change)
        critical_threshold: Treat transitions with propensity < threshold
                          as critical (require exact SSA)
        max_tau: Upper bound on leap size (prevents runaway leaps)
        min_tau: Lower bound (prevents too-small leaps)
    
    Example:
        >>> selector = LeapSelector(epsilon=0.03)
        >>> propensities = [2.5, 1.0, 0.1]
        >>> tau = selector.select_tau(propensities, place_populations)
        >>> tau  # ~0.01 (small enough to keep changes bounded)
    """
    
    def __init__(
        self,
        epsilon: float = 0.03,
        critical_threshold: float = 10.0,
        max_tau: float = 1.0,
        min_tau: float = 1e-6
    ):
        """Initialize leap selector.
        
        Args:
            epsilon: Leap condition tolerance (0 < ε ≤ 1). Smaller = more accurate.
            critical_threshold: Propensity below this is "critical" (exact SSA)
            max_tau: Maximum allowed leap size
            min_tau: Minimum allowed leap size (numerical stability)
        """
        if not 0 < epsilon <= 1:
            raise ValueError(f"Epsilon must be in (0, 1]: {epsilon}")
        if max_tau <= min_tau:
            raise ValueError(f"max_tau ({max_tau}) must be > min_tau ({min_tau})")
        
        self.epsilon = epsilon
        self.critical_threshold = critical_threshold
        self.max_tau = max_tau
        self.min_tau = min_tau
        
        self.logger = logging.getLogger(__name__)
    
    def select_tau(
        self,
        transitions: List[Any],
        model: Any,
        current_time: float,
        controller: Any = None,
        propensity_hint: Optional[Dict[str, Any]] = None,
        arc_table: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """Select appropriate time leap based on current state.
        
        Args:
            transitions: List of stochastic transitions
            model: Petri net model (for place populations)
            current_time: Current simulation time
            controller: Controller with behavior_cache (for propensity access)
        
        Returns:
            Tuple of (tau, info_dict):
                tau: Selected leap size
                info_dict: Diagnostic information
        """
        # Store controller for _get_behavior access
        self._controller = controller
        if not transitions:
            return self.max_tau, {'reason': 'no_stochastic_transitions'}
        
        # Calculate propensities for all transitions
        propensities = []
        critical_transitions = []
        
        for transition in transitions:
            # Use pre-computed propensity from the C accelerator when available
            _hint = (propensity_hint or {}).get(getattr(transition, 'id', None))
            if _hint is not None:
                propensity = _hint[0]   # net propensity
                propensities.append(propensity)
                if propensity < self.critical_threshold:
                    critical_transitions.append((transition.name, propensity))
                continue

            behavior = self._get_behavior(transition)
            if behavior is None:
                continue

            # Get propensity (rate at current state)
            try:
                propensity = behavior._evaluate_rate_at_enablement(current_time)
            except Exception as e:
                self.logger.warning(f"Could not evaluate propensity for {transition.name}: {e}")
                propensity = getattr(behavior, 'rate', 1.0)

            propensities.append(propensity)
            
            # Check if critical (low propensity)
            if propensity < self.critical_threshold:
                critical_transitions.append((transition.name, propensity))
        
        # If all transitions are critical, use exact SSA (tau = 0)
        if len(critical_transitions) == len(transitions):
            return 0.0, {
                'reason': 'all_critical',
                'critical_transitions': critical_transitions,
                'recommendation': 'use_exact_ssa'
            }
        
        # Calculate τ using simplified leap condition
        tau_unbounded = self._calculate_tau_simplified(propensities, model, transitions, arc_table)
        
        # Apply bounds
        tau = max(self.min_tau, min(tau_unbounded, self.max_tau))
        
        return tau, {
            'propensities': propensities,
            'critical_count': len(critical_transitions),
            'critical_transitions': critical_transitions,
            'unbounded_tau': tau,
            'bounded_tau': tau,
            'epsilon': self.epsilon
        }
    
    def _calculate_tau_simplified(
        self,
        propensities: List[float],
        model: Any,
        transitions: Optional[List[Any]] = None,
        arc_table: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Calculate τ using simplified leap condition.
        
        Simplified formula (conservative but fast):
            τ = ε / max(aⱼ) for all propensities aⱼ
        
        Additionally constrains tau based on available tokens to prevent
        sampling more firings than physically possible.
        
        Args:
            propensities: List of transition propensities
            model: Petri net model
            transitions: List of transitions (for token-based constraint)
        
        Returns:
            Calculated tau value
        """
        if not propensities:
            return self.max_tau
        
        # Remove zeros (transitions with zero propensity don't constrain tau)
        active_propensities = [a for a in propensities if a > 0]
        
        if not active_propensities:
            return self.max_tau
        
        # Conservative: τ = ε / max(a)
        # Interpretation: Limit fastest transition to ~ε expected firings
        max_propensity = max(active_propensities)
        tau = self.epsilon / max_propensity
        
        # Additional constraint: limit tau based on available tokens
        # For each transition, ensure propensity * tau doesn't exceed available tokens
        # This prevents Poisson sampling from requesting more firings than possible
        if transitions and model:
            for i, transition in enumerate(transitions):
                if i >= len(propensities) or propensities[i] <= 0:
                    continue
                
                # Get minimum tokens available in input places
                min_tokens = self._get_min_input_tokens(transition, model, arc_table)
                if min_tokens > 0:
                    # Limit tau so expected firings <= min_tokens
                    # The _calculate_max_firings method will cap actual firings if needed
                    # No need to be overly conservative here (was causing 50% token loss bug)
                    max_tau_for_tokens = min_tokens / propensities[i]
                    tau = min(tau, max_tau_for_tokens)
        
        return tau
    
    def _get_min_input_tokens(
        self,
        transition: Any,
        model: Any,
        arc_table: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Get minimum available tokens across all input places.

        Uses the precomputed *arc_table* (Phase 2.1) when available for
        O(k) lookup instead of O(|arcs|) scan of ``model.arcs``.

        Args:
            transition: Transition to check
            model: Petri net model
            arc_table: Optional precomputed mapping transition_id →
                       [(place_obj, weight), ...] from PropensityAccelerator.
        Returns:
            Minimum tokens available (accounting for arc weights)
        """
        min_tokens = float('inf')

        # Phase 2.1: O(k) fast path using precomputed table
        _tid = getattr(transition, "id", None)
        if arc_table is not None and _tid is not None:
            entries = arc_table.get(_tid)
            if not entries:
                return float('inf')  # source transition — no consume arcs
            for _place, _weight in entries:
                if _weight > 0 and hasattr(_place, "tokens"):
                    min_tokens = min(min_tokens, _place.tokens / _weight)
            return min_tokens if min_tokens != float('inf') else 0.0

        # Fallback: O(|arcs|) scan when no table available
        input_arcs = [arc for arc in model.arcs 
                     if arc.target == transition and hasattr(arc, 'source')]
        
        if not input_arcs:
            # Source transition - unlimited
            return float('inf')
        
        for arc in input_arcs:
            place = arc.source
            if place and hasattr(place, 'tokens'):
                # Account for arc weight
                weight = getattr(arc, 'weight', 1)
                if weight > 0:
                    available = place.tokens / weight
                    min_tokens = min(min_tokens, available)
        
        return min_tokens if min_tokens != float('inf') else 0.0
    
    def _calculate_tau_exact(
        self,
        transitions: List[Any],
        model: Any,
        current_time: float
    ) -> float:
        """Calculate τ using full leap condition (Cao et al. 2006).
        
        Full formula considers how propensities change with place populations:
            τ = ε × min_i (μᵢ / gᵢ)
        
        where:
            μᵢ = population of species i
            gᵢ = highest-order rate of change affecting species i
        
        This is more accurate but requires analyzing stoichiometry.
        
        **Currently not implemented** - placeholder for future enhancement.
        
        Args:
            transitions: List of transitions
            model: Petri net model
            current_time: Current time
        
        Returns:
            Calculated tau
        """
        # TODO: Implement full leap condition
        # For now, fall back to simplified version
        propensities = []
        for transition in transitions:
            behavior = self._get_behavior(transition)
            if behavior:
                try:
                    propensity = behavior._evaluate_rate_at_enablement(current_time)
                    propensities.append(propensity)
                except (AttributeError, ValueError, TypeError) as e:
                    # Behavior rate evaluation failed, skip this transition
                    import logging
                    logging.getLogger(__name__).debug(f"Rate evaluation failed for transition: {e}")
                    pass
        
        return self._calculate_tau_simplified(propensities, model)
    
    def _get_behavior(self, transition: Any) -> Optional[Any]:
        """Get behavior object for transition.
        
        Args:
            transition: Transition object
        
        Returns:
            Behavior object or None
        """
        # Use controller's behavior cache if available
        if hasattr(self, '_controller') and self._controller and hasattr(self._controller, 'behavior_cache'):
            return self._controller.behavior_cache.get(transition.id)
        
        # Fallback to transition.behavior attribute
        if hasattr(transition, 'behavior'):
            return transition.behavior
        return None
    
    def adjust_for_next_event(self, tau: float, next_event_time: float, current_time: float) -> float:
        """Adjust τ to not overshoot next scheduled event.
        
        If there's a timed transition or immediate event scheduled,
        limit τ so we don't step past it.
        
        Args:
            tau: Proposed leap size
            next_event_time: Time of next scheduled event
            current_time: Current simulation time
        
        Returns:
            Adjusted tau (≤ original tau)
        """
        if next_event_time is None or next_event_time <= current_time:
            return tau
        
        time_to_event = next_event_time - current_time
        return min(tau, time_to_event)
    
    def should_use_exact_ssa(
        self,
        propensities: List[float]
    ) -> bool:
        """Determine if exact SSA should be used instead of τ-leaping.
        
        Use exact SSA when:
        - All propensities are below critical threshold
        - Total propensity is very small
        
        Args:
            propensities: List of propensities
        
        Returns:
            True if should use exact SSA
        """
        if not propensities:
            return True
        
        # Check if all critical
        num_critical = sum(1 for a in propensities if a < self.critical_threshold)
        if num_critical == len(propensities):
            return True
        
        # Check if total propensity is tiny
        total_propensity = sum(propensities)
        if total_propensity < self.critical_threshold:
            return True
        
        return False
