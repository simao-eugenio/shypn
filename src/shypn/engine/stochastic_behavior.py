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
"""

from typing import Dict, Tuple, List, Any, Optional
import random
import math
import logging
from .transition_behavior import TransitionBehavior


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
        
        # Extract stochastic parameters
        props = getattr(transition, 'properties', {})
        
        # Check if has rate_function (SBML formulas)
        self.has_rate_function = 'rate_function' in props
        self.rate_function_expr = props.get('rate_function') if self.has_rate_function else None
        
        # Warn if stochastic transition has complex formula (likely should be continuous)
        if self.has_rate_function and self.rate_function_expr:
            # Check for patterns indicating reversible reactions (forward - reverse)
            formula_lower = str(self.rate_function_expr).lower()
            if ' - ' in self.rate_function_expr or 'k_r' in formula_lower or 'kr_' in formula_lower:
                self.logger.warning(
                    f"Stochastic transition '{transition.name}' has formula with subtraction, "
                    f"which may produce negative rates. Consider converting to continuous transition. "
                    f"Formula: {self.rate_function_expr[:80]}..."
                )
        
        # Support both properties dict AND transition.rate attribute (for UI compatibility)
        if 'rate' in props:
            # Explicit rate in properties
            self.rate = float(props.get('rate'))
        else:
            # Fallback: Use transition.rate attribute (UI stores it here)
            rate = getattr(transition, 'rate', None)
            if rate is not None:
                try:
                    self.rate = float(rate) if isinstance(rate, (int, float)) else 1.0
                except (ValueError, TypeError):
                    self.rate = 1.0  # Safe default
            else:
                self.rate = 1.0  # Default rate
        
        self.max_burst = int(props.get('max_burst', 8))
        
        # Validation
        if self.rate <= 0:
            raise ValueError(f"Rate must be positive: {self.rate}")
        if self.max_burst < 1:
            raise ValueError(f"Max burst must be >= 1: {self.max_burst}")
        
        # Scheduling state
        self._enablement_time = None
        self._scheduled_fire_time = None
        self._sampled_burst = None
    
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
            
            # Add place tokens
            places_dict = self._get_places_dict()
            for place_id, tokens in places_dict.items():
                if isinstance(place_id, str) and place_id.startswith('P'):
                    context[place_id] = tokens
                else:
                    context[f'P{place_id}'] = tokens
            
            # Evaluate formula
            result = eval(self.rate_function_expr, {"__builtins__": {}}, context)
            rate = float(result)
            
            # Ensure positive rate (required for exponential distribution)
            if rate <= 0:
                raise ValueError(
                    f"Stochastic transition '{self.transition.name}' formula evaluated to "
                    f"non-positive rate {rate:.3f}. This indicates a reversible reaction "
                    f"that should be modeled as continuous (not stochastic), or the formula is incorrect. "
                    f"Expression: {self.rate_function_expr}, Context: {context}"
                )
            
            return rate
            
        except Exception as e:
            raise RuntimeError(
                f"Failed to evaluate rate_function for stochastic transition '{self.transition.name}': {e}\n"
                f"Expression: {self.rate_function_expr}\n"
                f"Context: {context}"
            ) from e
    
    def _get_places_dict(self) -> Dict:
        """Get current place tokens as dict for formula evaluation."""
        places_dict = {}
        
        # Get all input places
        for arc in self.get_input_arcs():
            if hasattr(arc, 'source'):
                place = arc.source
                if hasattr(place, 'tokens') and hasattr(place, 'name'):
                    # Extract numeric ID from name (e.g., "P5" → 5)
                    place_id = place.name
                    places_dict[place_id] = place.tokens
        
        # Get all output places (for access to all network state)
        for arc in self.get_output_arcs():
            if hasattr(arc, 'target'):
                place = arc.target
                if hasattr(place, 'tokens') and hasattr(place, 'name'):
                    place_id = place.name
                    places_dict[place_id] = place.tokens
        
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
        lambda_rate = self._evaluate_rate_at_enablement(time)
        
        # Sample firing delay from exponential distribution
        # T ~ Exp(λ) => T = -ln(U) / λ, where U ~ Uniform(0,1)
        u = random.random()
        delay = -math.log(u) / lambda_rate if u > 0 and lambda_rate > 0 else 0.0
        
        self._scheduled_fire_time = time + delay
        
        # Sample burst size (will be used at firing time)
        self._sampled_burst = random.randint(1, self.max_burst)
    
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
            
            for arc in input_arcs:
                source_place = self._get_place(arc.source_id)
                if source_place is None:
                    return False, f"missing-source-place-{arc.source_id}"
                
                # Test arcs only check presence (weight), not burst requirements
                # They don't consume tokens, so burst doesn't apply
                if hasattr(arc, 'consumes_tokens') and not arc.consumes_tokens():
                    required = arc.weight  # Just check presence for catalysts
                else:
                    required = arc.weight * burst  # Normal/inhibitor need burst tokens
                
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
                    # Skip test arcs - they check enablement but don't consume tokens
                    if hasattr(arc, 'consumes_tokens') and not arc.consumes_tokens():
                        continue
                    
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
