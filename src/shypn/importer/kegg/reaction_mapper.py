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
    
    # Common enzyme abbreviations (prioritized for naming)
    ENZYME_ABBREVIATIONS = {
        'EC:2.7.1.1': 'HK',      # Hexokinase
        'EC:2.7.1.11': 'PFK',    # Phosphofructokinase
        'EC:2.7.1.40': 'PK',     # Pyruvate kinase
        'EC:5.3.1.9': 'PGI',     # Phosphoglucose isomerase
        'EC:4.1.2.13': 'ALDO',   # Aldolase
        'EC:5.3.1.1': 'TPI',     # Triose phosphate isomerase
        'EC:1.2.1.12': 'GAPDH',  # Glyceraldehyde-3-phosphate dehydrogenase
        'EC:2.7.2.3': 'PGK',     # Phosphoglycerate kinase
        'EC:5.4.2.11': 'PGM',    # Phosphoglycerate mutase
        'EC:4.2.1.11': 'ENO',    # Enolase
        'EC:1.1.1.1': 'ADH',     # Alcohol dehydrogenase
        'EC:1.1.1.27': 'LDH',    # Lactate dehydrogenase
        'EC:2.7.1.2': 'GK',      # Glucokinase
    }
    
    def __init__(self):
        """Initialize reaction mapper."""
        self.transition_counter = 1
        self.ec_cache: Dict[str, List[str]] = {}  # Cache for pre-fetched EC numbers
        self.id_manager = None  # Will be set during conversion
    
    def _get_biological_name(self, reaction: KEGGReaction, ec_numbers: List[str] = None, 
                             transition_id: str = None) -> str:
        """Extract biological name from KEGG reaction.
        
        CRITICAL: Names must be biological identifiers (enzymes), NOT database codes!
        Names represent actual biochemical processes (hexokinase, not R00001).
        
        Priority order (AGGRESSIVE - biological names only):
        1. Enzyme abbreviation from EC number (HK, PFK, PK, etc.)
        2. Enzyme name from reaction graphics (Hexokinase, Pyruvate kinase, etc.)
        3. EC number formatted (EC_2.7.1.1) - still biological, better than codes
        4. Extract enzyme name from reaction equation/definition
        5. Use transition ID (T1, T2) as fallback - users can reference in formulas
        6. NEVER use KEGG reaction codes (R#####) - they're database refs, not biology
        
        Note: We AGGRESSIVELY avoid R##### codes because:
        - R00001 is a database reference, not a biological entity
        - Names must represent actual enzymes/processes (hexokinase, phosphorylation)
        - Formulas should use biological identifiers or system IDs, never DB codes
        
        Args:
            reaction: KEGG reaction
            ec_numbers: Optional list of EC numbers for the reaction
            transition_id: System-generated transition ID (e.g., "T1", "T2")
            
        Returns:
            Biological name (enzyme/process name) or transition ID, NEVER R##### codes
        """
        # 1. Check for common enzyme abbreviation from EC number (BEST)
        if ec_numbers:
            for ec in ec_numbers:
                # Normalize EC format
                ec_key = ec if ec.startswith('EC:') else f'EC:{ec}'
                if ec_key in self.ENZYME_ABBREVIATIONS:
                    return self.ENZYME_ABBREVIATIONS[ec_key]
        
        # 2. Try enzyme name from reaction graphics (ACTUAL ENZYME NAME)
        if hasattr(reaction, 'graphics') and reaction.graphics and hasattr(reaction.graphics, 'name'):
            enzyme_name = str(reaction.graphics.name).strip()
            if enzyme_name and enzyme_name.lower() not in ('undefined', 'unknown', ''):
                # Extract SHORT name (first word only, not entire EC family)
                # Example: "Hexokinase type 1" → "Hexokinase"
                # Example: "Pyruvate kinase" → "Pyruvate"
                first_word = enzyme_name.split()[0] if ' ' in enzyme_name else enzyme_name
                # Remove trailing punctuation
                first_word = first_word.rstrip(',;:()')
                # Must be actual name, not a reaction code
                if first_word and len(first_word) > 1 and not (first_word.startswith('R') and len(first_word) == 6):
                    return first_word
        
        # 3. Use EC number directly if no abbreviation found (still biological)
        # Format as short EC number without family details
        if ec_numbers and len(ec_numbers) > 0:
            # Use first EC number, formatted simply (e.g., "2.7.1.1")
            ec_clean = ec_numbers[0].replace('EC:', '').replace('EC ', '').strip()
            if ec_clean:
                # Return just the EC number for brevity
                return ec_clean
        
        # 4. Try to extract enzyme name from reaction definition/equation
        if hasattr(reaction, 'equation') and reaction.equation:
            # Sometimes enzyme name is embedded in equation
            # This is a heuristic extraction
            pass  # Could implement extraction logic here if needed
        
        # 5. Use transition ID as fallback (user can reference in formulas)
        # This is better than R##### codes because users can work with T1, T2, etc.
        if transition_id:
            return transition_id
        
        # 6. NEVER return R##### codes - they're meaningless to users
        # If we reach here, we truly have no biological name
        # Use generic placeholder that indicates unknown enzyme
        return "UnknownEnzyme"
    
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
                          options: ConversionOptions, id_manager=None) -> List[Transition]:
        """Create Transition(s) from a KEGG reaction.
        
        Args:
            reaction: KEGG reaction to convert
            pathway: Complete pathway (for context)
            options: Conversion options
            id_manager: Optional IDManager for generating unique IDs
            
        Returns:
            List of Transition objects (one for normal, two for split reversible)
        """
        # Store id_manager for use in helper methods
        if id_manager:
            self.id_manager = id_manager
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
        # Use IDManager if available, otherwise fall back to local counter
        if self.id_manager:
            transition_id = self.id_manager.generate_transition_id()
        else:
            transition_id = f"T{self.transition_counter}"
            self.transition_counter += 1
        
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
            except (ConnectionError, TimeoutError, ValueError) as e:
                logger.warning(f"Failed to fetch EC numbers for {reaction.name}: {e}")
        
        # Get biological name for the transition (pass transition_id for fallback)
        transition_name = self._get_biological_name(reaction, ec_numbers, transition_id)
        
        # For duplicate KEGG reactions (same reaction.name but different internal IDs),
        # append internal ID to make labels unique and traceable
        # This helps distinguish between multiple instances of R01175, R00631, etc.
        display_label = name
        if hasattr(reaction, 'id') and reaction.id:
            # Check if we need to add disambiguation
            # (This will be enhanced by pathway converter if duplicates detected)
            display_label = f"{name}"
        
        # Create transition with correct arguments: (x, y, id, name)
        # The reaction name becomes the label, not the system name
        transition = Transition(x, y, transition_id, transition_name, label=display_label)
        
        # Store KEGG metadata
        if not hasattr(transition, 'metadata'):
            transition.metadata = {}
        transition.metadata['kegg_reaction_id'] = reaction.id
        transition.metadata['kegg_reaction_name'] = reaction.name
        transition.metadata['source'] = 'KEGG'
        transition.metadata['data_source'] = 'kegg_import'  # For Report panel colored rendering
        transition.metadata['reversible'] = reaction.is_reversible()
        
        # Store reaction type if available
        if hasattr(reaction, 'type'):
            transition.metadata['reaction_type'] = reaction.type
        
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
            except (ConnectionError, TimeoutError, ValueError) as e:
                logger.warning(f"Failed to fetch EC numbers for {reaction.name}: {e}")
        
        # Forward transition
        if self.id_manager:
            forward_id = self.id_manager.generate_transition_id()
        else:
            forward_id = f"T{self.transition_counter}"
            self.transition_counter += 1
        
        # Get biological name for the transition (pass forward_id for fallback)
        biological_name = self._get_biological_name(reaction, ec_numbers, forward_id)
        forward_sys_name = f"{biological_name}_fwd"  # Biological name with direction
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
        if self.id_manager:
            backward_id = self.id_manager.generate_transition_id()
        else:
            backward_id = f"T{self.transition_counter}"
            self.transition_counter += 1
        backward_sys_name = f"{biological_name}_rev"  # Biological name with direction
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
