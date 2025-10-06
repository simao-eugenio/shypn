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
        
        Does not check type-specific constraints (timing, rates, etc.).
        
        Returns:
            bool: True if structurally enabled, False otherwise
        """
        if not hasattr(self.model, 'is_transition_enabled_logical'):
            # Fallback: check manually
            return self._check_enablement_manual()
        
        return self.model.is_transition_enabled_logical(self.transition.id)
    
    def _check_enablement_manual(self) -> bool:
        """Manual enablement check (fallback if model doesn't provide method).
        
        SHYPN uses "living systems" cooperation semantics:
        - ALL input arcs (normal and inhibitor) check: tokens >= weight
        - Normal arc meaning: "I need weight tokens to function" (necessity)
        - Inhibitor arc meaning: "I need weight tokens surplus to share" (cooperation)
        
        Both prevent firing when tokens < weight, but for different reasons:
        - Normal: insufficient resources
        - Inhibitor: insufficient surplus (starvation prevention)
        
        Returns:
            bool: True if enabled, False otherwise
        """
        input_arcs = self.get_input_arcs()
        
        for arc in input_arcs:
            # Get source place directly from arc reference
            source_place = arc.source
            if source_place is None:
                return False
            
            # Living systems semantics: ALL arcs check for sufficient tokens
            # The semantic meaning differs (need vs. surplus) but check is same
            if source_place.tokens < arc.weight:
                return False
        
        return True
    
    def get_input_arcs(self) -> List:
        """Get all input arcs to this transition.
        
        Returns:
            List of Arc objects that target this transition
        """
        if not hasattr(self.model, 'arcs'):
            return []
        
        # Use object reference comparison, not ID
        return [arc for arc in self.model.arcs.values() 
                if arc.target == self.transition]
    
    def get_output_arcs(self) -> List:
        """Get all output arcs from this transition.
        
        Returns:
            List of Arc objects that originate from this transition
        """
        if not hasattr(self.model, 'arcs'):
            return []
        
        # Use object reference comparison, not ID
        return [arc for arc in self.model.arcs.values() 
                if arc.source == self.transition]
    
    def _get_place(self, place_id: int):
        """Get place object by ID.
        
        Args:
            place_id: Integer ID of the place
            
        Returns:
            Place object or None if not found
        """
        if not hasattr(self.model, 'places'):
            return None
        
        return self.model.places.get(place_id)
    
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
        
        # String expression guard - evaluate with place tokens
        if isinstance(guard_expr, str):
            try:
                from shypn.engine.function_catalog import FUNCTION_CATALOG
                
                # Build evaluation context
                context = {'t': self._get_current_time()}
                context.update(FUNCTION_CATALOG)
                
                # Add place tokens as P1, P2, ...
                if hasattr(self.model, 'places'):
                    for place_id, place in self.model.places.items():
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
