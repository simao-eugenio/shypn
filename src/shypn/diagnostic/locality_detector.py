#!/usr/bin/env python3
"""Locality Detector - Detect transition neighborhoods (locality patterns).

This module provides the LocalityDetector class for identifying localities
in Petri nets based on arc connectivity.

Locality Concept:
    A locality is a transition-centered neighborhood consisting of its
    connected places via input and/or output arcs.
    
    Locality L(T) = •T ∪ T•  (preset union postset)
    
    Valid Patterns:
    1. Normal:   Pn → T → Pm  (n ≥ 1 inputs, m ≥ 1 outputs)
    2. Source:   T → Pm       (no inputs, m ≥ 1 outputs)
    3. Sink:     Pn → T       (n ≥ 1 inputs, no outputs)
    4. Multiple: T1 → P ← T2  (shared places allowed)
    
    A locality is valid if it has at least ONE connected place.

Example:
    detector = LocalityDetector(model)
    locality = detector.get_locality_for_transition(transition)
    
    if locality.is_valid:
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Locality:
    """Represents a transition-centered locality.
    
    A locality consists of:
    - One central transition
    - Input places (places that feed tokens TO the transition)
    - Output places (places that receive tokens FROM the transition)
    - Input arcs (place → transition)
    - Output arcs (transition → place)
    
    Attributes:
        transition: The central transition object
        input_places: List of places that feed TO transition
        output_places: List of places that receive FROM transition
        input_arcs: List of arcs (place → transition)
        output_arcs: List of arcs (transition → place)
    
    Example:
        # Valid locality: P1 → T1 → P2
        locality = Locality(
            transition=t1,
            input_places=[p1],
            output_places=[p2],
            input_arcs=[arc1],
            output_arcs=[arc2]
        )
        
        assert locality.is_valid  # True (has inputs AND outputs)
    """
    transition: Any
    input_places: List[Any] = field(default_factory=list)
    output_places: List[Any] = field(default_factory=list)
    input_arcs: List[Any] = field(default_factory=list)
    output_arcs: List[Any] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        """Check if locality is valid.
        
        A valid locality is a transition with at least one connected place
        (either input or output, or both).
        
        Valid locality patterns:
        - Normal: Pn → T → Pm (n ≥ 1 inputs AND m ≥ 1 outputs)
        - Source: T → Pm (no inputs, m ≥ 1 outputs) - token generation
        - Sink: Pn → T (n ≥ 1 inputs, no outputs) - token consumption
        - Multiple-source: T1 → P ← T2 (shared output place)
        
        Shared places are allowed (organic system structure).
        
        Returns:
            True if locality has at least ONE place (input OR output or both)
        """
        # A locality is valid if it has at least one connected place
        # This accepts: Normal (P→T→P), Source (T→P), Sink (P→T), and shared patterns
        return len(self.input_places) >= 1 or len(self.output_places) >= 1
    
    @property
    def locality_type(self) -> str:
        """Get locality type based on arc pattern.
        
        Classification:
        - 'source': T → P pattern (no inputs, has outputs)
        - 'sink': P → T pattern (has inputs, no outputs)  
        - 'normal': P → T → P pattern (has both inputs and outputs)
        - 'invalid': Isolated transition (no inputs, no outputs)
        
        Returns:
            'source' | 'sink' | 'normal' | 'invalid'
        """
        has_inputs = len(self.input_places) >= 1
        has_outputs = len(self.output_places) >= 1
        
        if not has_inputs and not has_outputs:
            return 'invalid'  # Isolated transition (no connected places)
        elif not has_inputs and has_outputs:
            return 'source'   # T→P pattern (token generation)
        elif has_inputs and not has_outputs:
            return 'sink'     # P→T pattern (token consumption)
        else:
            return 'normal'   # P→T→P pattern (normal flow)
    
    @property
    def place_count(self) -> int:
        """Total number of places in locality.
        
        Returns:
            Sum of input and output places
        """
        return len(self.input_places) + len(self.output_places)
    
    def get_summary(self) -> str:
        """Get human-readable summary with source/sink awareness.
        
        Returns:
            String like "2 inputs → TransitionName → 3 outputs"
            Or "TransitionName (source) → 2 outputs"
            Or "1 input → TransitionName (sink)"
        """
        locality_type = self.locality_type
        
        if locality_type == 'source':
            return (f"{self.transition.name} (source) → "
                    f"{len(self.output_places)} output{'s' if len(self.output_places) != 1 else ''}")
        elif locality_type == 'sink':
            return (f"{len(self.input_places)} input{'s' if len(self.input_places) != 1 else ''} → "
                    f"{self.transition.name} (sink)")
        else:
            return (f"{len(self.input_places)} input{'s' if len(self.input_places) != 1 else ''} → "
                    f"{self.transition.name} → "
                    f"{len(self.output_places)} output{'s' if len(self.output_places) != 1 else ''}")


class LocalityDetector:
    """Detector for transition-centered localities.
    
    This class analyzes Petri net structure to identify localities:
    each locality consists of a central transition with its connected
    input and output places.
    
    The detector works by examining arc connectivity:
    - Input arcs: place → transition (these places provide tokens)
    - Output arcs: transition → place (these places receive tokens)
    
    Attributes:
        model: Reference to PetriNetModel
    
    Example:
        detector = LocalityDetector(model)
        
        # Detect locality for one transition
        locality = detector.get_locality_for_transition(transition)
        if locality.is_valid:
            for place in locality.input_places:
            for place in locality.output_places:
        
        # Detect all valid localities in model
        all_localities = detector.get_all_localities()
        
        # Find shared places
        shared = detector.find_shared_places()
        for place_id, transitions in shared.items():
    """
    
    def __init__(self, model: Any):
        """Initialize detector with model reference.
        
        Args:
            model: PetriNetModel instance (must have .arcs and .transitions)
        """
        self.model = model
    
    def get_locality_for_transition(self, transition: Any) -> Locality:
        """Detect locality for a specific transition.
        
        Algorithm:
        1. Scan all arcs in model
        2. Classify arcs as input (place → transition) or output (transition → place)
        3. Extract places from arcs (avoiding duplicates)
        4. Build Locality object
        
        Args:
            transition: Transition object to analyze
            
        Returns:
            Locality object (may be invalid if no inputs/outputs)
            
        Example:
            locality = detector.get_locality_for_transition(t1)
            
            if locality.is_valid:
            else:
                      f"{len(locality.output_places)} outputs")
        """
        locality = Locality(transition=transition)
        
        # Check if model has arcs
        if not hasattr(self.model, 'arcs'):
            return locality
        
        # Scan all arcs in model
        # Model uses lists, not dictionaries
        for arc in self.model.arcs:
            # Input arc: place → transition
            if arc.target == transition:
                locality.input_arcs.append(arc)
                if arc.source not in locality.input_places:
                    locality.input_places.append(arc.source)
            
            # Output arc: transition → place
            elif arc.source == transition:
                locality.output_arcs.append(arc)
                if arc.target not in locality.output_places:
                    locality.output_places.append(arc.target)
        
        return locality
    
    def get_all_localities(self) -> List[Locality]:
        """Detect localities for all transitions in model.
        
        Only returns valid localities (those with both inputs and outputs).
        
        Returns:
            List of valid Locality objects
            
        Example:
            localities = detector.get_all_localities()
            
            for locality in localities:
        """
        localities = []
        
        # Check if model has transitions
        if not hasattr(self.model, 'transitions'):
            return localities
        
        # Detect locality for each transition
        # Model uses lists, not dictionaries
        for transition in self.model.transitions:
            locality = self.get_locality_for_transition(transition)
            if locality.is_valid:
                localities.append(locality)
        
        return localities
    
    def find_shared_places(self) -> Dict[str, List['Transition']]:
        """
        Find places that are shared between multiple localities.
        
        Returns:
            Dictionary mapping place IDs to lists of transitions that share them
        """
        place_to_transitions = {}
        
        # Model uses lists, not dictionaries
        for transition in self.model.transitions:
            locality = self.get_locality_for_transition(transition)
            all_places = locality.input_places + locality.output_places
            
            for place in all_places:
                place_id = place.label
                if place_id not in place_to_transitions:
                    place_to_transitions[place_id] = []
                place_to_transitions[place_id].append(transition)