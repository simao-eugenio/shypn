"""Viability checker for transition firing conditions.

This module implements viability checking for Petri net transitions, extracted
from SimulationController as part of Phase 2.3.2 quality improvements.

The ViabilityChecker validates:
- Token availability (substrate availability)
- Arc thresholds for all arc types:
  * Normal arcs (Arc, CurvedArc): Consume tokens, disabled when tokens < threshold
  * Signal flow arcs (SignalFlowArc, CurvedSignalFlowArc): Consume tokens, same logic as normal
  * Inhibitor arcs (InhibitorArc, CurvedInhibitorArc): Inverted logic, disabled when tokens >= threshold
  * Test arcs (TestArc): Don't consume, disabled when tokens < threshold
- Guard conditions (regulatory constraints)

This is distinct from thermodynamic validation, which checks equilibrium
consistency of reversible reactions.
"""

from typing import Any, List, Tuple, Optional


class ViabilityChecker:
    """Check if transitions can fire based on structural conditions.
    
    This class validates whether transitions are structurally enabled
    (can fire) based on:
    - Token availability in input places
    - Arc type-specific rules (all 7 arc types supported):
      * Normal: Arc, CurvedArc (consume tokens)
      * Signal: SignalFlowArc, CurvedSignalFlowArc (consume tokens, same logic as normal)
      * Inhibitor: InhibitorArc, CurvedInhibitorArc (inverted logic)
      * Test: TestArc (non-consuming catalyst)
    - Guard condition evaluation
    
    Design Pattern: Extracted stateless checker (can be used by controller and analysis tools)
    
    Key Features:
    - Single transition enablement check
    - Batch validation for transition sets
    - Detailed failure reasons
    - Arc type-aware checking (all 7 arc types)
    - Guard condition support
    
    Usage:
        checker = ViabilityChecker(controller)
        if checker.is_enabled(transition):
            controller.fire(transition)
        
        # Batch check
        if checker.validate_all(transition_set):
            controller.fire_all(transition_set)
    
    Attributes:
        controller: SimulationController instance providing model and behavior access
    """
    
    def __init__(self, controller: Any):
        """Initialize viability checker.
        
        Args:
            controller: SimulationController instance with model and _get_behavior()
        """
        self.controller = controller
    
    def is_enabled(self, transition: Any) -> bool:
        """Check if a specific transition is enabled using behavior dispatch.
        
        Uses the transition's behavior to determine if it can fire based on
        locality (input places and arc weights only).
        
        Args:
            transition: Transition object to check
            
        Returns:
            bool: True if transition can fire, False otherwise
        """
        behavior = self.controller._get_behavior(transition)
        can_fire, reason = behavior.can_fire()
        return can_fire
    
    def is_enabled_with_reason(self, transition: Any) -> Tuple[bool, Optional[str]]:
        """Check if transition is enabled and return reason if not.
        
        Args:
            transition: Transition object to check
            
        Returns:
            Tuple of (enabled, reason):
                - enabled: True if can fire, False otherwise
                - reason: None if enabled, failure reason string if not
        """
        behavior = self.controller._get_behavior(transition)
        can_fire, reason = behavior.can_fire()
        return can_fire, reason
    
    def validate_all(self, transition_set: List) -> bool:
        """Check if all transitions in set are currently enabled.
        
        Pre-flight validation before snapshot to avoid rollback overhead.
        Useful for atomic execution of transition sets.
        
        Args:
            transition_set: List of Transition objects to validate
            
        Returns:
            True if all transitions can fire, False otherwise
            
        Checks:
            1. All input places have sufficient tokens
            2. All guards evaluate to True (if present)
            3. All arc thresholds are met (if applicable)
            
        Example:
            T1: P1(2) --[weight=1]--> T1 ---> P2
            T2: P3(0) --[weight=1]--> T2 ---> P4
            
            validate_all([T1, T2]) → False (P3 has 0 < 1 tokens)
            validate_all([T1]) → True (P1 has 2 >= 1 tokens)
        """
        # Import arc types for proper handling
        from shypn.netobjs.inhibitor_arc import InhibitorArc
        from shypn.netobjs.curved_inhibitor_arc import CurvedInhibitorArc
        from shypn.netobjs.test_arc import TestArc
        
        for transition in transition_set:
            # Find input arcs for this transition
            for arc in self.controller.model.arcs:
                if arc.target == transition:
                    # This is an input arc (place → transition)
                    place = arc.source
                    
                    # Get effective threshold for enablement check
                    # Use threshold if set, otherwise fallback to weight
                    tokens_needed = getattr(arc, 'weight', 1)
                    if hasattr(arc, 'threshold') and arc.threshold is not None:
                        tokens_needed = arc.threshold
                    
                    # Check based on arc type using defensive pattern
                    # All 7 arc types are handled:
                    # 1. Arc (normal, straight)
                    # 2. CurvedArc (normal, curved)
                    # 3. SignalFlowArc (signal, straight) - same logic as normal
                    # 4. CurvedSignalFlowArc (signal, curved) - same logic as normal
                    # 5. InhibitorArc (inhibitor, straight)
                    # 6. CurvedInhibitorArc (inhibitor, curved)
                    # 7. TestArc (catalyst, straight)
                    kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
                    arc_type = getattr(arc, 'arc_type', 'normal')
                    
                    if arc_type == 'inhibitor' or (kind != 'normal' and isinstance(arc, (InhibitorArc, CurvedInhibitorArc))):
                        # Inhibitor arcs (straight + curved): INVERTED check (disabled when tokens >= threshold)
                        if place.tokens >= tokens_needed:
                            return False  # Inhibited by excess
                    elif arc_type == 'test' or (kind != 'normal' and isinstance(arc, TestArc)):
                        # Test arcs: Check threshold but won't consume
                        if place.tokens < tokens_needed:
                            return False  # Catalyst not present
                    else:
                        # Normal arcs (straight + curved) and Signal flow arcs (straight + curved):
                        # All consume tokens, same enablement logic (disabled when tokens < threshold)
                        if place.tokens < tokens_needed:
                            return False  # Not enough tokens
            
            # Check guard condition (if any)
            if hasattr(transition, 'guard') and transition.guard is not None:
                try:
                    if not transition.guard.evaluate():
                        return False  # Guard prevents firing
                except Exception:
                    return False  # Guard evaluation failed
        
        return True  # All transitions can fire
    
    def validate_all_with_reasons(self, transition_set: List) -> Tuple[bool, List[str]]:
        """Check if all transitions can fire and collect failure reasons.
        
        Args:
            transition_set: List of Transition objects to validate
            
        Returns:
            Tuple of (all_enabled, reasons):
                - all_enabled: True if all can fire, False otherwise
                - reasons: List of failure reasons (empty if all_enabled=True)
        """
        from shypn.netobjs.inhibitor_arc import InhibitorArc
        from shypn.netobjs.curved_inhibitor_arc import CurvedInhibitorArc
        from shypn.netobjs.test_arc import TestArc
        
        reasons = []
        
        for transition in transition_set:
            transition_name = getattr(transition, 'name', f'T{transition.id}')
            
            # Find input arcs for this transition
            for arc in self.controller.model.arcs:
                if arc.target == transition:
                    # This is an input arc (place → transition)
                    place = arc.source
                    place_name = getattr(place, 'name', f'P{place.id}')
                    
                    # Get effective threshold for enablement check
                    tokens_needed = getattr(arc, 'weight', 1)
                    if hasattr(arc, 'threshold') and arc.threshold is not None:
                        tokens_needed = arc.threshold
                    
                    # Check based on arc type (supports all 7 arc types)
                    # Curved and signal flow arcs use same consumption logic as normal
                    kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
                    arc_type = getattr(arc, 'arc_type', 'normal')
                    
                    if arc_type == 'inhibitor' or (kind != 'normal' and isinstance(arc, (InhibitorArc, CurvedInhibitorArc))):
                        # Inhibitor arcs: INVERTED check
                        if place.tokens >= tokens_needed:
                            reasons.append(
                                f"{transition_name}: Inhibited by {place_name} "
                                f"(has {place.tokens} >= threshold {tokens_needed})"
                            )
                    elif arc_type == 'test' or (kind != 'normal' and isinstance(arc, TestArc)):
                        # Test arcs: Check presence
                        if place.tokens < tokens_needed:
                            reasons.append(
                                f"{transition_name}: Test arc from {place_name} not satisfied "
                                f"(has {place.tokens} < threshold {tokens_needed})"
                            )
                    else:
                        # Normal, Curved, SignalFlow, CurvedSignalFlow arcs: Standard check
                        if place.tokens < tokens_needed:
                            reasons.append(
                                f"{transition_name}: Insufficient tokens in {place_name} "
                                f"(has {place.tokens} < needed {tokens_needed})"
                            )
            
            # Check guard condition
            if hasattr(transition, 'guard') and transition.guard is not None:
                try:
                    if not transition.guard.evaluate():
                        reasons.append(f"{transition_name}: Guard condition false")
                except Exception as e:
                    reasons.append(f"{transition_name}: Guard evaluation error ({e})")
        
        return (len(reasons) == 0, reasons)
    
    def get_enabled_transitions(self) -> List:
        """Get list of all currently enabled transitions.
        
        Returns:
            List of Transition objects that can currently fire
        """
        enabled = []
        for transition in self.controller.model.transitions:
            if self.is_enabled(transition):
                enabled.append(transition)
        return enabled
    
    def get_disabled_transitions_with_reasons(self) -> List[Tuple]:
        """Get list of disabled transitions with reasons.
        
        Returns:
            List of (transition, reason) tuples for disabled transitions
        """
        disabled = []
        for transition in self.controller.model.transitions:
            can_fire, reason = self.is_enabled_with_reason(transition)
            if not can_fire:
                disabled.append((transition, reason))
        return disabled
