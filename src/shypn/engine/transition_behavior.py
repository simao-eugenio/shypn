#!/usr/bin/env python3
"""Transition Behavior - Abstract Base Class for Transition Firing Behaviors.

This module defines the abstract interface that all transition types must implement.
Each transition type (immediate, timed, stochastic, continuous) provides its own
firing semantics by subclassing TransitionBehavior.

Architecture:
    TransitionBehavior (ABC)
        ├── ImmediateBehavior
        ├── TimedBehavior
        ├── StochasticBehavior
        └── ContinuousBehavior
"""

from abc import ABC, abstractmethod
from typing import Dict, Tuple, List, Any, Optional
import logging
from shypn.utils.safe_eval import safe_eval_bool

logger = logging.getLogger(__name__)


class TransitionBehavior(ABC):
    """Abstract base class for transition firing behaviors.
    
    Each transition type (immediate, timed, stochastic, continuous) implements
    its own firing semantics by subclassing this base class. This follows the
    Strategy pattern, allowing different firing algorithms to be used interchangeably.
    
    The base class provides:
    - Common interface that all behaviors must implement
    - Utility methods for accessing model state
    - Helper methods for arc queries
    
    Subclasses must implement:
    - can_fire(): Type-specific enablement checking
    - fire(): Type-specific firing logic
    - get_type_name(): Human-readable type name
    
    Usage:
        # Typically created through factory
        behavior = create_behavior(transition, model)
        
        # Check if can fire
        can_fire, reason = behavior.can_fire()
        
        # Fire if enabled
        if can_fire:
            success, details = behavior.fire(
                input_arcs=behavior.get_input_arcs(),
                output_arcs=behavior.get_output_arcs()
            )
    """
    
    def __init__(self, transition, model):
        """Initialize behavior with transition and model context.
        
        Args:
            transition: Transition object (from shypn.netobjs.Transition)
            model: PetriNetModel instance (provides access to places, arcs, time)
        """
        self.transition = transition
        self.model = model
        
        # Token accounting tracking
        self._last_consumed = {}
        self._last_produced = {}
        self._accounting_enabled = False
    
    # ============================================================================
    # Abstract Methods (Must be implemented by subclasses)
    # ============================================================================
    
    @abstractmethod
    def can_fire(self) -> Tuple[bool, str]:
        """Check if transition can fire according to type-specific rules.
        
        This method checks both structural enablement (enough tokens) and
        type-specific constraints (timing windows, rate functions, etc.).
        
        Returns:
            Tuple of (can_fire: bool, reason: str)
            - can_fire: True if transition can fire, False otherwise
            - reason: Human-readable explanation
              Examples: "enabled", "insufficient-tokens", "not-in-timing-window"
        """
        pass
    
    @abstractmethod
    def fire(self, input_arcs: List, output_arcs: List) -> Tuple[bool, Dict[str, Any]]:
        """Execute firing logic for this transition type.
        
        This method implements the type-specific firing semantics:
        - Immediate: discrete token transfer (arc_weight units)
        - Timed: discrete with timing constraints
        - Stochastic: burst firing (N × arc_weight)
        - Continuous: continuous flow with integration
        
        Args:
            input_arcs: List of incoming Arc objects
            output_arcs: List of outgoing Arc objects
        
        Returns:
            Tuple of (success: bool, details: dict)
            - success: True if firing succeeded, False if failed
            - details: Dictionary with firing information:
                {
                    'consumed': {place_id: amount, ...},
                    'produced': {place_id: amount, ...},
                    ... type-specific fields ...
                }
        """
        pass
    
    @abstractmethod
    def get_type_name(self) -> str:
        """Return human-readable type name.
        
        Returns:
            String type name like "Immediate", "Timed (TPN)", etc.
        """
        pass
    
    # ============================================================================
    # Common Utility Methods (Available to all subclasses)
    # ============================================================================
    
    def is_enabled(self) -> bool:
        """Check basic structural enablement (sufficient tokens in input places).
        
        This checks the standard Petri net enablement condition:
        For all input places p: marking(p) >= arc_weight
        
        Handles all arc types:
        - Normal arcs: tokens >= weight (standard enablement)
        - Test arcs: tokens >= weight (catalyst presence, non-consuming)
        - Inhibitor arcs: tokens < weight (negative feedback)
        
        Does not check type-specific constraints (timing, rates, etc.).
        
        Returns:
            bool: True if structurally enabled, False otherwise
        """
        return self._check_enablement_manual()
    
    def _check_enablement_manual(self) -> bool:
        """Manual enablement check with proper handling of ALL arc types.
        
        SHYPN Arc Semantics:
        - Normal arcs: tokens >= threshold (standard enablement, CONSUMES)
        - Test arcs: tokens >= threshold (catalyst presence, NON-CONSUMING)
        - Inhibitor arcs: tokens < threshold (INVERTED - negative feedback)
        
        **Dynamic Threshold Support** (NEW):
        When arc.threshold is set, it SUPERSEDES arc.weight for enablement checking.
        The arc.weight property is still used for token consumption.
        
        Threshold types:
        - None: Use arc.weight (backward compatible)
        - Numeric: Fixed threshold value
        - Expression: Dynamic formula (e.g., "4.0 * (1.0 + AMP / 0.1)")
        - Function: Lambda with dependencies
        
        Biological Semantics:
        - Normal arc: "I need threshold tokens to function" (substrate requirement)
        - Test arc: "Catalyst/enzyme must be present" (non-consuming check)
        - Inhibitor arc: "Inhibit reaction when product >= threshold" (negative feedback)
        
        Example with weight=10:
        - Normal arc: enabled at 10+ tokens, CONSUMES 10 tokens on fire
        - Test arc: enabled at 10+ tokens, DOES NOT consume on fire
        - Inhibitor arc: DISABLED at 10+ tokens (product inhibition)
        
        Example with dynamic threshold:
        - arc.weight = 1 (consumption)
        - arc.threshold = "4.0 * (1.0 + AMP / 0.1)" (enablement)
        - At AMP=0.05: threshold=6.0, enabled if tokens >= 6.0
        
        This models biological reactions correctly:
        - Substrates are consumed (normal arcs)
        - Enzymes enable but aren't consumed (test arcs)
        - Products can inhibit their own production (inhibitor arcs)
        - Inhibition thresholds adapt to cellular state (dynamic thresholds)
        
        Returns:
            bool: True if enabled, False otherwise
        """
        from shypn.utils.threshold_evaluator import ThresholdEvaluator
        
        input_arcs = self.get_input_arcs()
        
        # Create threshold evaluator for dynamic threshold support
        evaluator = ThresholdEvaluator(self.model)
        context = {'time': self._get_current_time()}
        
        for arc in input_arcs:
            # Get source place directly from arc reference
            source_place = arc.source
            if source_place is None:
                raise ValueError(f"Arc {arc.id if hasattr(arc, 'id') else 'unknown'} has no source place")
            
            # Evaluate effective threshold (supersedes weight if threshold is set)
            effective_threshold = evaluator.evaluate(arc, context)
            
            # Check arc type using defensive pattern
            kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
            arc_type = getattr(arc, 'arc_type', 'normal')
            
            # Check based on arc type
            # FIXED v2.1.2: Detect ALL inhibitor arc variants (includes curved_inhibitor_arc)
            if kind == 'inhibitor' or arc_type == 'inhibitor' or 'inhibitor' in arc_type:
                # Inhibitor: INVERTED check (tokens < threshold)
                # Transition DISABLED when place has too many tokens (negative feedback)
                # Transition ENABLED when place has few tokens (allows production)
                if source_place.tokens >= effective_threshold:
                    return False  # INHIBITED by excess product
            elif arc_type == 'test':
                # Test arc: Same enablement as normal (tokens >= threshold)
                # BUT does NOT consume tokens on fire (catalyst behavior)
                # This is checked separately in fire() methods via kind/arc_type checks
                if source_place.tokens < effective_threshold:
                    return False  # Catalyst not present in sufficient quantity
            else:
                # Normal: Standard check (tokens >= threshold)
                # Transition enabled when enough substrate available
                if source_place.tokens < effective_threshold:
                    return False
        
        return True
    
    def get_input_arcs(self) -> List:
        """Get all input arcs to this transition.
        
        Returns:
            List of Arc objects that target this transition
            
        Raises:
            AttributeError: If model doesn't have arcs attribute
        """
        if not hasattr(self.model, 'arcs'):
            raise AttributeError(
                f"Model {self.model} does not have 'arcs' attribute. "
                f"Cannot determine input arcs for transition {self.transition.id}"
            )
        
        # Handle both dict and list representations
        arcs_collection = self.model.arcs
        if isinstance(arcs_collection, dict):
            arcs = arcs_collection.values()
        elif isinstance(arcs_collection, list):
            arcs = arcs_collection
        else:
            raise TypeError(
                f"Model.arcs must be dict or list, got {type(arcs_collection)}"
            )
        
        # Use ID comparison (primary) with object reference fallback
        # Netobjects should be dereferenced via properties like source_id, target_id
        transition_id = self.transition.id if hasattr(self.transition, 'id') else str(self.transition)
        result = []
        
        # Use ID comparison (primary) with object reference fallback
        # Netobjects should be dereferenced via properties like source_id, target_id
        transition_id = self.transition.id if hasattr(self.transition, 'id') else str(self.transition)
        result = []
        
        for arc in arcs:
            # Primary: ID comparison via arc.target_id property
            try:
                if hasattr(arc, 'target_id') and arc.target_id == transition_id:
                    result.append(arc)
                    continue
            except (AttributeError, TypeError):
                # Arc structure doesn't support ID access
                pass
            
            # Fallback: Object reference comparison
            try:
                if arc.target == self.transition:
                    result.append(arc)
                    continue
            except (AttributeError, TypeError):
                # Arc doesn't have target reference
                pass
                
            # Last resort: String ID in target
            try:
                if isinstance(arc.target, str) and arc.target == transition_id:
                    result.append(arc)
            except (AttributeError, TypeError):
                # Arc target is not comparable
                pass
        
        return result
    
    def get_output_arcs(self) -> List:
        """Get all output arcs from this transition.
        
        Returns:
            List of Arc objects that originate from this transition
            
        Raises:
            AttributeError: If model doesn't have arcs attribute
        """
        if not hasattr(self.model, 'arcs'):
            raise AttributeError(
                f"Model {self.model} does not have 'arcs' attribute. "
                f"Cannot determine output arcs for transition {self.transition.id}"
            )
        
        # Handle both dict and list representations
        arcs_collection = self.model.arcs
        if isinstance(arcs_collection, dict):
            arcs = arcs_collection.values()
        elif isinstance(arcs_collection, list):
            arcs = arcs_collection
        else:
            raise TypeError(
                f"Model.arcs must be dict or list, got {type(arcs_collection)}"
            )
        
        # Use ID comparison (primary) with object reference fallback
        # Netobjects should be dereferenced via properties like source_id, target_id
        transition_id = self.transition.id if hasattr(self.transition, 'id') else str(self.transition)
        result = []
        
        # Use ID comparison (primary) with object reference fallback
        # Netobjects should be dereferenced via properties like source_id, target_id
        transition_id = self.transition.id if hasattr(self.transition, 'id') else str(self.transition)
        result = []
        
        for arc in arcs:
            # Primary: ID comparison via arc.source_id property
            try:
                if hasattr(arc, 'source_id') and arc.source_id == transition_id:
                    result.append(arc)
                    continue
            except (AttributeError, TypeError):
                # Arc structure doesn't support ID access
                pass
            
            # Fallback: Object reference comparison
            try:
                if arc.source == self.transition:
                    result.append(arc)
                    continue
            except (AttributeError, TypeError):
                # Arc doesn't have source reference
                pass
                
            # Last resort: String ID in source
            try:
                if isinstance(arc.source, str) and arc.source == transition_id:
                    result.append(arc)
            except (AttributeError, TypeError):
                # Arc source is not comparable
                pass
        
        return result
    
    def _get_place(self, place_id):
        """Get place object by ID.
        
        Args:
            place_id: ID of the place (string like "P101")
            
        Returns:
            Place object or None if not found
            
        Raises:
            AttributeError: If model doesn't have places attribute
        """
        if not hasattr(self.model, 'places'):
            raise AttributeError(
                f"Model {self.model} does not have 'places' attribute. "
                f"Cannot look up place {place_id}"
            )
        
        # Handle both dict and list representations
        places_collection = self.model.places
        if isinstance(places_collection, dict):
            # Direct lookup
            return places_collection.get(place_id)
        elif isinstance(places_collection, list):
            # Linear search
            return next((p for p in places_collection if p.id == place_id), None)
        else:
            raise TypeError(
                f"Model.places must be dict or list, got {type(places_collection)}"
            )
    
    def _get_arc(self, arc_id):
        """Get arc object by ID.
        
        Args:
            arc_id: ID of the arc (string like "A101")
            
        Returns:
            Arc object or None if not found
            
        Raises:
            AttributeError: If model doesn't have arcs attribute
        """
        if not hasattr(self.model, 'arcs'):
            raise AttributeError(
                f"Model {self.model} does not have 'arcs' attribute. "
                f"Cannot look up arc {arc_id}"
            )
        
        # Handle both dict and list representations
        arcs_collection = self.model.arcs
        if isinstance(arcs_collection, dict):
            # Direct lookup
            return arcs_collection.get(arc_id)
        elif isinstance(arcs_collection, list):
            # Linear search
            return next((a for a in arcs_collection if a.id == arc_id), None)
        else:
            raise TypeError(
                f"Model.arcs must be dict or list, got {type(arcs_collection)}"
            )
    
    def _get_current_time(self) -> float:
        """Get current simulation time from model.
        
        Returns:
            float: Current logical/simulation time
        """
        return getattr(self.model, 'logical_time', 0.0)
    
    def _evaluate_guard(self) -> Tuple[bool, str]:
        """Evaluate guard condition if present.
        
        Guards can be:
        - None/empty: Always passes (True)
        - Boolean (True/False): Direct value
        - Numeric: Treated as threshold (> 0 passes)
        - Callable (lambda/function): Called and result evaluated
        - String expression: Evaluated with place tokens context
        
        Returns:
            Tuple of (passes: bool, reason: str)
            - (True, "guard-passes") if condition met
            - (False, "guard-fails") if condition not met
            - (True, "no-guard") if no guard defined
        """
        # Check if guard exists in properties first (preferred location)
        guard_expr = None
        if hasattr(self.transition, 'properties') and self.transition.properties:
            guard_expr = self.transition.properties.get('guard_function')
        
        # Fallback to direct guard attribute
        if guard_expr is None and hasattr(self.transition, 'guard'):
            guard_expr = self.transition.guard
        
        # No guard means always enabled
        if guard_expr is None or guard_expr == "":
            return True, "no-guard"
        
        # Boolean guard
        if isinstance(guard_expr, bool):
            return guard_expr, f"guard-boolean-{guard_expr}"
        
        # Numeric guard (threshold)
        if isinstance(guard_expr, (int, float)):
            passes = guard_expr > 0
            return passes, f"guard-threshold-{passes}"
        
        # Callable guard (lambda/function) - NEW
        if callable(guard_expr):
            try:
                result = guard_expr()
                passes = bool(result)
                return passes, f"guard-callable-{passes}"
            except Exception as e:
                # Guard evaluation error - fail safe (don't fire)
                return False, f"guard-callable-error: {e}"
        
        # String expression guard - evaluate with place tokens
        if isinstance(guard_expr, str):
            try:
                from shypn.engine.function_catalog import FUNCTION_CATALOG
                
                # Build evaluation context
                context = {'t': self._get_current_time()}
                context.update(FUNCTION_CATALOG)
                
                # Add place tokens as P1, P2, ... (or P88, P105 if ID already has P)
                if hasattr(self.model, 'places'):
                    # Handle both list and dict format for places
                    places_iterable = self.model.places.items() if isinstance(self.model.places, dict) else [(p.id, p) for p in self.model.places]
                    
                    for place_id, place in places_iterable:
                        # Handle both numeric IDs (1, 2, 3) and string IDs ("P88", "P105")
                        if isinstance(place_id, str) and place_id.startswith('P'):
                            # ID already has P prefix (e.g., "P105")
                            context[place_id] = place.tokens
                        else:
                            # Numeric ID needs P prefix (e.g., 1 → P1)
                            context[f'P{place_id}'] = place.tokens
                
                # Evaluate expression safely (replaces eval() for security)
                passes = safe_eval_bool(guard_expr, context, default_on_error=False)
                return passes, f"guard-expr-{passes}"
            except Exception as e:
                # Guard evaluation error - fail safe (don't fire)
                return False, f"guard-eval-error: {e}"
        
        # Unknown guard type - fail safe
        return False, f"guard-unknown-type: {type(guard_expr)}"
    
    def _record_event(self, consumed: Dict[int, float], produced: Dict[int, float], 
                     mode: str = 'logical', **kwargs):
        """Record transition firing event in model history.
        
        Args:
            consumed: Dictionary of {place_id: amount} consumed
            produced: Dictionary of {place_id: amount} produced
            mode: Event mode ('logical', 'timed', etc.)
            **kwargs: Additional event data
        """
        # Store for accounting
        self._last_consumed = consumed.copy()
        self._last_produced = produced.copy()
        
        if hasattr(self.model, 'record_transition_event'):
            try:
                self.model.record_transition_event(
                    self.transition.id,
                    consumed=consumed,
                    produced=produced,
                    mode=mode,
                    **kwargs
                )
            except Exception:
                # Event recording is not critical for firing success
                logger.debug("Transition event recording failed for %s", self.transition.id, exc_info=True)
    
    def get_last_consumed(self) -> Dict[int, float]:
        """Get tokens consumed in last firing.
        
        Returns:
            Dictionary of {place_id: amount} consumed
        """
        return self._last_consumed.copy()
    
    def get_last_produced(self) -> Dict[int, float]:
        """Get tokens produced in last firing.
        
        Returns:
            Dictionary of {place_id: amount} produced
        """
        return self._last_produced.copy()
    
    def enable_accounting(self):
        """Enable token accounting tracking."""
        self._accounting_enabled = True
        
    def disable_accounting(self):
        """Disable token accounting tracking."""
        self._accounting_enabled = False
    
    # ============================================================================
    # String Representation
    # ============================================================================
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"<{self.__class__.__name__} "
                f"transition={self.transition.name} "
                f"type={self.get_type_name()}>")
    
    def __str__(self) -> str:
        """Human-readable string."""
        return f"{self.get_type_name()} behavior for {self.transition.name}"
