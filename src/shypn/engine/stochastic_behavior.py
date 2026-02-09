#!/usr/bin/env python3
"""Stochastic Behavior - Fluid Stochastic Petri Net (FSPN) with burst firing.

Stochastic transitions use exponential distribution for firing delays
and support burst firing (1x to 8x arc_weight tokens consumed/produced).

Mathematical Model:
    - Firing delay: T ~ Exp(λ) where λ = rate parameter
    - Burst size: B ~ DiscreteUniform(1, 8)
    - Tokens consumed: arc_weight * B
    - Tokens produced: arc_weight * B
    - Enablement: ∀p ∈ •t: m(p) ≥ arc_weight * max_burst

Extracted from: legacy/shypnpy/core/petri.py:1562-1690

# RESOLVED: Mass conservation enforced globally in SimulationController.
#           Burst firing conserves mass PER firing (consumed == produced),
#           but cumulative firing imbalances over simulation cause violations.
#           ConservationEnforcer corrects this after each step.
#           12/12 test models validated (including stochastic transitions).
#           See conservation_enforcer.py for implementation.
"""

from typing import Dict, Tuple, List, Any, Optional
import random
import math
import logging
from .transition_behavior import TransitionBehavior
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.utils.threshold_evaluator import ThresholdEvaluator
from .spatial_utils import BoundaryValidator, VolumeAdaptiveSelector

logger = logging.getLogger(__name__)


