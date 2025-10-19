"""Standard reaction to transition mapping strategy."""

import logging
from typing import List, Tuple, Dict, Optional
from shypn.netobjs import Transition
from .converter_base import ReactionMapper, ConversionOptions
from .models import KEGGPathway, KEGGReaction, KEGGEntry
from shypn.data.kegg_ec_fetcher import get_default_fetcher

logger = logging.getLogger(__name__)


class StandardReactionMapper(ReactionMapper):
    """Standard strategy for mapping KEGG reactions to transitions.
    
    This mapper:
    - Creates single transition for normal reactions
    - Optionally splits reversible reactions into forward/backward transitions
    - Calculates transition position from substrate/product locations
    - Extracts enzyme/reaction names
    - Supports pre-fetched EC numbers for performance
    """
    
    def __init__(self):
        """Initialize reaction mapper."""
        self.transition_counter = 1
        self.ec_cache: Dict[str, List[str]] = {}  # Cache for pre-fetched EC numbers
    
    def set_ec_cache(self, ec_cache: Dict[str, List[str]]):
        """
        Set pre-fetched EC numbers cache.
        
        This allows the pathway converter to pre-fetch all EC numbers
        in parallel, then pass them to the mapper for fast lookup.
        
        Args:
            ec_cache: Dictionary mapping reaction name → EC numbers
        """
        self.ec_cache = ec_cache
        logger.debug(f"EC cache set with {len(ec_cache)} entries")
    
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
        transition_name = f"T{self.transition_counter}"  # System-assigned name
        self.transition_counter += 1
        
        # Create transition with correct arguments: (x, y, id, name)
        # The reaction name becomes the label, not the system name
        transition = Transition(x, y, transition_id, transition_name, label=name)
        
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
        
        # Get EC numbers (from pre-fetched cache or fetch now)
        # Use reaction.name (KEGG reaction ID like "rn:R00710")
        # not reaction.id (internal entry ID like "61")
        ec_numbers = []
        
        # Try pre-fetched cache first (fast)
        if reaction.name in self.ec_cache:
            ec_numbers = self.ec_cache[reaction.name]
            logger.debug(f"Using cached EC numbers for {reaction.name}: {ec_numbers}")
        else:
            # Fall back to fetching now (slower, but still works)
            try:
                fetcher = get_default_fetcher()
                ec_numbers = fetcher.fetch_ec_numbers(reaction.name)
                
                if ec_numbers:
                    logger.debug(f"Fetched EC numbers for {reaction.name}: {ec_numbers}")
            except Exception as e:
                logger.warning(f"Failed to fetch EC numbers for {reaction.name}: {e}")
        
        # Store EC numbers in metadata
        if ec_numbers:
            transition.metadata['ec_numbers'] = ec_numbers
        
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
        
        # Get EC numbers once for both directions (from cache or fetch)
        # Use reaction.name (KEGG reaction ID like "rn:R00710")
        # not reaction.id (internal entry ID like "61")
        ec_numbers = []
        
        # Try pre-fetched cache first (fast)
        if reaction.name in self.ec_cache:
            ec_numbers = self.ec_cache[reaction.name]
            logger.debug(f"Using cached EC numbers for {reaction.name}: {ec_numbers}")
        else:
            # Fall back to fetching now
            try:
                fetcher = get_default_fetcher()
                ec_numbers = fetcher.fetch_ec_numbers(reaction.name)
                if ec_numbers:
                    logger.debug(f"Fetched EC numbers for {reaction.name}: {ec_numbers}")
            except Exception as e:
                logger.warning(f"Failed to fetch EC numbers for {reaction.name}: {e}")
        
        # Forward transition
        forward_id = f"T{self.transition_counter}"
        forward_sys_name = f"T{self.transition_counter}"  # System-assigned name
        self.transition_counter += 1
        forward_label = f"{base_name} (forward)"  # User-visible label
        forward = Transition(x - 10, y, forward_id, forward_sys_name, label=forward_label)
        
        if not hasattr(forward, 'metadata'):
            forward.metadata = {}
        forward.metadata['kegg_reaction_id'] = reaction.id
        forward.metadata['kegg_reaction_name'] = reaction.name
        forward.metadata['source'] = 'KEGG'
        forward.metadata['reversible'] = True
        forward.metadata['direction'] = 'forward'
        if ec_numbers:
            forward.metadata['ec_numbers'] = ec_numbers
        
        transitions.append(forward)
        
        # Backward transition
        backward_id = f"T{self.transition_counter}"
        backward_sys_name = f"T{self.transition_counter}"  # System-assigned name
        self.transition_counter += 1
        backward_label = f"{base_name} (backward)"  # User-visible label
        backward = Transition(x + 10, y, backward_id, backward_sys_name, label=backward_label)
        
        if not hasattr(backward, 'metadata'):
            backward.metadata = {}
        backward.metadata['kegg_reaction_id'] = reaction.id
        backward.metadata['kegg_reaction_name'] = reaction.name
        backward.metadata['source'] = 'KEGG'
        backward.metadata['reversible'] = True
        backward.metadata['direction'] = 'reverse'
        if ec_numbers:
            backward.metadata['ec_numbers'] = ec_numbers
        
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
