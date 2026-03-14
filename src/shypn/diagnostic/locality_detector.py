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
        pass
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Any
from dataclasses import dataclass, field


if TYPE_CHECKING:
    from shypn.netobjs.transition import Transition


@dataclass
class Locality:
    """Represents a transition-centered locality.
    
    A locality consists of:
    - One central transition
    - Input places (places that feed tokens TO the transition)
    - Output places (places that receive tokens FROM the transition)
    - Input arcs (place → transition)
    - Output arcs (transition → place)
    - Catalyst places (non-consuming, connected via TestArcs)
    - Catalyst-substrate places (dual role: catalyst + substrate)
    
    Attributes:
        transition: The central transition object
        input_places: List of places that feed TO transition
        output_places: List of places that receive FROM transition
        input_arcs: List of arcs (place → transition)
        output_arcs: List of arcs (transition → place)
        catalyst_places: List of places connected via TestArcs (non-consuming)
        catalyst_arcs: List of TestArcs (place ⋯→ transition)
        dual_role_places: List of places that are BOTH catalyst AND substrate
    
    Example:
        # Valid locality: P1 → T1 → P2, with enzyme E1
        locality = Locality(
            transition=t1,
            input_places=[p1],
            output_places=[p2],
            input_arcs=[arc1],
            output_arcs=[arc2],
            catalyst_places=[e1],
            catalyst_arcs=[test_arc1]
        )
        
        assert locality.is_valid  # True (has inputs AND outputs)
    """
    transition: Any
    input_places: List[Any] = field(default_factory=list)
    output_places: List[Any] = field(default_factory=list)
    input_arcs: List[Any] = field(default_factory=list)
    output_arcs: List[Any] = field(default_factory=list)
    catalyst_places: List[Any] = field(default_factory=list)
    catalyst_arcs: List[Any] = field(default_factory=list)
    dual_role_places: List[Any] = field(default_factory=list)
    
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
        """Total number of unique places in locality.
        
        Counts all unique places (input + output + catalyst-only).
        Dual-role places are counted once.
        
        Returns:
            Count of unique places
        """
        # Use set to avoid counting dual-role places twice
        all_places = set(self.input_places) | set(self.output_places) | set(self.catalyst_places)
        return len(all_places)
    
    @property
    def catalyst_count(self) -> int:
        """Total number of catalyst places.
        
        Returns:
            Count of catalyst places (including dual-role)
        """
        return len(self.catalyst_places)
    
    @property
    def dual_role_count(self) -> int:
        """Number of places that are BOTH catalyst AND substrate.
        
        Returns:
            Count of dual-role places
        """
        return len(self.dual_role_places)
    
    def get_summary(self) -> str:
        """Get human-readable summary with catalyst information.
        
        Returns:
            String like "2 inputs → TransitionName → 3 outputs [+1 catalyst]"
            Or "1 input → TransitionName → 2 outputs [+2 catalysts, 1 dual-role]"
        """
        locality_type = self.locality_type
        
        # Build catalyst suffix
        catalyst_info = []
        if self.catalyst_count > 0:
            catalyst_info.append(f"{self.catalyst_count} catalyst{'s' if self.catalyst_count != 1 else ''}")
        if self.dual_role_count > 0:
            catalyst_info.append(f"{self.dual_role_count} dual-role")
        
        catalyst_suffix = f" [+{', '.join(catalyst_info)}]" if catalyst_info else ""
        
        if locality_type == 'source':
            return (f"{self.transition.name} (source) → "
                    f"{len(self.output_places)} output{'s' if len(self.output_places) != 1 else ''}"
                    f"{catalyst_suffix}")
        elif locality_type == 'sink':
            return (f"{len(self.input_places)} input{'s' if len(self.input_places) != 1 else ''} → "
                    f"{self.transition.name} (sink)"
                    f"{catalyst_suffix}")
        else:
            return (f"{len(self.input_places)} input{'s' if len(self.input_places) != 1 else ''} → "
                    f"{self.transition.name} → "
                    f"{len(self.output_places)} output{'s' if len(self.output_places) != 1 else ''}"
                    f"{catalyst_suffix}")


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
        2. Classify arcs by type and direction:
           - Normal input arcs: substrate consumption (place → transition)
           - Normal output arcs: product formation (transition → place)
           - Test arcs: catalyst/enzyme (place ⋯→ transition, non-consuming)
           - Inhibitor arcs: regulatory control (place ⊣ transition)
        3. Identify dual-role places (both catalyst AND substrate)
        4. Build comprehensive Locality object
        
        CATALYST DETECTION:
        - Test arcs (arc_type == 'test'): Pure catalysts (enzymes, cofactors)
        - Dual-role detection: Place connected by BOTH TestArc AND normal Arc
          Example: AMP in yeast glycolysis (activator + substrate)
        
        IMPORTANT: Includes ALL arc types that affect transition behavior:
        - Normal arcs: Material flow (substrates → transition → products)
        - Test arcs: Catalytic control (enzymes/cofactors that enable reaction)
        - Inhibitor arcs: Regulatory control (products that inhibit reaction)
        
        Excludes only legacy catalyst places (is_catalyst=True flag), which is
        a deprecated decoration system separate from test arc semantics.
        
        Args:
            transition: Transition object to analyze
            
        Returns:
            Locality object with catalyst information (may be invalid if no inputs/outputs)
            
        Example:
            locality = detector.get_locality_for_transition(t1)
            
            if locality.is_valid:
                print(f"Catalysts: {len(locality.catalyst_places)}")
                print(f"Dual-role: {len(locality.dual_role_places)}")
        """
        from shypn.netobjs.test_arc import TestArc


        
        locality = Locality(transition=transition)
        
        # Check if model has arcs
        if not hasattr(self.model, 'arcs'):
            return locality
        
        # Track places by their roles for dual-role detection
        substrate_places = set()  # Places with normal input arcs
        catalyst_places_set = set()  # Places with test arcs
        
        # Scan all arcs in model
        # Model uses lists, not dictionaries
        for arc in self.model.arcs:
            # INCLUDE ALL arc types that affect transition behavior:
            # - Normal arcs: material flow (consume/produce tokens)
            # - Test arcs: catalytic control (affect rate without consumption)
            # - Inhibitor arcs: negative feedback (block when product accumulates)
            # All three arc types define the transition's regulatory context
            
            # NOTE: Removed legacy is_catalyst flag check - it conflicts with TestArc semantics
            # The proper way to mark catalysts is using TestArc class, not is_catalyst flag
            
            # Check if arc targets this transition
            if arc.target == transition:
                # Test arc: Catalyst (non-consuming)
                if isinstance(arc, TestArc):
                    locality.catalyst_arcs.append(arc)
                    if arc.source not in locality.catalyst_places:
                        locality.catalyst_places.append(arc.source)
                    catalyst_places_set.add(arc.source)
                else:
                    # Normal or inhibitor input arc: Substrate/Regulator (consuming)
                    locality.input_arcs.append(arc)
                    if arc.source not in locality.input_places:
                        locality.input_places.append(arc.source)
                    # Track for dual-role detection (only normal arcs, not inhibitors)
                    if arc.arc_type == 'normal':
                        substrate_places.add(arc.source)
            
            # Output arc: transition → place
            elif arc.source == transition:
                locality.output_arcs.append(arc)
                if arc.target not in locality.output_places:
                    locality.output_places.append(arc.target)
        
        # Identify dual-role places: in BOTH catalyst_places_set AND substrate_places
        dual_role_set = catalyst_places_set & substrate_places
        locality.dual_role_places = list(dual_role_set)
        
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