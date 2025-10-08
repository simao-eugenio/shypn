"""Standard reaction to transition mapping strategy."""

from typing import List
from shypn.netobjs import Transition
from .converter_base import ReactionMapper, ConversionOptions
from .models import KEGGPathway, KEGGReaction, KEGGEntry


class StandardReactionMapper(ReactionMapper):
    """Standard strategy for mapping KEGG reactions to Petri net transitions.
    
    This mapper:
    - Converts each reaction to a transition
    - Optionally splits reversible reactions into forward/reverse
    - Positions transitions between substrates and products
    - Extracts enzyme names for labels
    """
    
    def create_transitions(self, reaction: KEGGReaction, pathway: KEGGPathway,
                          options: ConversionOptions) -> List[Transition]:
        """Create Transition(s) from reaction.
        
        Args:
            reaction: KEGG reaction
            pathway: Complete pathway
            options: Conversion options
            
        Returns:
            List with 1 transition (irreversible or unsplit reversible)
            or 2 transitions (split reversible: forward and reverse)
        """
        # Get substrate and product entries
        substrates = [pathway.get_entry_by_id(s.id) for s in reaction.substrates]
        substrates = [s for s in substrates if s is not None]
        
        products = [pathway.get_entry_by_id(p.id) for p in reaction.products]
        products = [p for p in products if p is not None]
        
        # Calculate position
        x, y = self.get_reaction_position(reaction, pathway, substrates, products, options)
        
        # Get base name
        base_name = self.get_reaction_name(reaction, pathway)
        
        # Check if should split reversible
        if reaction.is_reversible() and options.split_reversible:
            return self._create_split_reversible(reaction, x, y, base_name)
        else:
            return [self._create_single_transition(reaction, x, y, base_name)]
    
    def _create_single_transition(self, reaction: KEGGReaction, x: float, y: float,
                                 name: str) -> Transition:
        """Create a single transition for a reaction.
        
        Args:
            reaction: KEGG reaction
            x: X coordinate
            y: Y coordinate
            name: Transition name
            
        Returns:
            Transition object
        """
        # Create transition ID (T prefix + reaction ID)
        transition_id = f"T{reaction.id}"
        
        # Create transition
        transition = Transition(x, y, transition_id, 0)
        transition.label = name
        
        # Store KEGG metadata
        if not hasattr(transition, 'metadata'):
            transition.metadata = {}
        transition.metadata['kegg_id'] = reaction.name
        transition.metadata['kegg_reaction_id'] = reaction.id
        transition.metadata['reversible'] = reaction.is_reversible()
        transition.metadata['source'] = 'KEGG'
        
        return transition
    
    def _create_split_reversible(self, reaction: KEGGReaction, x: float, y: float,
                                base_name: str) -> List[Transition]:
        """Create forward and reverse transitions for reversible reaction.
        
        Args:
            reaction: KEGG reaction
            x: X coordinate (will be offset)
            y: Y coordinate
            base_name: Base transition name
            
        Returns:
            List of [forward_transition, reverse_transition]
        """
        # Offset positions slightly
        offset = 30.0
        
        # Forward transition
        fwd_id = f"T{reaction.id}_fwd"
        fwd = Transition(x - offset, y, fwd_id, 0)
        fwd.label = f"{base_name} →"
        
        if not hasattr(fwd, 'metadata'):
            fwd.metadata = {}
        fwd.metadata['kegg_id'] = reaction.name
        fwd.metadata['kegg_reaction_id'] = reaction.id
        fwd.metadata['direction'] = 'forward'
        fwd.metadata['source'] = 'KEGG'
        
        # Reverse transition
        rev_id = f"T{reaction.id}_rev"
        rev = Transition(x + offset, y, rev_id, 0)
        rev.label = f"{base_name} ←"
        
        if not hasattr(rev, 'metadata'):
            rev.metadata = {}
        rev.metadata['kegg_id'] = reaction.name
        rev.metadata['kegg_reaction_id'] = reaction.id
        rev.metadata['direction'] = 'reverse'
        rev.metadata['source'] = 'KEGG'
        
        return [fwd, rev]
