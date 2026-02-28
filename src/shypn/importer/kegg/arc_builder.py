"""Standard arc building strategy."""

from typing import List, Dict
from shypn.netobjs import Place, Transition, Arc
from .converter_base import ArcBuilder, ConversionOptions
from .models import KEGGPathway, KEGGReaction


class StandardArcBuilder(ArcBuilder):
    """Standard strategy for creating arcs between places and transitions.
    
    This builder:
    - Creates input arcs from substrate places to transition
    - Creates output arcs from transition to product places
    - Handles stoichiometry (arc weights)
    - Handles reversible reactions (bidirectional arcs or split transitions)
    """
    
    def __init__(self):
        """Initialize arc builder."""
        self.arc_counter = 1
        self.id_manager = None  # Will be set during conversion
    
    def create_arcs(self, reaction: KEGGReaction, transition: Transition,
                   place_map: Dict[str, Place], pathway: KEGGPathway,
                   options: ConversionOptions, document=None) -> List[Arc]:
        """Create arcs for a reaction.
        
        Args:
            reaction: KEGG reaction
            transition: Transition representing the reaction (or forward part)
            place_map: Mapping from KEGG entry ID to Place
            pathway: Complete pathway
            options: Conversion options
            document: Optional DocumentModel for unified arc ID counter
            
        Returns:
            List of Arc objects
        """
        # Use document's IDManager if available
        if document and hasattr(document, 'id_manager'):
            self.id_manager = document.id_manager
        
        arcs = []
        
        # Check if this is a reverse transition (from split reversible)
        is_reverse = (hasattr(transition, 'metadata') and
                     transition.metadata.get('direction') == 'reverse')
        
        if is_reverse:
            # For reverse transition, swap substrates and products
            arcs.extend(self._create_input_arcs(reaction.products, transition, place_map))
            arcs.extend(self._create_output_arcs(reaction.substrates, transition, place_map))
        else:
            # Normal or forward direction
            arcs.extend(self._create_input_arcs(reaction.substrates, transition, place_map))
            arcs.extend(self._create_output_arcs(reaction.products, transition, place_map))
        
        return arcs
    
    def _create_input_arcs(self, substrates, transition: Transition,
                          place_map: Dict[str, Place]) -> List[Arc]:
        """Create input arcs from places to transition.
        
        Args:
            substrates: List of KEGGSubstrate objects (with stoichiometry)
            transition: Target transition
            place_map: Mapping from entry ID to Place
            
        Returns:
            List of Arc objects (place → transition) with stoichiometric weights
        """
        arcs: List[Arc] = []
        
        for substrate in substrates:
            place = place_map.get(substrate.id)
            if place is None:
                # Substrate place not included (e.g., filtered cofactor)
                continue
            
            # VALIDATION: Ensure bipartite property (Place → Transition)
            if not isinstance(place, Place):
                raise ValueError(
                    f"Invalid arc source: {substrate.id} is not a Place. "
                    f"Got {type(place).__name__} instead."
                )
            if not isinstance(transition, Transition):
                raise ValueError(
                    f"Invalid arc target: {transition.id} is not a Transition. "
                    f"Got {type(transition).__name__} instead."
                )
            
            # Create arc from place to transition
            if self.id_manager:
                arc_id = self.id_manager.generate_arc_id()
            else:
                arc_id = f"A{self.arc_counter}"
                self.arc_counter += 1
            
            # Use stoichiometry from substrate as arc weight
            weight = substrate.stoichiometry
            
            # FORMALISM-COMPLIANT ARC CREATION:
            # - coefficient=0 means catalyst/cofactor (non-consuming) → use TestArc (Ft)
            # - coefficient>0 for signal place → use SignalFlowArc (Fs) with Ws ∈ ℝ⁺
            # - coefficient>0 for normal place → use Arc (F)
            arc: Arc
            if weight == 0:
                # Catalyst/cofactor: Use TestArc for non-consuming observation
                from shypn.netobjs.test_arc import TestArc
                arc = TestArc(place, transition, arc_id, "", weight=1.0)  # Test arcs use weight=1 for threshold
            elif getattr(place, 'is_signal_place', False):
                # Signal place with weight>0: Use SignalFlowArc (consumptive regulation)
                from shypn.netobjs.signal_flow_arc import SignalFlowArc
                arc = SignalFlowArc(place, transition, arc_id, "", weight=weight)
            else:
                # Normal place: Use regular Arc (mass transfer)
                arc = Arc(place, transition, arc_id, "", weight=weight)
            
            # Store KEGG metadata including stoichiometry
            if not hasattr(arc, 'metadata'):
                arc.metadata = {}
            arc.metadata['kegg_compound'] = substrate.name
            arc.metadata['source'] = 'KEGG'
            arc.metadata['direction'] = 'input'
            arc.metadata['stoichiometry'] = substrate.stoichiometry
            
            arcs.append(arc)
        
        return arcs
    
    def _create_output_arcs(self, products, transition: Transition,
                           place_map: Dict[str, Place]) -> List[Arc]:
        """Create output arcs from transition to places.
        
        Args:
            products: List of KEGGProduct objects (with stoichiometry)
            transition: Source transition
            place_map: Mapping from entry ID to Place
            
        Returns:
            List of Arc objects (transition → place) with stoichiometric weights
        """
        arcs: List[Arc] = []
        
        for product in products:
            place = place_map.get(product.id)
            if place is None:
                # Product place not included (e.g., filtered cofactor)
                continue
            
            # VALIDATION: Ensure bipartite property (Transition → Place)
            if not isinstance(transition, Transition):
                raise ValueError(
                    f"Invalid arc source: {transition.id} is not a Transition. "
                    f"Got {type(transition).__name__} instead."
                )
            if not isinstance(place, Place):
                raise ValueError(
                    f"Invalid arc target: {product.id} is not a Place. "
                    f"Got {type(place).__name__} instead."
                )
            
            # Create arc from transition to place
            if self.id_manager:
                arc_id = self.id_manager.generate_arc_id()
            else:
                arc_id = f"A{self.arc_counter}"
                self.arc_counter += 1
            
            # Use stoichiometry from product as arc weight
            weight = product.stoichiometry
            
            # FORMALISM-COMPLIANT ARC CREATION:
            # - coefficient=0 means catalyst/cofactor (non-consuming) → use TestArc (Ft)
            # - coefficient>0 for signal place → use SignalFlowArc (Fs) with Ws ∈ ℝ⁺
            # - coefficient>0 for normal place → use Arc (F)
            arc: Arc
            if weight == 0:
                # Catalyst/cofactor: Use TestArc for non-consuming observation
                from shypn.netobjs.test_arc import TestArc
                arc = TestArc(transition, place, arc_id, "", weight=1.0)  # Test arcs use weight=1 for threshold
            elif getattr(place, 'is_signal_place', False):
                # Signal place with weight>0: Use SignalFlowArc (consumptive regulation)
                from shypn.netobjs.signal_flow_arc import SignalFlowArc
                arc = SignalFlowArc(transition, place, arc_id, "", weight=weight)
            else:
                # Normal place: Use regular Arc (mass transfer)
                arc = Arc(transition, place, arc_id, "", weight=weight)
            
            # Store KEGG metadata including stoichiometry
            if not hasattr(arc, 'metadata'):
                arc.metadata = {}
            arc.metadata['kegg_compound'] = product.name
            arc.metadata['source'] = 'KEGG'
            arc.metadata['direction'] = 'output'
            arc.metadata['stoichiometry'] = product.stoichiometry
            
            arcs.append(arc)
        
        return arcs
