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
        - Normal arcs: tokens >= weight (standard enablement, CONSUMES)
        - Test arcs: tokens >= weight (catalyst presence, NON-CONSUMING)
        - Inhibitor arcs: tokens < weight (INVERTED - negative feedback)
        
        Biological Semantics:
        - Normal arc: "I need weight tokens to function" (substrate requirement)
        - Test arc: "Catalyst/enzyme must be present" (non-consuming check)
        - Inhibitor arc: "Inhibit reaction when product >= weight" (negative feedback)
        
        Example with weight=10:
        - Normal arc: enabled at 10+ tokens, CONSUMES 10 tokens on fire
        - Test arc: enabled at 10+ tokens, DOES NOT consume on fire
        - Inhibitor arc: DISABLED at 10+ tokens (product inhibition)
        
        This models biological reactions correctly:
        - Substrates are consumed (normal arcs)
        - Enzymes enable but aren't consumed (test arcs)
        - Products can inhibit their own production (inhibitor arcs)
        
        Returns:
            bool: True if enabled, False otherwise
        """
        from shypn.netobjs.inhibitor_arc import InhibitorArc
        from shypn.netobjs.test_arc import TestArc
        
        input_arcs = self.get_input_arcs()
        
        for arc in input_arcs:
            # Get source place directly from arc reference
            source_place = arc.source
            if source_place is None:
                raise ValueError(f"Arc {arc.id if hasattr(arc, 'id') else 'unknown'} has no source place")
            
            # Check based on arc type
            if isinstance(arc, InhibitorArc):
                # Inhibitor: INVERTED check (tokens < weight)
                # Transition DISABLED when place has too many tokens (negative feedback)
                # Transition ENABLED when place has few tokens (allows production)
                if source_place.tokens >= arc.weight:
                    return False  # INHIBITED by excess product
            elif isinstance(arc, TestArc):
                # Test arc: Same enablement as normal (tokens >= weight)
                # BUT does NOT consume tokens on fire (catalyst behavior)
                # This is checked separately in fire() methods via consumes_tokens()
                if source_place.tokens < arc.weight:
                    return False  # Catalyst not present in sufficient quantity
            else:
                # Normal: Standard check (tokens >= weight)
                # Transition enabled when enough substrate available
                if source_place.tokens < arc.weight:
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
        
        # Use object reference comparison, not ID
        return [arc for arc in arcs if arc.target == self.transition]
    
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
        
        # Use object reference comparison, not ID
        return [arc for arc in arcs if arc.source == self.transition]
    
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
                    for place_id, place in self.model.places.items():
                        # Handle both numeric IDs (1, 2, 3) and string IDs ("P88", "P105")
                        if isinstance(place_id, str) and place_id.startswith('P'):
                            # ID already has P prefix (e.g., "P105")
                            context[place_id] = place.tokens
                        else:
                            # Numeric ID needs P prefix (e.g., 1 → P1)
                            context[f'P{place_id}'] = place.tokens
                
                # Evaluate expression safely
                result = eval(guard_expr, {"__builtins__": {}}, context)
                passes = bool(result)
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
                pass
    
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
