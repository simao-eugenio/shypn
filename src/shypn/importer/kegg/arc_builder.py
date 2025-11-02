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
        # Use document's arc counter if available (avoids ID conflicts with test arcs)
        if document and hasattr(document, '_next_arc_id'):
            self.arc_counter = document._next_arc_id
        
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
        
        # Sync counter back to document (for unified ID management)
        if document and hasattr(document, '_next_arc_id'):
            document._next_arc_id = self.arc_counter
        
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
        arcs = []
        
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
            arc_id = f"A{self.arc_counter}"
            self.arc_counter += 1
            
            # Use stoichiometry from substrate as arc weight
            weight = substrate.stoichiometry
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
        arcs = []
        
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
            arc_id = f"A{self.arc_counter}"
            self.arc_counter += 1
            
            # Use stoichiometry from product as arc weight
            weight = product.stoichiometry
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
