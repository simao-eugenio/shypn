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
        
        Returns:
            bool: True if enabled, False otherwise
        """
        input_arcs = self.get_input_arcs()
        
        for arc in input_arcs:
            # Skip inhibitor arcs
            kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
            if kind != 'normal':
                continue
            
            # Get source place
            source_place = self._get_place(arc.source_id)
            if source_place is None:
                return False
            
            # Check sufficient tokens
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
        
        return [arc for arc in self.model.arcs.values() 
                if getattr(arc, 'target_id', None) == self.transition.id]
    
    def get_output_arcs(self) -> List:
        """Get all output arcs from this transition.
        
        Returns:
            List of Arc objects that originate from this transition
        """
        if not hasattr(self.model, 'arcs'):
            return []
        
        return [arc for arc in self.model.arcs.values() 
                if getattr(arc, 'source_id', None) == self.transition.id]
    
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
