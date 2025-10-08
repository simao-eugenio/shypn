"""Standard compound to place mapping strategy."""

from typing import Set
from shypn.netobjs import Place
from .converter_base import CompoundMapper, ConversionOptions
from .models import KEGGEntry


# Common cofactors that appear in many reactions
COMMON_COFACTORS = {
    'C00002',  # ATP
    'C00008',  # ADP
    'C00020',  # AMP
    'C00003',  # NAD+
    'C00004',  # NADH
    'C00006',  # NADP+
    'C00005',  # NADPH
    'C00080',  # H+
    'C00001',  # H2O
    'C00007',  # Oxygen
    'C00011',  # CO2
    'C00013',  # Diphosphate
    'C00009',  # Orthophosphate
}


class StandardCompoundMapper(CompoundMapper):
    """Standard strategy for mapping KEGG compounds to Petri net places.
    
    This mapper:
    - Converts each compound to a place
    - Optionally filters out common cofactors
    - Uses KEGG coordinates scaled to world coordinates
    - Extracts clean compound names for labels
    """
    
    def __init__(self, excluded_compounds: Set[str] = None):
        """Initialize compound mapper.
        
        Args:
            excluded_compounds: Set of compound IDs to exclude (e.g., cofactors)
        """
        self.excluded_compounds = excluded_compounds or set()
    
    def should_include(self, entry: KEGGEntry, options: ConversionOptions) -> bool:
        """Determine if compound should be included.
        
        Filters out:
        - Common cofactors (if include_cofactors is False)
        - Manually excluded compounds
        
        Args:
            entry: KEGG compound entry
            options: Conversion options
            
        Returns:
            True if compound should be included
        """
        # Extract compound ID from name (e.g., "cpd:C00031" -> "C00031")
        compound_id = entry.name.replace('cpd:', '').strip()
        
        # Check if manually excluded
        if compound_id in self.excluded_compounds:
            return False
        
        # Check if common cofactor
        if not options.include_cofactors and compound_id in COMMON_COFACTORS:
            return False
        
        return True
    
    def create_place(self, entry: KEGGEntry, options: ConversionOptions) -> Place:
        """Create a Place from compound entry.
        
        Args:
            entry: KEGG compound entry
            options: Conversion options
            
        Returns:
            Place object with:
            - Position scaled from KEGG coordinates
            - Label from compound name
            - ID from entry ID
            - Optional initial marking
        """
        # Calculate position
        x = entry.graphics.x * options.coordinate_scale + options.center_x
        y = entry.graphics.y * options.coordinate_scale + options.center_y
        
        # Get clean name
        label = self.get_compound_name(entry)
        
        # Create place ID (P prefix + entry ID)
        place_id = f"P{entry.id}"
        
        # Determine initial marking
        marking = options.initial_tokens if options.add_initial_marking else 0
        
        # Create place
        place = Place(x, y, place_id, marking)
        place.label = label
        
        # Store KEGG metadata
        if not hasattr(place, 'metadata'):
            place.metadata = {}
        place.metadata['kegg_id'] = entry.name
        place.metadata['kegg_entry_id'] = entry.id
        place.metadata['source'] = 'KEGG'
        
        return place