class StochasticBehavior(TransitionBehavior):
    """Fluid Stochastic Petri Net (FSPN) transition firing behavior.
    
    Implements stochastic semantics with:
    - Exponential distribution for firing delays
    - Burst firing (1x-8x arc_weight tokens)
    - Rate-dependent behavior (higher rate = more frequent firing)
    
    Stochastic Properties:
        rate (float): Rate parameter λ for exponential distribution
        max_burst (int): Maximum burst multiplier (default 8)
        
    Firing Process:
        1. Sample delay: t ~ Exp(λ)
        2. Wait until t_enable + delay
        3. Sample burst: B ~ Uniform(1, max_burst)
        4. Consume/produce: arc_weight * B tokens
    
    Usage:
        behavior = StochasticBehavior(transition, model)
        
        # Check if can fire with burst
        can_fire, reason = behavior.can_fire()
        if can_fire:
            success, details = behavior.fire(
                behavior.get_input_arcs(),
                behavior.get_output_arcs()
            )
    """
    
    def __init__(self, transition, model):
        """Initialize stochastic behavior.
        
        Args:
            transition: Transition object with stochastic properties
            model: Model instance for context access
        """
        super().__init__(transition, model)
        
        # Logger for warnings
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize spatial property integration utilities
        self.boundary_validator = BoundaryValidator(model)
        self.volume_selector = VolumeAdaptiveSelector(threshold_fL=1.0)
        
        # Check if connected places suggest stochastic is appropriate
        input_arcs = self.get_input_arcs()
        output_arcs = self.get_output_arcs()
        
        input_places = [self._get_place(arc.source_id) for arc in input_arcs 
                       if self._get_place(arc.source_id)]
        output_places = [self._get_place(arc.target_id) for arc in output_arcs 
                        if self._get_place(arc.target_id)]
        
        if input_places or output_places:
            use_stochastic, details = self.volume_selector.analyze_transition(
                input_places, output_places
            )
            
            if not use_stochastic and details.get('reason') == 'volume-based':
                self.logger.debug(
                    f"Stochastic transition '{transition.name}' connected to large volume "
                    f"places (min={details.get('min_volume'):.2f} fL). "
                    f"Consider using continuous transition type for better performance."
                )
        
        # Rate limiting for negative rate warnings (avoid console spam)
        self._negative_rate_warnings = {}  # transition_name -> (count, last_logged_time)
        self._negative_rate_log_interval = 100  # Log every 100 occurrences
        
        # Log creation with all details
        self.logger.debug(
            f"Creating StochasticBehavior for transition '{transition.name}' (ID={transition.id}), "
            f"transition.rate={getattr(transition, 'rate', 'NOT SET')}, "
            f"transition.transition_type={getattr(transition, 'transition_type', 'NOT SET')}"
        )
        
        # Extract stochastic parameters
        props = getattr(transition, 'properties', {})
        
        # PHASE 1 REFACTORING: Prioritize properties.rate_function (unified approach)
        # Check for rate_function first (this is the canonical field)
        self.has_rate_function = 'rate_function' in props
        self.rate_function_expr = props.get('rate_function') if self.has_rate_function else None
        
        # If rate_function is a simple numeric string, parse it as lambda rate
        if self.has_rate_function and self.rate_function_expr:
            rate_func_str = str(self.rate_function_expr).strip()
            
            # Try to parse as simple number first
            try:
                self.rate = float(rate_func_str)
                self.has_rate_function = False  # It's just a number, not a formula
                self.rate_function_expr = None
                self.logger.debug(f"Transition '{transition.name}': rate_function '{rate_func_str}' is numeric lambda = {self.rate}")
            except ValueError:
                # It's a formula - keep as rate_function
                self._detect_signal_places()
                self.rate = 1.0  # Placeholder (will be evaluated at enablement)
                
                # Detect reversible reactions (formulas with subtraction)
                formula_lower = rate_func_str.lower()
                if ' - ' in rate_func_str or 'k_r' in formula_lower or 'kr_' in formula_lower:
                    self.logger.debug(
                        f"Stochastic transition '{transition.name}' has reversible formula (subtraction). "
                        f"τ-leaping will use Skellam distribution for net flux sampling. "
                        f"Formula: {rate_func_str[:80]}..."
                    )
        else:
            # LEGACY FALLBACK: Check old rate fields (deprecated, with warning)
            # First check properties.rate (numeric)
            if 'rate' in props:
                self.rate = float(props.get('rate'))
                self.logger.debug(f"Transition '{transition.name}': using properties.rate (legacy field)")
            else:
                # Last resort: transition.rate attribute (deprecated)
                rate = getattr(transition, 'rate', None)
                if rate is not None:
                    if isinstance(rate, (int, float)):
                        self.rate = float(rate)
                        self.logger.warning(
                            f"Transition '{transition.name}': using deprecated transition.rate attribute. "
                            f"Please migrate to properties.rate_function"
                        )
                    elif isinstance(rate, str):
                        # String in old rate field - treat as formula
                        rate_str = rate.strip()
                        try:
                            self.rate = float(rate_str)
                        except ValueError:
                            # Formula in old field - migrate it
                            self.has_rate_function = True
                            self.rate_function_expr = rate_str
                            self.rate = 1.0
                            self.logger.warning(
                                f"Transition '{transition.name}': found formula in deprecated rate field. "
                                f"Migrating to rate_function. Please save model to persist migration."
                            )
                    else:
                        self.rate = 1.0
                else:
                    self.rate = 1.0  # Default rate
        
        self.max_burst = int(props.get('max_burst', 8))
        
        # Validation - use warnings instead of exceptions to avoid breaking initialization
        if self.rate <= 0:
            self.logger.warning(
                f"Stochastic transition '{transition.name}' has non-positive rate ({self.rate}). "
                f"Using default rate 1.0. Please set rate property in transition dialog."
            )
            self.rate = 1.0
        if self.max_burst < 1:
            self.logger.warning(f"Max burst must be >= 1, got {self.max_burst}. Using default 8.")
            self.max_burst = 8
        
        # Scheduling state
        self._enablement_time = None
        self._scheduled_fire_time = None
        self._sampled_burst = None
        
        # Assignment rule support (Option 3: Runtime Re-evaluation)
        self.assignment_rules: Dict[int, str] = {}  # place_id -> formula
        self._compiled_rules: Dict[int, Any] = {}  # place_id -> compiled code
        self._rules_initialized = False
    
    def _detect_signal_places(self):
        r"""Detect signal places (Ψ) for this transition's rate formula.
        
        Signal places are referenced in the rate function but have no
        arc connection (input, output, or regulatory). They represent
        environmental sensing or quorum sensing behavior.
        
        Mathematical Definition:
            Ψ(t) = ReferencedPlaces(Φ(t)) \ (•t ∪ t• ∪ Σ(t))
        
        Updates:
            self.transition.signal_places: List of place IDs
            self.transition.is_environment_aware: Boolean flag
        
        Example:
            Rate: "0.5 * AHL / (1.0 + AHL)"
            If AHL has no arc to transition → AHL is a signal place
        """
        try:
            from shypn.analysis.quorum_sensing import QuorumSensingDetector
            
            detector = QuorumSensingDetector(self.model)
            signal_places = detector.detect_signal_places(
                self.transition, 
                self.rate_function_expr
            )
            
            # Annotate transition with results
            self.transition.signal_places = list(signal_places)
            self.transition.is_environment_aware = len(signal_places) > 0
            
            if signal_places:
                self.logger.debug(
                    f"Transition '{self.transition.name}' has {len(signal_places)} "
                    f"signal place(s): {signal_places} (quorum sensing / environmental sensing)"
                )
        
        except Exception as e:
            # Don't fail initialization if signal detection fails
            self.logger.warning(
                f"Could not detect signal places for '{self.transition.name}': {e}"
            )
            self.transition.signal_places = []
            self.transition.is_environment_aware = False
    
    def _is_signal_place(self, place) -> bool:
        """Check if a place is a signal place (read-only, non-consuming).
        
        Signal places (Ψ) in modular Bio-PN architecture provide information
        flow without mass transfer. They are never consumed during simulation.
        
        Args:
            place: Place object to check
        
        Returns:
            bool: True if place is a signal place
        """
        if place is None:
            return False
        
        # Check is_signal_place attribute (primary indicator)
        if hasattr(place, 'is_signal_place') and place.is_signal_place:
            return True
        
        # Check signal_type property (alternative indicator)
        if hasattr(place, 'signal_type') and place.signal_type is not None:
            return True
        
        return False
    
    def _evaluate_rate_at_enablement(self, time: float) -> float:
        """Evaluate rate (λ) at enablement time.
        
        For SBML stochastic reactions with formulas, evaluate the formula
        at the moment of enablement to get the rate parameter.
        
        Args:
            time: Current simulation time
            
        Returns:
            Evaluated rate (λ) for exponential distribution
        """
        if not self.has_rate_function:
            # No formula - use constant rate
            # Ensure we have a valid positive rate (should be validated in __init__)
            if not hasattr(self, 'rate') or self.rate <= 0:
                self.logger.warning(
                    f"Stochastic transition '{self.transition.name}' has invalid rate "
                    f"({getattr(self, 'rate', 'None')}). Using default rate 1.0"
                )
                return 1.0
            return self.rate
        
        try:
            # Build evaluation context (similar to continuous_behavior.py)
            from .function_catalog import FUNCTION_CATALOG
            import numpy as np
            
            context = {
                'time': time,
                't': time,
                'min': min,
                'max': max,
                'abs': abs,
                'math': math,
                'np': np,
                'numpy': np,
            }
            
            # Add function catalog
            context.update(FUNCTION_CATALOG)
            
            # Add SBML parameters from kinetic_metadata (if available)
            if hasattr(self.transition, 'kinetic_metadata') and self.transition.kinetic_metadata:
                if hasattr(self.transition.kinetic_metadata, 'parameters'):
                    context.update(self.transition.kinetic_metadata.parameters)
            
            # Add place tokens using their names directly
            # Add small epsilon to prevent division by zero in rate formulas
            places_dict = self._get_places_dict()
            
            # Debug: Log available places
            if not places_dict:
                self.logger.warning(
                    f"No places found for rate formula evaluation in {self.transition.name}. "
                    f"Formula: {self.rate_function_expr}"
                )
            
            for place_name, tokens in places_dict.items():
                # Add tiny epsilon (1e-10) to avoid division by zero
                # This doesn't affect simulation dynamics but prevents math errors
                context[place_name] = max(tokens, 1e-10)
            
            # Debug: Log context for first few evaluations
            if not hasattr(self, '_eval_debug_count'):
                self._eval_debug_count = 0
            if self._eval_debug_count < 3:
                self.logger.debug(
                    f"Rate eval for {self.transition.name}: formula={self.rate_function_expr}, "
                    f"context keys={list(context.keys())[:5]}, "
                    f"sample values={dict(list(context.items())[:3])}"
                )
                self._eval_debug_count += 1
            
            # Preprocess expression: convert [PlaceName] to PlaceName
            # This supports chemistry notation where [X] means "concentration of X"
            import re
            expr_processed = re.sub(r'\[([^\]]+)\]', r'\1', self.rate_function_expr)
            
            # Evaluate formula
            result = eval(expr_processed, {"__builtins__": {}}, context)
            rate = float(result)
            
            # Handle zero/negative rates gracefully for τ-leaping
            # When substrates are depleted, rate can legitimately become 0
            # This doesn't indicate an error - the transition simply can't fire
            # Return 0.0 propensity (will result in 0 firings in τ-leaping)
            if rate <= 0:
                # Only log warning if rate is significantly negative (formula error)
                if rate < -1e-6:
                    # Rate-limit warnings to avoid console spam
                    transition_name = self.transition.name
                    if transition_name not in self._negative_rate_warnings:
                        self._negative_rate_warnings[transition_name] = [0, None]
                    
                    count_info = self._negative_rate_warnings[transition_name]
                    count_info[0] += 1
                    
                    # Log first occurrence and then every N occurrences
                    if count_info[0] == 1 or count_info[0] % self._negative_rate_log_interval == 0:
                        self.logger.warning(
                            f"Stochastic transition '{transition_name}' formula evaluated to "
                            f"negative rate {rate:.6f} ({count_info[0]} times), which indicates "
                            f"a reversible reaction that should be modeled as continuous. "
                            f"Clamping to 0.0. Expression: {self.rate_function_expr}"
                        )
                        if count_info[0] >= 200:
                            self.logger.warning(
                                f"  → Negative rate warnings for '{transition_name}' will now be "
                                f"suppressed after {count_info[0]} occurrences. Consider using "
                                f"continuous or hybrid mode for this model."
                            )
                            # Stop logging after 200 warnings
                            self._negative_rate_log_interval = 1000000
                return 0.0  # Transition inactive, but not an error
            
            return rate
            
        except Exception as e:
            # If NameError, suggest similar function names
            if isinstance(e, NameError):
                try:
                    import re
                    import difflib
                    # Import at module level to avoid UnboundLocalError
                    from shypn.engine import function_catalog
                    
                    # Extract undefined name from error message
                    match = re.search(r"name '(\w+)' is not defined", str(e))
                    if match:
                        undefined_name = match.group(1)
                        # Find close matches (case-insensitive)
                        close_matches = difflib.get_close_matches(
                            undefined_name.lower(), 
                            [name.lower() for name in function_catalog.FUNCTION_CATALOG.keys()],
                            n=3,
                            cutoff=0.6
                        )
                        if close_matches:
                            # Get actual function names (preserving case)
                            actual_names = [name for name in function_catalog.FUNCTION_CATALOG.keys() 
                                          if name.lower() in close_matches]
                            print(f"   💡 Did you mean: {', '.join(actual_names)}?")
                except Exception:
                    pass  # Silently skip suggestion if import fails
            
            raise RuntimeError(
                f"Failed to evaluate rate_function for stochastic transition '{self.transition.name}': {e}\n"
                f"Expression: {self.rate_function_expr}\n"
                f"Available places: {list(places_dict.keys()) if 'places_dict' in locals() else 'N/A'}"
            ) from e
    
    def _get_places_dict(self) -> Dict:
        """Get current place tokens as dict for formula evaluation.
        
        For stochastic transitions with rate formulas, we need access to ALL places
        because the formula can reference any species, not just those directly
        connected by arcs.
        """
        places_dict = {}
        
        # If transition has rate_function, get ALL places (formula can reference any)
        # This applies to both SBML-imported and manually created models
        if self.has_rate_function and hasattr(self.model, 'places'):
            # ModelAdapter returns places as a dict, so we need .values()
            places_to_iterate = self.model.places.values() if isinstance(self.model.places, dict) else self.model.places
            
            for place in places_to_iterate:
                if hasattr(place, 'tokens'):
                    # Add by internal ID (P1, P2, P7, P8, etc.)
                    # IDs are system-generated and always have the prefix
                    if hasattr(place, 'id'):
                        places_dict[place.id] = place.tokens
                    # Also add by user-defined name (ATP_pool, Drug_ext, etc.)
                    # Names are user-controlled aliases - use as-is WITHOUT prefix
                    if hasattr(place, 'name') and place.name:
                        places_dict[place.name] = place.tokens
            
            return places_dict
        
        # For constant-rate stochastic transitions: Only get connected places
        # Get all input places
        for arc in self.get_input_arcs():
            if hasattr(arc, 'source'):
                place = arc.source
                if hasattr(place, 'tokens'):
                    # Add by internal ID (P1, P2, P7, P8, etc.)
                    if hasattr(place, 'id'):
                        places_dict[place.id] = place.tokens
                    # Also add by user-defined name - use as-is WITHOUT prefix
                    if hasattr(place, 'name') and place.name:
                        places_dict[place.name] = place.tokens
        
        # Get all output places (for access to all network state)
        for arc in self.get_output_arcs():
            if hasattr(arc, 'target'):
                place = arc.target
                if hasattr(place, 'tokens'):
                    # Add by internal ID (P1, P2, P7, P8, etc.)
                    if hasattr(place, 'id'):
                        places_dict[place.id] = place.tokens
                    # Also add by user-defined name - use as-is WITHOUT prefix
                    if hasattr(place, 'name') and place.name:
                        places_dict[place.name] = place.tokens
        
        return places_dict
    
    def set_enablement_time(self, time: float):
        """Set enablement time and sample firing delay.
        
        When a stochastic transition becomes enabled, we immediately
        sample the firing delay from Exp(rate) distribution.
        
        If transition has rate_function (SBML formula), evaluate it
        at enablement time to get the rate parameter λ.
        
        Args:
            time: Current simulation time when enablement occurred
        """
        self._enablement_time = time
        
        # Get rate (λ) - either from formula evaluation or constant
        try:
            lambda_rate = self._evaluate_rate_at_enablement(time)
        except (RuntimeError, NameError, AttributeError, KeyError) as e:
            # During import, places may not be available yet for rate evaluation
            # This is normal - rate will be evaluated when simulation actually starts
            self.logger.warning(
                f"Could not evaluate rate at enablement for {self.transition.name}: {e}. "
                f"Transition will not be scheduled."
            )
            return
        
        # If rate is zero or negative, don't schedule firing
        # This happens when substrates are depleted and propensity = 0
        if lambda_rate <= 0:
            self.logger.warning(
                f"Transition {self.transition.name} has zero/negative rate ({lambda_rate:.6f}). "
                f"Check that: (1) transition.rate is set to positive value, "
                f"(2) if using rate formula, it evaluates correctly. "
                f"Self.rate={getattr(self, 'rate', 'NOT SET')}, "
                f"has_rate_function={getattr(self, 'has_rate_function', False)}"
            )
            # Clear any previous scheduling
            self._scheduled_fire_time = None
            self._sampled_burst = None
            return
        
        # Sample firing delay from exponential distribution
        # T ~ Exp(λ) => T = -ln(U) / λ, where U ~ Uniform(0,1)
        u = random.random()
        # Protect against u=0 which would cause log(0) = -inf
        if u <= 1e-10:
            u = 1e-10
        delay = -math.log(u) / lambda_rate
        
        self._scheduled_fire_time = time + delay
        
        # Sample burst size with intelligent constraint awareness
        # If inhibitor arcs exist, limit burst to respect thresholds
        max_allowed_burst = self._calculate_max_burst_for_inhibitors()
        effective_max_burst = min(self.max_burst, max_allowed_burst)
        
        if effective_max_burst >= 1:
            self._sampled_burst = random.randint(1, effective_max_burst)
        else:
            # No burst allowed - inhibitor threshold would be exceeded
            self._sampled_burst = 0
        
        self.logger.debug(
            f"Stochastic {self.transition.name} enabled at t={time:.3f}, "
            f"rate={lambda_rate:.3f}, delay={delay:.3f}, "
            f"scheduled={self._scheduled_fire_time:.3f}, burst={self._sampled_burst}"
        )
    
    def _calculate_max_burst_for_inhibitors(self) -> int:
        """Calculate maximum burst size that respects inhibitor arc thresholds.
        
        For each inhibitor arc (Product → Transition), calculates how many
        firings can occur before the product place exceeds its threshold.
        Returns the minimum across all inhibitors (most restrictive).
        
        Returns:
            int: Maximum allowed burst size (can be very large if no constraints)
        """
        from shypn.utils.threshold_evaluator import ThresholdEvaluator
        
        max_allowed = float('inf')  # Start with no limit
        
        # Get input and output arcs
        input_arcs = self.get_input_arcs()
        output_arcs = self.get_output_arcs()
        
        # Find inhibitor arcs (Product → Transition) using defensive pattern
        inhibitor_arcs = []
        for arc in input_arcs:
            kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
            arc_type = getattr(arc, 'arc_type', 'normal')
            # FIXED v2.1.2: Detect ALL inhibitor arc variants (includes curved_inhibitor_arc)
            if kind == 'inhibitor' or arc_type == 'inhibitor' or 'inhibitor' in arc_type:
                inhibitor_arcs.append(arc)
        
        for inh_arc in inhibitor_arcs:
            # The source of inhibitor arc is the product place
            product_place = self._get_place(inh_arc.source_id)
            if not product_place:
                continue
            
            # Evaluate threshold dynamically
            evaluator = ThresholdEvaluator(self.model)
            current_time = self._get_current_time()
            context = {'time': current_time}
            
            try:
                threshold_value = evaluator.evaluate(inh_arc, context)
            except Exception as e:
                self.logger.warning(f"Failed to evaluate inhibitor threshold for {inh_arc.id}: {e}")
                continue
            
            # Find how many tokens this transition produces to the inhibited place
            tokens_per_firing = 0
            for out_arc in output_arcs:
                if out_arc.target_id == inh_arc.source_id:
                    tokens_per_firing += out_arc.weight
            
            if tokens_per_firing > 0:
                current_tokens = product_place.tokens
                
                # Calculate remaining capacity before exceeding threshold
                remaining = threshold_value - current_tokens
                
                if remaining > 0:
                    # How many firings before exceeding?
                    max_firings = int(remaining / tokens_per_firing)
                    max_allowed = min(max_allowed, max_firings)
                else:
                    # Already at or above threshold
                    max_allowed = 0
        
        # Return finite value (if inf, no inhibitor constraints exist)
        return int(max_allowed) if max_allowed != float('inf') else self.max_burst
    
    def get_scheduled_fire_time(self) -> Optional[float]:
        """Get the scheduled firing time.
        
        Returns:
            float: Scheduled time, or None if not enabled
        """
        return self._scheduled_fire_time
    
    def get_sampled_burst(self) -> Optional[int]:
        """Get the pre-sampled burst size.
        
        Returns:
            int: Burst multiplier (1-8), or None if not sampled
        """
        return self._sampled_burst
    
    def clear_enablement(self):
        """Clear enablement and scheduled firing."""
        self._enablement_time = None
        self._scheduled_fire_time = None
        self._sampled_burst = None
    
    def can_fire(self) -> Tuple[bool, str]:
        """Check if transition can fire (guard, tokens for burst, and scheduled time).
        
        Stochastic transitions require:
        1. Guard condition must pass (if defined)
        2. Sufficient tokens for maximum possible burst (unless source transition)
        3. Current time >= scheduled fire time
        
        Source transitions are always structurally enabled.
        
        Returns:
            Tuple of (can_fire: bool, reason: str)
            - (True, "enabled-stochastic") if can fire now
            - (True, "enabled-source") if source transition at scheduled time
            - (False, "guard-fails") if guard condition not met
            - (False, "insufficient-tokens-for-burst") if not enough tokens
            - (False, "not-scheduled") if no scheduled fire time
            - (False, "too-early") if before scheduled time
        """
        # Check if this is a source transition
        is_source = getattr(self.transition, 'is_source', False)
        
        # Check guard first
        guard_passes, guard_reason = self._evaluate_guard()
        if not guard_passes:
            return False, guard_reason
        
        if self._scheduled_fire_time is None:
            return False, "not-scheduled"
        
        current_time = self._get_current_time()
        if current_time < self._scheduled_fire_time:
            remaining = self._scheduled_fire_time - current_time
            return False, f"too-early (remaining={remaining:.3f})"
        
        # Check sufficient tokens for burst firing (skip if source transition)
        if not is_source:
            input_arcs = self.get_input_arcs()
            burst = self._sampled_burst if self._sampled_burst else self.max_burst
            
            # VERBOSE DEBUG: Print ALL input arcs for T7, T8, T15
            if self._transition.id in ['T7', 'T8', 'T15']:
                print(f"\n{'='*60}")
                print(f"VERBOSE: Checking enablement for {self._transition.id} ({self._transition.name})")
                print(f"Input arcs: {len(input_arcs)}")
                for i, arc in enumerate(input_arcs):
                    arc_type_name = type(arc).__name__
                    arc_type_attr = getattr(arc, 'arc_type', 'unknown')
                    print(f"  Arc {i+1}: {arc.id}, type={arc_type_name}, arc_type={arc_type_attr}, "
                          f"isinstance(InhibitorArc)={isinstance(arc, InhibitorArc)}")
                print(f"{'='*60}\n")
            
            for arc in input_arcs:
                source_place = self._get_place(arc.source_id)
                if source_place is None:
                    return False, f"missing-source-place-{arc.source_id}"
                
                # Check arc type using defensive pattern
                kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
                arc_type = getattr(arc, 'arc_type', 'normal')
                
                # INHIBITOR ARC: Transition is DISABLED when place has too many tokens
                # This implements negative feedback / product inhibition
                # FIXED v2.1.2: Detect ALL inhibitor arc variants (includes curved_inhibitor_arc)
                if kind == 'inhibitor' or arc_type == 'inhibitor' or 'inhibitor' in arc_type:
                    # Inhibitor arcs use INVERTED logic: disable when tokens >= threshold
                    # Evaluate threshold dynamically (supports formulas like "2.0 * (1 + ATP_pool/5000)**0.5")
                    evaluator = ThresholdEvaluator(self.model)
                    context = {'time': self.model.time if hasattr(self.model, 'time') else 0.0}
                    threshold_value = evaluator.evaluate(arc, context)
                    
                    # VERBOSE DEBUG for specific transitions
                    if self._transition.id in ['T7', 'T8', 'T15']:
                        print(f"  INHIBITOR CHECK: {arc.id} ({arc.source_id} → {self._transition.id})")
                        print(f"    Source tokens: {source_place.tokens:.2f}")
                        print(f"    Threshold: {threshold_value:.2f}")
                        print(f"    Will inhibit: {source_place.tokens >= threshold_value}")
                    
                    if source_place.tokens >= threshold_value:
                        logging.info(f"Transition {self._transition.id} INHIBITED by {arc.source_id}: "
                                   f"{source_place.tokens:.2f} >= {threshold_value:.2f}")
                        return False, f"inhibited-by-{arc.source_id} (tokens={source_place.tokens:.1f} >= threshold={threshold_value:.2f})"
                    # If tokens < threshold, inhibitor doesn't block (continue checking other arcs)
                    continue
                
                # TEST ARC: Check presence only (weight), not burst requirements
                # They don't consume tokens, so burst doesn't apply
                kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
                arc_type = getattr(arc, 'arc_type', 'normal')
                
                logger.debug(f"  [BURST CALC] Arc {arc.id}: type={type(arc).__name__}, kind={kind}, arc_type={arc_type}, burst={burst}")
                
                if kind != 'normal' or arc_type in ('inhibitor', 'test'):
                    required = arc.weight  # Just check presence for catalysts
                    logger.debug(f"    → Test/Inhibitor: checking weight={required} only")
                else:
                    required = arc.weight * burst  # Normal arcs (including SignalFlowArcs) need burst tokens
                    logger.debug(f"    → Normal: checking burst requirement={required}")
                
                if source_place.tokens < required:
                    return False, f"insufficient-tokens-for-burst-P{arc.source_id}"
        
        if is_source:
            return True, f"enabled-source (burst={self._sampled_burst if self._sampled_burst else self.max_burst})"
        return True, f"enabled-stochastic (burst={self._sampled_burst if self._sampled_burst else self.max_burst})"
    
    def fire(self, input_arcs: List, output_arcs: List) -> Tuple[bool, Dict[str, Any]]:
        """Execute stochastic burst firing.
        
        Firing process:
        1. Validate scheduled time and token availability
        2. Use pre-sampled burst size
        3. Consume arc_weight * burst from each input place
        4. Produce arc_weight * burst to each output place
        5. Clear enablement (will reschedule if re-enabled)
        6. Record firing event with stochastic info
        
        Args:
            input_arcs: List of incoming Arc objects
            output_arcs: List of outgoing Arc objects
        
        Returns:
            Tuple of (success: bool, details: dict)
            
            Success case:
                (True, {
                    'consumed': {place_id: amount, ...},
                    'produced': {place_id: amount, ...},
                    'stochastic_mode': True,
                    'burst_size': int,
                    'rate': float,
                    'delay': float
                })
            
            Failure case:
                (False, {
                    'reason': 'error-description',
                    'stochastic_mode': True
                })
        """
        try:
            # Validate can fire
            can_fire, reason = self.can_fire()
            if not can_fire:
                return False, {
                    'reason': f'stochastic-violation: {reason}',
                    'stochastic_mode': True,
                    'rate': self.rate
                }
            
            # Check if this is a source or sink transition
            is_source = getattr(self.transition, 'is_source', False)
            is_sink = getattr(self.transition, 'is_sink', False)
            
            consumed_map = {}
            produced_map = {}
            current_time = self._get_current_time()
            burst = self._sampled_burst if self._sampled_burst else 1
            delay = current_time - self._enablement_time if self._enablement_time else 0.0
            
            # Phase 1: Consume tokens with burst multiplier (skip if source transition)
            if not is_source:
                for arc in input_arcs:
                    # Skip inhibitor arcs and test arcs (they don't consume)
                    # Use defensive pattern: check kind, properties['kind'], and arc_type
                    kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
                    arc_type = getattr(arc, 'arc_type', 'normal')
                    
                    logger.debug(f"  Arc {arc.id}: type={type(arc).__name__}, kind={kind}, arc_type={arc_type}")
                    
                    # DEFENSIVE v2.1.1: Only TEST arcs skip consumption (pure catalysts)
                    # Inhibitor arcs DO consume tokens when threshold permits transition to fire
                    if arc_type == 'test':
                        logger.debug(f"    → SKIP consumption (test arc - catalyst)")
                        continue
                    
                    logger.debug(f"    → CONSUMING {firing_count * arc.weight} tokens")
                    
                    source_place = self._get_place(arc.source_id)
                    if source_place is None:
                        return False, {
                            'reason': 'missing-source-place',
                            'place_id': arc.source_id,
                            'stochastic_mode': True
                        }
                    
                    amount = arc.weight * burst
                    if source_place.tokens < amount:
                        return False, {
                            'reason': 'insufficient-tokens-for-burst',
                            'place_id': arc.source_id,
                            'required': amount,
                            'available': source_place.tokens,
                            'burst': burst,
                            'stochastic_mode': True
                        }
                    
                    # Burst consumption (INSIDE the loop, not outside!)
                    source_place.set_tokens(source_place.tokens - amount)
                    consumed_map[arc.source_id] = float(amount)
            
            # Phase 2: Produce tokens with burst multiplier (skip if sink transition)
            if not is_sink:
                for arc in output_arcs:
                    target_place = self._get_place(arc.target_id)
                    if target_place is None:
                        continue
                    
                    amount = arc.weight * burst
                    
                    # Burst production
                    target_place.set_tokens(target_place.tokens + amount)
                    produced_map[arc.target_id] = float(amount)
            
            # Phase 3: Clear scheduling state
            self.clear_enablement()
            
            # Auto-reschedule source transitions for continuous firing
            is_source = getattr(self.transition, 'is_source', False)
            if is_source:
                # Source transitions represent continuous processes (Poisson process)
                # Immediately reschedule with new exponential delay
                self.set_enablement_time(current_time)
            
            # Phase 4: Record stochastic firing event
            self._record_event(
                consumed=consumed_map,
                produced=produced_map,
                mode='stochastic',
                transition_type='stochastic',
                burst_size=burst,
                rate=self.rate,
                delay=delay
            )
            
            return True, {
                'consumed': consumed_map,
                'produced': produced_map,
                'stochastic_mode': True,
                'burst_size': burst,
                'rate': self.rate,
                'delay': delay,
                'transition_type': 'stochastic',
                'time': current_time
            }
            
        except Exception as e:
            return False, {
                'reason': f'stochastic-error: {str(e)}',
                'stochastic_mode': True,
                'error_type': type(e).__name__
            }
    
    def get_type_name(self) -> str:
        """Return human-readable type name.
        
        Returns:
            str: "Stochastic (FSPN)"
        """
        return "Stochastic (FSPN)"
    
    # ============================================================================
    # Additional Helper Methods
    # ============================================================================
    
    def get_stochastic_info(self) -> Dict[str, Any]:
        """Get detailed stochastic information.
        
        Returns:
            Dictionary with rate, burst, and scheduling info
        """
        current_time = self._get_current_time()
        
        info = {
            'rate': self.rate,
            'max_burst': self.max_burst,
            'mean_delay': 1.0 / self.rate,
            'enablement_time': self._enablement_time,
            'scheduled_fire_time': self._scheduled_fire_time,
            'sampled_burst': self._sampled_burst,
            'current_time': current_time
        }
        
        if self._scheduled_fire_time is not None:
            info['time_until_fire'] = max(0, self._scheduled_fire_time - current_time)
            info['can_fire_now'] = current_time >= self._scheduled_fire_time
        
        return info
    
    def resample_burst(self):
        """Resample burst size (useful for re-enablement).
        
        This allows changing the burst without resampling the firing time.
        """
        self._sampled_burst = random.randint(1, self.max_burst)
    
    def get_required_tokens_for_burst(self) -> Dict[int, int]:
        """Calculate required tokens for current burst in each input place.
        
        Returns:
            Dictionary mapping place_id -> required_tokens
        """
        burst = self._sampled_burst if self._sampled_burst else self.max_burst
        required = {}
        
        for arc in self.get_input_arcs():
            kind = getattr(arc, 'kind', 'normal')
            if kind == 'normal':
                required[arc.source_id] = arc.weight * burst
        
        return required
    
    # ============================================================================
    # Assignment Rule Re-evaluation (Option 3: Temporal Evaluation)
    # ============================================================================
    
    def initialize_assignment_rules(self, pathway_data: Any = None) -> None:
        """Initialize assignment rules from pathway data.
        
        Extract assignment rules from species and prepare for runtime evaluation.
        Called once during simulation initialization.
        
        Args:
            pathway_data: PathwayData object with species containing assignment_rule field
        """
        if self._rules_initialized:
            return
            
        if pathway_data is None:
            self._rules_initialized = True
            return
        
        # Extract assignment rules from species
        for species in pathway_data.species:
            if hasattr(species, 'assignment_rule') and species.assignment_rule:
                # Find corresponding place in model
                place = None
                for p in self.model.places:
                    if p.name == species.id or p.name == species.name:
                        place = p
                        break
                
                if place:
                    self.assignment_rules[place.id] = species.assignment_rule
                    self.logger.debug(
                        f"Registered assignment rule for place '{place.name}' (ID={place.id}): "
                        f"{species.assignment_rule[:60]}..."
                    )
        
        # Precompile formulas for performance
        self._compile_assignment_rules()
        self._rules_initialized = True
        
        if self.assignment_rules:
            self.logger.debug(
                f"Initialized {len(self.assignment_rules)} assignment rule(s) for "
                f"runtime re-evaluation in stochastic mode"
            )
    
    def _compile_assignment_rules(self) -> None:
        """Precompile assignment rule formulas for performance.
        
        Uses compile() to avoid repeated parsing overhead during simulation.
        Caches compiled code objects in _compiled_rules.
        """
        for place_id, formula in self.assignment_rules.items():
            try:
                # Compile formula to bytecode
                compiled_code = compile(formula, f'<assignment_rule_{place_id}>', 'eval')
                self._compiled_rules[place_id] = compiled_code
                self.logger.debug(f"Compiled assignment rule for place ID={place_id}")
            except SyntaxError as e:
                self.logger.error(
                    f"Failed to compile assignment rule for place ID={place_id}: {e}. "
                    f"Formula: {formula}"
                )
    
    def _build_evaluation_context(self, time: float) -> Dict[str, Any]:
        """Build evaluation context for assignment rule formulas.
        
        Creates dictionary with:
        - All place tokens (by name)
        - Common math functions
        - Time variable
        - Function catalog
        
        Args:
            time: Current simulation time
            
        Returns:
            Dictionary for eval() context
        """
        from .function_catalog import FUNCTION_CATALOG
        import numpy as np
        
        context = {
            'time': time,
            't': time,
            'min': min,
            'max': max,
            'abs': abs,
            'math': math,
            'np': np,
            'numpy': np,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'sqrt': math.sqrt,
            'pow': pow,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan
        }
        
        # Add function catalog
        for func_name, func_impl in FUNCTION_CATALOG.items():
            context[func_name] = func_impl
        
        # Add all place tokens (by name)
        for place in self.model.places:
            context[place.name] = place.tokens
        
        return context
    
    def _safe_eval(self, formula: str, context: Dict[str, Any], place_id: int) -> float:
        """Safely evaluate formula with error handling.
        
        Args:
            formula: Formula string to evaluate
            context: Evaluation context dictionary
            place_id: Place ID for logging
            
        Returns:
            Evaluated value (float)
        """
        try:
            # Use precompiled code if available
            if place_id in self._compiled_rules:
                result = eval(self._compiled_rules[place_id], {"__builtins__": {}}, context)
            else:
                result = eval(formula, {"__builtins__": {}}, context)
            
            return float(result)
        except Exception as e:
            place = self.model.get_object_by_id(place_id)
            place_name = place.name if place else f"ID={place_id}"
            self.logger.error(
                f"Failed to evaluate assignment rule for place '{place_name}': {e}. "
                f"Formula: {formula[:60]}... Keeping current value."
            )
            # Return current value as fallback
            return place.tokens if place else 0.0
    
    def update_rule_defined_species(self, time: float) -> int:
        """Update all species with assignment rules.
        
        Re-evaluates assignment rule formulas and updates place tokens.
        Called after each τ-leap or SSA step.
        
        Args:
            time: Current simulation time
            
        Returns:
            Number of species updated
        """
        if not self.assignment_rules:
            return 0
        
        # Build evaluation context once
        context = self._build_evaluation_context(time)
        
        # Update each rule-defined species
        updated = 0
        for place_id, formula in self.assignment_rules.items():
            place = self.model.get_object_by_id(place_id)
            if not place:
                continue
            
            # Evaluate formula
            new_value = self._safe_eval(formula, context, place_id)
            
            # Update tokens (ensure non-negative)
            place.tokens = max(0.0, new_value)
            updated += 1
        
        return updated
