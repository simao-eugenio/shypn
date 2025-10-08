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
                   options: ConversionOptions) -> List[Arc]:
        """Create arcs for a reaction.
        
        Args:
            reaction: KEGG reaction
            transition: Transition representing the reaction (or forward part)
            place_map: Mapping from KEGG entry ID to Place
            pathway: Complete pathway
            options: Conversion options
            
        Returns:
            List of Arc objects
        """
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
            substrates: List of KEGGSubstrate objects
            transition: Target transition
            place_map: Mapping from entry ID to Place
            
        Returns:
            List of Arc objects (place → transition)
        """
        arcs = []
        
        for substrate in substrates:
            place = place_map.get(substrate.id)
            if place is None:
                # Substrate place not included (e.g., filtered cofactor)
                continue
            
            # Create arc from place to transition
            arc_id = f"A{self.arc_counter}"
            self.arc_counter += 1
            
            arc = Arc(place, transition, arc_id, "", weight=1)
            
            # Store KEGG metadata
            if not hasattr(arc, 'metadata'):
                arc.metadata = {}
            arc.metadata['kegg_compound'] = substrate.name
            arc.metadata['source'] = 'KEGG'
            arc.metadata['direction'] = 'input'
            
            arcs.append(arc)
        
        return arcs
    
    def _create_output_arcs(self, products, transition: Transition,
                           place_map: Dict[str, Place]) -> List[Arc]:
        """Create output arcs from transition to places.
        
        Args:
            products: List of KEGGProduct objects
            transition: Source transition
            place_map: Mapping from entry ID to Place
            
        Returns:
            List of Arc objects (transition → place)
        """
        arcs = []
        
        for product in products:
            place = place_map.get(product.id)
            if place is None:
                # Product place not included (e.g., filtered cofactor)
                continue
            
            # Create arc from transition to place
            arc_id = f"A{self.arc_counter}"
            self.arc_counter += 1
            
            arc = Arc(transition, place, arc_id, "", weight=1)
            
            # Store KEGG metadata
            if not hasattr(arc, 'metadata'):
                arc.metadata = {}
            arc.metadata['kegg_compound'] = product.name
            arc.metadata['source'] = 'KEGG'
            arc.metadata['direction'] = 'output'
            
            arcs.append(arc)
        
        return arcs
