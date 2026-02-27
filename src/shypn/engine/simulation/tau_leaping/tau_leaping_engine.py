"""τ-Leaping Simulation Engine.

Main engine for approximate stochastic simulation using τ-leaping method.
Coordinates leap selection, Poisson sampling (for irreversible reactions),
Skellam sampling (for reversible reactions), and state updates.

Supports:
- Irreversible reactions: Poisson(λ) for non-negative rates
- Reversible reactions: Skellam(λ_forward, λ_reverse) for net flux
"""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

from .leap_selector import LeapSelector
from .poisson_sampler import PoissonSampler
from .skellam_sampler import SkellamSampler
from .parallel_scheduler import ParallelStochasticScheduler


class TauLeapingEngine:
    """Sequential τ-leaping simulation engine.
    
    Implements approximate stochastic simulation:
    1. Select time leap τ (adaptive based on propensities)
    2. Sample firings for each transition:
       - Irreversible: Kⱼ ~ Poisson(aⱼ·τ)
       - Reversible: ΔKⱼ ~ Skellam(a_forward·τ, a_reverse·τ)
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
        use_parallel: bool = False,
        verbose: bool = True
    ):
        """Initialize τ-leaping engine.
        
        Args:
            epsilon: Leap condition tolerance (smaller = more accurate)
            critical_threshold: Propensity below this triggers exact SSA
            max_tau: Maximum leap size
            seed: Random seed for reproducibility
            use_parallel: Enable parallel sampling for weakly independent transitions.
                         Worker count automatically determined from system capabilities.
            verbose: If False, suppress warnings (for batch mode performance)
        """
        self.leap_selector = LeapSelector(
            epsilon=epsilon,
            critical_threshold=critical_threshold,
            max_tau=max_tau
        )
        self.poisson_sampler = PoissonSampler(seed=seed)
        self.skellam_sampler = SkellamSampler(seed=seed)  # For reversible reactions
        self.use_parallel = use_parallel
        self.verbose = verbose
        
        # Parallel scheduler (initialized lazily)
        self._parallel_scheduler = None
        
        # Control flag for time advancement (can be disabled for hybrid models)
        self._advance_time = True
        
        self.logger = logging.getLogger(__name__)
        
        # Suppress warnings if not verbose
        if not verbose:
            self.logger.setLevel(logging.ERROR)  # Only show errors, not warnings
        
        # Statistics
        self.stats = {
            'total_leaps': 0,
            'total_firings': 0,
            'mean_tau': 0.0,
            'exact_ssa_fallbacks': 0,
            'reversible_reactions': 0,  # Count of Skellam samples
            'irreversible_reactions': 0  # Count of Poisson samples
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
        
        # Get all stochastic transitions (including adaptive in stochastic mode)
        stochastic_transitions = [
            t for t in model.transitions
            if t.transition_type in ('stochastic', 'adaptive')
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
        
        # Step 4: Advance time (only if enabled - disabled for hybrid models)
        if self._advance_time:
            controller.time += tau
        
        # Step 4.5: Update assignment rule-defined species (Option 3)
        if hasattr(controller, 'enable_assignment_rule_reevaluation') and controller.enable_assignment_rule_reevaluation:
            self._update_assignment_rules(controller)
        
        # NOTE: State recording moved to controller.step() to avoid duplicate recording
        # Controller records state once per step after all phases complete
        
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
        # If duration is None, run indefinitely (return True)
        if controller.settings.duration is None:
            return True
        return controller.time < controller.settings.duration
    
    def _sample_firings(
        self,
        transitions: List[Any],
        tau: float,
        current_time: float
    ) -> Dict[Any, int]:
        """Sample number of firings for each transition.
        
        Detects reversible reactions (formulas with subtraction) and uses
        Skellam distribution. Otherwise uses Poisson distribution.
        
        Args:
            transitions: List of stochastic transitions
            tau: Time leap size
            current_time: Current simulation time
        
        Returns:
            Dictionary mapping transition -> number of firings (can be negative for reversible)
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
                
                # Check if this is a reversible reaction
                if hasattr(behavior, 'rate_function_expr') and behavior.rate_function_expr:
                    is_reversible, forward_expr, reverse_expr = (
                        SkellamSampler.detect_reversible_formula(behavior.rate_function_expr)
                    )
                    
                    if is_reversible:
                        # Mark for Skellam sampling
                        transition._skellam_reversible = True
                        transition._forward_expr = forward_expr
                        transition._reverse_expr = reverse_expr
                    else:
                        transition._skellam_reversible = False
                else:
                    transition._skellam_reversible = False
                    
            except Exception as e:
                self.logger.warning(
                    f"Could not evaluate propensity for {transition.name}: {e}. Using default rate."
                )
                propensity = getattr(behavior, 'rate', 1.0)
                transition._skellam_reversible = False
            
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
                    # Fallback to sequential (normal for small models)
                    self.logger.debug("Could not access model for parallel scheduler, using sequential")
                    self.use_parallel = False
            
            if self._parallel_scheduler:
                return self._parallel_scheduler.sample_parallel(
                    transitions, propensities, tau
                )
        
        # Sequential sampling with Skellam support for reversible reactions
        firings_map = {}
        
        # Diagnostic: Check for extreme propensities before sampling
        if np.any(np.array(propensities) > 1e10):
            max_prop = max(propensities)
            max_idx = propensities.index(max_prop)
            problem_transition = transitions[max_idx]
            
            # Get transition details - try multiple attribute names
            trans_name = getattr(problem_transition, 'label', getattr(problem_transition, 'name', f"T{max_idx}"))
            trans_id = getattr(problem_transition, 'id', f"transition_{max_idx}")
            
            # Try to get behavior and formula
            formula_str = 'N/A'
            input_info = []
            
            try:
                behavior = self._get_behavior(problem_transition)
                if behavior:
                    # Get formula from behavior
                    if hasattr(behavior, 'formula'):
                        formula_str = str(behavior.formula)
                    elif hasattr(behavior, 'rate_expression'):
                        formula_str = str(behavior.rate_expression)
                    
                    # Get input places and their markings
                    if hasattr(behavior, 'input_places'):
                        for place in behavior.input_places:
                            place_name = getattr(place, 'label', getattr(place, 'name', getattr(place, 'id', 'unknown')))
                            marking = getattr(place, 'marking', 0)
                            input_info.append(f"{place_name}={marking:.2e}")
                    
                    # Also try to evaluate the formula with current context to see what values are being used
                    if hasattr(behavior, 'context') or hasattr(behavior, '_context'):
                        context = getattr(behavior, 'context', getattr(behavior, '_context', {}))
                        if context and isinstance(context, dict):
                            # Show a sample of context values
                            context_items = list(context.items())[:5]
                            context_str = ", ".join([f"{k}={v:.2e}" if isinstance(v, (int, float)) else f"{k}={v}" 
                                                    for k, v in context_items])
                            formula_str += f" [Context sample: {context_str}]"
            except Exception as diag_err:
                # Don't let diagnostic failure block the error report
                formula_str += f" [Diagnostic error: {diag_err}]"
            
            inputs_str = ", ".join(input_info) if input_info else "Unknown inputs"
            
            self.logger.warning(
                f"Extreme propensity detected:\n"
                f"  Transition #{max_idx}: {trans_name} (id={trans_id})\n"
                f"  Propensity: {max_prop:.2e}\n"
                f"  Tau: {tau:.2e}\n"
                f"  Lambda (propensity*tau): {max_prop*tau:.2e}\n"
                f"  Input places: {inputs_str}\n"
                f"  Kinetic law: {formula_str[:200]}{'...' if len(formula_str) > 200 else ''}"
            )
        
        # Sample firings - use Skellam for reversible, Poisson for irreversible
        for transition, propensity in zip(transitions, propensities):
            if getattr(transition, '_skellam_reversible', False):
                # Reversible reaction: use Skellam distribution
                try:
                    behavior = self._get_behavior(transition)
                    
                    # Evaluate forward and reverse propensities separately
                    # For now, use the net propensity and split based on sign
                    # TODO: Improve by parsing formula to extract forward/reverse components
                    if propensity >= 0:
                        # Net forward
                        forward_prop = propensity
                        reverse_prop = 0.0
                    else:
                        # Net reverse
                        forward_prop = 0.0
                        reverse_prop = abs(propensity)
                    
                    firings = self.skellam_sampler.sample(forward_prop, reverse_prop, tau)
                    firings_map[transition] = firings
                    self.stats['reversible_reactions'] += 1
                    
                except Exception as e:
                    self.logger.warning(
                        f"Skellam sampling failed for {transition.name}: {e}. Using Poisson."
                    )
                    # Fallback to Poisson with clamped propensity
                    firings = self.poisson_sampler.sample(max(0, propensity), tau)
                    firings_map[transition] = firings
                    self.stats['irreversible_reactions'] += 1
            else:
                # Irreversible reaction: use Poisson distribution
                # Clamp negative propensities to zero (shouldn't happen for irreversible)
                if propensity < 0:
                    self.logger.warning(
                        f"Negative propensity for irreversible transition {transition.name}: {propensity}. "
                        f"Clamping to 0."
                    )
                    propensity = 0.0
                
                firings = self.poisson_sampler.sample(propensity, tau)
                firings_map[transition] = firings
                self.stats['irreversible_reactions'] += 1
        
        # Apply inhibitor arc constraints to limit firings
        firings_map = self._apply_inhibitor_constraints(firings_map, transitions)
        
        return firings_map
    
    def _apply_inhibitor_constraints(
        self,
        firings_map: Dict[Any, int],
        transitions: List[Any]
    ) -> Dict[Any, int]:
        """Apply inhibitor arc constraints to limit firings.
        
        For each transition with inhibitor arcs, check if the products
        would exceed their thresholds and reduce firings accordingly.
        
        Args:
            firings_map: Dictionary mapping transition -> sampled firings
            transitions: List of transitions
        
        Returns:
            Modified firings_map with inhibitor constraints applied
        """
        from shypn.netobjs.inhibitor_arc import InhibitorArc
        from shypn.utils.threshold_evaluator import ThresholdEvaluator
        import sys
        
        constrained_map = {}
        
        for transition in transitions:
            original_firings = firings_map.get(transition, 0)
            if original_firings <= 0:
                constrained_map[transition] = original_firings
                continue
            
            # Get behavior to access arcs
            behavior = self._get_behavior(transition)
            if behavior is None:
                constrained_map[transition] = original_firings
                continue
            
            # Get arcs
            try:
                input_arcs = behavior.get_input_arcs()
                output_arcs = behavior.get_output_arcs()
            except Exception as e:
                print(f"❌ Could not get arcs for {getattr(transition, 'name', 'unknown')}: {e}", file=sys.stderr)
                self.logger.debug(f"Could not get arcs for {transition.name}: {e}")
                constrained_map[transition] = original_firings
                continue
            
            # Find inhibitor arcs (Product → Transition) using defensive pattern
            # FIXED v2.1.2: Detect ALL inhibitor arc variants (includes curved_inhibitor_arc)
            inhibitor_arcs = [arc for arc in input_arcs if 
                            getattr(arc, 'arc_type', 'normal') == 'inhibitor' or
                            'inhibitor' in getattr(arc, 'arc_type', 'normal') or
                            getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal')) == 'inhibitor']
            
            if not inhibitor_arcs:
                # No inhibitors, use original firings
                constrained_map[transition] = original_firings
                continue
            
            # Found inhibitors - evaluate constraints
            trans_name = getattr(transition, 'name', getattr(transition, 'label', 'unknown'))
            
            # Calculate maximum allowed firings based on inhibitors
            max_allowed_firings = original_firings
            
            for inh_arc in inhibitor_arcs:
                try:
                    # The source of inhibitor arc is the product place
                    product_place = behavior._get_place(inh_arc.source_id)
                    if not product_place:
                        continue
                    
                    # Evaluate threshold dynamically
                    evaluator = ThresholdEvaluator(behavior.model)
                    context = {'time': behavior.model.time if hasattr(behavior.model, 'time') else 0.0}
                    threshold = evaluator.evaluate(inh_arc, context)
                    
                    # Current tokens in product place
                    current_tokens = product_place.tokens
                    
                    # Find how much this transition produces to that place
                    # Note: output_arcs should be arc objects, but handle strings just in case
                    tokens_per_firing = 0.0
                    
                    for out_arc_ref in output_arcs:
                        # Get actual arc object if we have an ID string
                        if isinstance(out_arc_ref, str):
                            # It's an arc ID, need to get the arc object from model
                            out_arc = behavior._get_arc(out_arc_ref)
                            if not out_arc:
                                continue
                        else:
                            out_arc = out_arc_ref
                        
                        if out_arc.target_id == product_place.id:
                            tokens_per_firing = out_arc.weight
                            break
                    
                    if tokens_per_firing > 0:
                        # Calculate remaining capacity
                        remaining = threshold - current_tokens
                        
                        if remaining <= 0:
                            # Already at or above threshold, no firings allowed
                            max_allowed_firings = 0
                            break
                        
                        # Calculate max firings before exceeding threshold
                        max_firings_for_this_inhibitor = int(remaining / tokens_per_firing)
                        
                        # Keep the most restrictive constraint
                        max_allowed_firings = min(max_allowed_firings, max_firings_for_this_inhibitor)
                
                except Exception as e:
                    import traceback
                    self.logger.error(
                        f"❌ Error evaluating inhibitor for {trans_name}: {e}\n"
                        f"Traceback: {traceback.format_exc()}"
                    )
                    print(f"❌ Error evaluating inhibitor for {trans_name}: {e}", file=sys.stderr)
                    continue
            
            # Apply the constraint
            if max_allowed_firings < original_firings:
                trans_name = getattr(transition, 'name', getattr(transition, 'label', 'unknown'))
                self.logger.info(
                    f"🔒 Inhibitor constraint: {trans_name} firings reduced "
                    f"{original_firings} → {max_allowed_firings}"
                )
            
            constrained_map[transition] = max_allowed_firings
        
        return constrained_map
    
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
            
            # Log if we had to cap firings due to insufficient tokens (debug level only)
            if actual_firings < num_firings:
                self.logger.debug(
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
            
            # Record firing event in engine's data collector (for reports)
            if hasattr(controller, 'data_collector') and controller.data_collector:
                controller.data_collector.record_firing(
                    time=controller.time,
                    transition=transition,
                    consumed=consumed_map,
                    produced=produced_map,
                    mode='tau_leaping',
                    firings=actual_firings
                )
            
            # Notify step listeners that have on_transition_fired (for analyses/plotting)
            if hasattr(controller, 'step_listeners'):
                details = {
                    'consumed': consumed_map,
                    'produced': produced_map,
                    'mode': 'tau_leaping',
                    'firings': actual_firings
                }
                for listener in controller.step_listeners:
                    # Listeners are bound methods, check the object they're bound to
                    listener_obj = getattr(listener, '__self__', listener)
                    if hasattr(listener_obj, 'on_transition_fired'):
                        # Notify once per actual firing for cumulative count tracking
                        for _ in range(actual_firings):
                            listener_obj.on_transition_fired(transition, controller.time, details)
        
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
            kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
            arc_type = getattr(arc, 'arc_type', 'normal')
            if kind != 'normal' or arc_type in ('inhibitor', 'test'):
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
                # Skip test arcs and inhibitor arcs (they don't consume)
                kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
                arc_type = getattr(arc, 'arc_type', 'normal')
                if kind != 'normal' or arc_type in ('inhibitor', 'test'):
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
        
        # NOTE: firing_count is incremented by data_collector.record_firing() 
        # in _apply_firings(), not here. Removed duplicate increment that was
        # causing 2× firing counts and 50% token loss bug.
        
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
    
    def reset_statistics(self) -> None:
        """Reset statistics counters."""
        self.stats = {
            'total_leaps': 0,
            'total_firings': 0,
            'mean_tau': 0.0,
            'exact_ssa_fallbacks': 0,
            'reversible_reactions': 0,
            'irreversible_reactions': 0
        }
    
    def _update_assignment_rules(self, controller: Any) -> None:
        """Update all assignment rule-defined species.
        
        Re-evaluates assignment rule formulas and updates place tokens.
        Called after each τ-leap to maintain algebraic constraints.
        
        Args:
            controller: Simulation controller with model and time
        """
        # Get any stochastic behavior (they all share the same assignment rules)
        stochastic_transitions = [
            t for t in controller.model.transitions
            if t.transition_type == 'stochastic'
        ]
        
        if not stochastic_transitions:
            return
        
        # Get behavior of first stochastic transition
        behavior = self._get_behavior(stochastic_transitions[0])
        if behavior is None or not hasattr(behavior, 'update_rule_defined_species'):
            return
        
        # Update all rule-defined species
        updated = behavior.update_rule_defined_species(controller.time)
        
        if updated > 0:
            self.logger.debug(
                f"Updated {updated} assignment rule-defined species at time {controller.time:.4f}"
            )
