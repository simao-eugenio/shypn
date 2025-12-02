"""τ-Leaping Simulation Engine.

Main engine for approximate stochastic simulation using τ-leaping method.
Coordinates leap selection, Poisson sampling, and state updates.

Phase 2: Sequential implementation (no parallelization)
Phase 3: Will add parallel execution for weakly independent transitions
"""

import logging
from typing import List, Dict, Any, Tuple, Optional

from .leap_selector import LeapSelector
from .poisson_sampler import PoissonSampler
from .parallel_scheduler import ParallelStochasticScheduler


class TauLeapingEngine:
    """Sequential τ-leaping simulation engine.
    
    Implements approximate stochastic simulation:
    1. Select time leap τ (adaptive based on propensities)
    2. Sample firings for each transition: Kⱼ ~ Poisson(aⱼ·τ)
    3. Apply all firings simultaneously
    4. Advance time by τ
    
    This provides significant speedup over exact SSA while maintaining
    controlled accuracy (error bounded by ε parameter).
    
    Example:
        >>> engine = TauLeapingEngine(epsilon=0.03)
        >>> success = engine.execute_step(controller)
        >>> # Transitions fire approximately, time advances by τ
    """
    
    def __init__(
        self,
        epsilon: float = 0.03,
        critical_threshold: float = 10.0,
        max_tau: float = 1.0,
        seed: int = None,
        use_parallel: bool = False
    ):
        """Initialize τ-leaping engine.
        
        Args:
            epsilon: Leap condition tolerance (smaller = more accurate)
            critical_threshold: Propensity below this triggers exact SSA
            max_tau: Maximum leap size
            seed: Random seed for reproducibility
            use_parallel: Enable parallel sampling for weakly independent transitions.
                         Worker count automatically determined from system capabilities.
        """
        self.leap_selector = LeapSelector(
            epsilon=epsilon,
            critical_threshold=critical_threshold,
            max_tau=max_tau
        )
        self.poisson_sampler = PoissonSampler(seed=seed)
        self.use_parallel = use_parallel
        
        # Parallel scheduler (initialized lazily)
        self._parallel_scheduler = None
        
        self.logger = logging.getLogger(__name__)
        
        # Statistics
        self.stats = {
            'total_leaps': 0,
            'total_firings': 0,
            'mean_tau': 0.0,
            'exact_ssa_fallbacks': 0
        }
    
    def execute_step(
        self,
        controller: Any
    ) -> bool:
        """Execute one τ-leaping step.
        
        Args:
            controller: Simulation controller with model and settings
        
        Returns:
            True if simulation should continue, False if complete
        """
        # Store controller reference for _get_behavior access
        self._controller = controller
        
        model = controller.model
        current_time = controller.time
        
        # Get all stochastic transitions
        stochastic_transitions = [
            t for t in model.transitions
            if t.transition_type == 'stochastic'
        ]
        
        if not stochastic_transitions:
            return False  # No stochastic transitions to execute
        
        # Step 1: Select leap size τ
        tau, leap_info = self.leap_selector.select_tau(
            stochastic_transitions,
            model,
            current_time,
            controller
        )
        
        # Log tau selection for debugging
        self.logger.debug(
            f"τ-leaping: selected tau={tau:.6f}, "
            f"propensities={leap_info.get('propensities', [])}, "
            f"epsilon={self.leap_selector.epsilon}"
        )
        
        # Check if should fall back to exact SSA
        if tau == 0.0 or leap_info.get('reason') == 'all_critical':
            self.stats['exact_ssa_fallbacks'] += 1
            return self._execute_exact_ssa_step(controller, stochastic_transitions)
        
        # Step 2: Calculate propensities and sample firings
        firings_map = self._sample_firings(
            stochastic_transitions,
            tau,
            current_time
        )
        
        # Log sampled firings for debugging
        self.logger.debug(
            f"τ-leaping: sampled firings={dict((t.name, f) for t, f in firings_map.items() if f > 0)}"
        )
        
        # Step 3: Apply firings (consume/produce tokens)
        total_firings = self._apply_firings(
            firings_map,
            controller
        )
        
        # Step 4: Advance time
        controller.time += tau
        
        # Step 5: Update statistics
        self.stats['total_leaps'] += 1
        self.stats['total_firings'] += total_firings
        self.stats['mean_tau'] = (
            (self.stats['mean_tau'] * (self.stats['total_leaps'] - 1) + tau)
            / self.stats['total_leaps']
        )
        
        # Step 6: Record leap event
        if hasattr(controller, 'data_collector') and controller.data_collector:
            controller.data_collector.record_event(
                time=controller.time,
                event_type='tau_leap',
                data={
                    'tau': tau,
                    'total_firings': total_firings,
                    'num_transitions': len([k for k in firings_map.values() if k > 0]),
                    'leap_info': leap_info
                }
            )
        
        # Check if simulation should continue
        return controller.time < controller.settings.duration
    
    def _sample_firings(
        self,
        transitions: List[Any],
        tau: float,
        current_time: float
    ) -> Dict[Any, int]:
        """Sample number of firings for each transition.
        
        Args:
            transitions: List of stochastic transitions
            tau: Time leap size
            current_time: Current simulation time
        
        Returns:
            Dictionary mapping transition -> number of firings
        """
        propensities = []
        
        for transition in transitions:
            behavior = self._get_behavior(transition)
            if behavior is None:
                propensities.append(0.0)
                continue
            
            # Calculate propensity
            try:
                propensity = behavior._evaluate_rate_at_enablement(current_time)
            except Exception as e:
                self.logger.warning(
                    f"Could not evaluate propensity for {transition.name}: {e}. Using default rate."
                )
                propensity = getattr(behavior, 'rate', 1.0)
            
            propensities.append(propensity)
        
        # Use parallel or sequential sampling
        if self.use_parallel and len(transitions) >= 4:
            # Lazy initialize parallel scheduler
            if self._parallel_scheduler is None:
                from shypn.engine.simulation.controller import SimulationController
                model = None
                # Try to get model from first transition
                if transitions and hasattr(transitions[0], 'parent_model'):
                    model = transitions[0].parent_model
                
                if model:
                    self._parallel_scheduler = ParallelStochasticScheduler(
                        model=model,
                        enable_parallel=True
                    )
                else:
                    # Fallback to sequential
                    self.logger.warning("Could not access model for parallel scheduler, using sequential")
                    self.use_parallel = False
            
            if self._parallel_scheduler:
                return self._parallel_scheduler.sample_parallel(
                    transitions, propensities, tau
                )
        
        # Sequential sampling (original implementation)
        firings_map = {}
        firings_array = self.poisson_sampler.sample_batch(propensities, tau)
        
        for transition, firings in zip(transitions, firings_array):
            firings_map[transition] = int(firings)
        
        return firings_map
    
    def _apply_firings(
        self,
        firings_map: Dict[Any, int],
        controller: Any
    ) -> int:
        """Apply sampled firings to update state.
        
        Args:
            firings_map: Dictionary of transition -> firings
            controller: Simulation controller
        
        Returns:
            Total number of firings applied
        """
        total_firings = 0
        
        for transition, num_firings in firings_map.items():
            if num_firings == 0:
                continue
            
            # Get behavior
            behavior = self._get_behavior(transition)
            if behavior is None:
                continue
            
            # Get input/output arcs
            input_arcs = behavior.get_input_arcs()
            output_arcs = behavior.get_output_arcs()
            
            # Check token availability (conservative: ensure we don't go negative)
            max_possible_firings = self._calculate_max_firings(
                transition,
                input_arcs,
                num_firings
            )
            
            actual_firings = min(num_firings, max_possible_firings)
            
            # Log if we had to cap firings due to insufficient tokens
            if actual_firings < num_firings:
                self.logger.warning(
                    f"τ-leaping: Capped {transition.name} firings from {num_firings} to {actual_firings} "
                    f"(insufficient tokens). Consider reducing tau or epsilon."
                )
            
            if actual_firings == 0:
                continue
            
            # Apply firings
            consumed_map, produced_map = self._fire_transition_multiple(
                transition,
                input_arcs,
                output_arcs,
                actual_firings,
                behavior
            )
            
            total_firings += actual_firings
            
            # Record firing event
            if hasattr(controller, 'data_collector') and controller.data_collector:
                controller.data_collector.record_firing(
                    time=controller.time,
                    transition=transition,
                    consumed=consumed_map,
                    produced=produced_map,
                    mode='tau_leaping',
                    firings=actual_firings
                )
        
        return total_firings
    
    def _calculate_max_firings(
        self,
        transition: Any,
        input_arcs: List[Any],
        requested_firings: int
    ) -> int:
        """Calculate maximum possible firings given available tokens.
        
        Args:
            transition: Transition object
            input_arcs: List of input arcs
            requested_firings: Requested number of firings
        
        Returns:
            Maximum firings possible (may be < requested)
        """
        # Source transitions have unlimited firings
        if getattr(transition, 'is_source', False):
            return requested_firings
        
        max_firings = requested_firings
        
        for arc in input_arcs:
            # Skip test arcs (don't consume tokens)
            if hasattr(arc, 'consumes_tokens') and not arc.consumes_tokens():
                continue
            
            source_place = arc.source
            if source_place is None:
                continue
            
            available_tokens = source_place.tokens
            tokens_per_firing = arc.weight
            
            if tokens_per_firing > 0:
                max_from_place = int(available_tokens // tokens_per_firing)
                max_firings = min(max_firings, max_from_place)
        
        return max(0, max_firings)
    
    def _fire_transition_multiple(
        self,
        transition: Any,
        input_arcs: List[Any],
        output_arcs: List[Any],
        num_firings: int,
        behavior: Any
    ) -> Tuple[Dict[int, float], Dict[int, float]]:
        """Fire a transition multiple times.
        
        Args:
            transition: Transition to fire
            input_arcs: Input arcs
            output_arcs: Output arcs
            num_firings: Number of times to fire
            behavior: Transition behavior
        
        Returns:
            Tuple of (consumed_map, produced_map)
        """
        consumed_map = {}
        produced_map = {}
        
        # Check if source/sink
        is_source = getattr(transition, 'is_source', False)
        is_sink = getattr(transition, 'is_sink', False)
        
        # Phase 1: Consume tokens (skip if source)
        if not is_source:
            for arc in input_arcs:
                # Skip test arcs
                if hasattr(arc, 'consumes_tokens') and not arc.consumes_tokens():
                    continue
                
                source_place = arc.source
                if source_place is None:
                    continue
                
                amount = arc.weight * num_firings
                source_place.set_tokens(source_place.tokens - amount)
                consumed_map[source_place.id] = float(amount)
        
        # Phase 2: Produce tokens (skip if sink)
        if not is_sink:
            for arc in output_arcs:
                target_place = arc.target
                if target_place is None:
                    continue
                
                amount = arc.weight * num_firings
                target_place.set_tokens(target_place.tokens + amount)
                produced_map[target_place.id] = float(amount)
        
        return consumed_map, produced_map
    
    def _execute_exact_ssa_step(
        self,
        controller: Any,
        stochastic_transitions: List[Any]
    ) -> bool:
        """Fall back to exact SSA for one step.
        
        Used when all transitions are critical (low propensity).
        
        Args:
            controller: Simulation controller
            stochastic_transitions: List of stochastic transitions
        
        Returns:
            True if simulation continues
        """
        # Find enabled transitions
        enabled = []
        for transition in stochastic_transitions:
            behavior = self._get_behavior(transition)
            if behavior:
                can_fire, _ = behavior.can_fire()
                if can_fire:
                    enabled.append(transition)
        
        if not enabled:
            # No enabled transitions - advance time slightly
            controller.time += 0.001
            return controller.time < controller.settings.duration
        
        # Select one transition (priority/random based on controller settings)
        transition = controller._select_transition(enabled)
        
        # Fire it using exact SSA
        controller._fire_transition(transition)
        
        return controller.time < controller.settings.duration
    
    def _get_behavior(self, transition: Any) -> Optional[Any]:
        """Get behavior object for transition.
        
        Args:
            transition: Transition object
        
        Returns:
            Behavior object or None
        """
        # Use controller's behavior cache (transitions don't store behavior directly)
        if hasattr(self, '_controller') and hasattr(self._controller, 'behavior_cache'):
            return self._controller.behavior_cache.get(transition.id)
        
        # Fallback: check if transition has behavior attribute (backward compatibility)
        if hasattr(transition, 'behavior'):
            return transition.behavior
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics.
        
        Returns:
            Dictionary with execution statistics
        """
        return {
            **self.stats,
            'epsilon': self.leap_selector.epsilon,
            'critical_threshold': self.leap_selector.critical_threshold
        }
    
    def reset_statistics(self):
        """Reset statistics counters."""
        self.stats = {
            'total_leaps': 0,
            'total_firings': 0,
            'mean_tau': 0.0,
            'exact_ssa_fallbacks': 0
        }
