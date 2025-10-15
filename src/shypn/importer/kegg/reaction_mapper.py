"""Standard reaction to transition mapping strategy."""

from typing import List, Tuple
from shypn.netobjs import Transition
from .converter_base import ReactionMapper, ConversionOptions
from .models import KEGGPathway, KEGGReaction, KEGGEntry


class StandardReactionMapper(ReactionMapper):
    """Standard strategy for mapping KEGG reactions to transitions.
    
    This mapper:
    - Creates single transition for normal reactions
    - Optionally splits reversible reactions into forward/backward transitions
    - Calculates transition position from substrate/product locations
    - Extracts enzyme/reaction names
    """
    
    def __init__(self):
        """Initialize reaction mapper."""
        self.transition_counter = 1
    
    def create_transitions(self, reaction: KEGGReaction, pathway: KEGGPathway,
                          options: ConversionOptions) -> List[Transition]:
        """Create Transition(s) from a KEGG reaction.
        
        Args:
            reaction: KEGG reaction to convert
            pathway: Complete pathway (for context)
            options: Conversion options
            
        Returns:
            List of Transition objects (one for normal, two for split reversible)
        """
        # Get substrate and product entries for position calculation
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
            x, y: Position coordinates
            name: Transition name/label
            
        Returns:
            Transition object
        """
        transition_id = f"T{self.transition_counter}"
        self.transition_counter += 1
        
        transition = Transition(x, y, transition_id, name)
        transition.label = name
        
        # Store KEGG metadata
        if not hasattr(transition, 'metadata'):
            transition.metadata = {}
        transition.metadata['kegg_reaction_id'] = reaction.id
        transition.metadata['kegg_reaction_name'] = reaction.name
        transition.metadata['source'] = 'KEGG'
        transition.metadata['reversible'] = reaction.is_reversible()
        
        # Store reaction type if available
        if hasattr(reaction, 'type'):
            transition.metadata['reaction_type'] = reaction.type
        
        return transition
    
    def _create_split_reversible(self, reaction: KEGGReaction, x: float, y: float,
                                 base_name: str) -> List[Transition]:
        """Create forward and backward transitions for a reversible reaction.
        
        Args:
            reaction: KEGG reaction (must be reversible)
            x, y: Position coordinates
            base_name: Base name for transitions
            
        Returns:
            List of two Transition objects [forward, backward]
        """
        transitions = []
        
        # Forward transition
        forward_id = f"T{self.transition_counter}"
        self.transition_counter += 1
        forward_name = f"{base_name} (forward)"
        forward = Transition(x - 10, y, forward_id, forward_name)
        forward.label = forward_name
        
        if not hasattr(forward, 'metadata'):
            forward.metadata = {}
        forward.metadata['kegg_reaction_id'] = reaction.id
        forward.metadata['kegg_reaction_name'] = reaction.name
        forward.metadata['source'] = 'KEGG'
        forward.metadata['reversible'] = True
        forward.metadata['direction'] = 'forward'
        
        transitions.append(forward)
        
        # Backward transition
        backward_id = f"T{self.transition_counter}"
        self.transition_counter += 1
        backward_name = f"{base_name} (backward)"
        backward = Transition(x + 10, y, backward_id, backward_name)
        backward.label = backward_name
        
        if not hasattr(backward, 'metadata'):
            backward.metadata = {}
        backward.metadata['kegg_reaction_id'] = reaction.id
        backward.metadata['kegg_reaction_name'] = reaction.name
        backward.metadata['source'] = 'KEGG'
        backward.metadata['reversible'] = True
        backward.metadata['direction'] = 'reverse'
        
        transitions.append(backward)
        
        return transitions
    
    def get_reaction_position(self, reaction: KEGGReaction, pathway: KEGGPathway,
                             substrates: List[KEGGEntry], products: List[KEGGEntry],
                             options: ConversionOptions) -> Tuple[float, float]:
        """Calculate position for reaction transition.
        
        Strategy: Place transition at the centroid of substrate and product positions.
        
        Args:
            reaction: KEGG reaction
            pathway: Complete pathway
            substrates: List of substrate entries
            products: List of product entries
            options: Conversion options
            
        Returns:
            Tuple of (x, y) coordinates
        """
        # Collect all participant positions
        positions = []
        
        for entry in substrates + products:
            if entry and entry.graphics:
                positions.append((entry.graphics.x, entry.graphics.y))
        
        # If no positions available, use a default
        if not positions:
            return (100.0 * options.coordinate_scale + options.center_x,
                   100.0 * options.coordinate_scale + options.center_y)
        
        # Calculate centroid
        avg_x = sum(x for x, y in positions) / len(positions)
        avg_y = sum(y for x, y in positions) / len(positions)
        
        # Apply scaling and offset
        x = avg_x * options.coordinate_scale + options.center_x
        y = avg_y * options.coordinate_scale + options.center_y
        
        return (x, y)
    
    def get_reaction_name(self, reaction: KEGGReaction, pathway: KEGGPathway) -> str:
        """Extract a clean reaction name.
        
        Priority:
        1. Enzyme name from reaction
        2. Reaction name from reaction
        3. Reaction ID
        
        Args:
            reaction: KEGG reaction
            pathway: Complete pathway
            
        Returns:
            Clean reaction name string
        """
        # Try to get enzyme name from reaction
        if hasattr(reaction, 'enzyme') and reaction.enzyme:
            # Clean up enzyme name
            name = str(reaction.enzyme)
            name = name.replace('\n', ' ')
            name = ' '.join(name.split())
            return name
        
        # Try reaction name
        if hasattr(reaction, 'name') and reaction.name:
            name = str(reaction.name)
            # Extract ID if in format "rn:R00001"
            if ':' in name:
                name = name.split(':')[-1]
            return name
        
        # Fallback to reaction ID
        return f"Reaction_{reaction.id}"
