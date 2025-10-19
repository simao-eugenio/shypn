"""Standard compound to place mapping strategy."""

from shypn.netobjs import Place
from .converter_base import CompoundMapper, ConversionOptions
from .models import KEGGEntry


# Common cofactors that can be filtered out to reduce clutter
COMMON_COFACTORS = {
    'C00001',  # H2O (water)
    'C00002',  # ATP
    'C00003',  # NAD+
    'C00004',  # NADH
    'C00005',  # NADPH
    'C00006',  # NADP+
    'C00008',  # ADP
    'C00009',  # Orthophosphate (Pi)
    'C00010',  # CoA
    'C00011',  # CO2
    'C00013',  # Diphosphate (PPi)
    'C00014',  # NH3 (ammonia)
    'C00015',  # UDP
    'C00016',  # FAD
    'C00017',  # Protein
    'C00020',  # AMP
    'C00035',  # GDP
    'C00044',  # GTP
    'C00059',  # Sulfate
    'C00063',  # CTP
    'C00080',  # H+ (proton)
    'C00081',  # ITP
    'C00104',  # IDP
    'C00131',  # dATP
    'C00144',  # GMP
    'C00206',  # UTP
}


class StandardCompoundMapper(CompoundMapper):
    """Standard strategy for mapping KEGG compounds to places.
    
    This mapper:
    - Filters common cofactors when include_cofactors=False
    - Applies coordinate scaling
    - Extracts clean compound names
    - Preserves KEGG metadata
    """
    
    def __init__(self):
        """Initialize compound mapper."""
        pass
    
    def should_include(self, entry: KEGGEntry, options: ConversionOptions) -> bool:
        """Determine if a compound should be included.
        
        Args:
            entry: KEGG compound entry
            options: Conversion options
            
        Returns:
            True if compound should be included, False otherwise
        """
        # Check if this is a common cofactor and filtering is enabled
        if not options.include_cofactors:
            # Extract compound ID from entry name (e.g., "cpd:C00001" -> "C00001")
            compound_id = entry.name.split(':')[-1] if ':' in entry.name else entry.name
            if compound_id in COMMON_COFACTORS:
                return False
        
        return True
    
    def create_place(self, entry: KEGGEntry, options: ConversionOptions) -> Place:
        """Create a Place from a KEGG compound entry.
        
        Args:
            entry: KEGG compound entry
            options: Conversion options
            
        Returns:
            Place object representing the compound
        """
        # Calculate position with scaling and offset
        x = entry.graphics.x * options.coordinate_scale + options.center_x
        y = entry.graphics.y * options.coordinate_scale + options.center_y
        
        # Get clean compound name from graphics
        label = self.get_compound_name(entry)
        
        # Create place ID and name
        place_id = f"P{entry.id}"
        place_name = f"P{entry.id}"  # Name should match ID for KEGG compounds
        
        # Determine initial marking
        marking = options.initial_tokens if options.add_initial_marking else 0
        
        # Create place with correct arguments: (x, y, id, name, radius, label)
        place = Place(x, y, place_id, place_name, label=label)
        
        # Set initial marking
        place.tokens = marking
        place.initial_marking = marking
        
        # Store KEGG metadata for traceability
        if not hasattr(place, 'metadata'):
            place.metadata = {}
        place.metadata['kegg_id'] = entry.name
        place.metadata['kegg_entry_id'] = entry.id
        place.metadata['source'] = 'KEGG'
        
        # Add compound type if available
        if hasattr(entry, 'type'):
            place.metadata['kegg_type'] = entry.type
        
        return place
    
    def get_compound_name(self, entry: KEGGEntry) -> str:
        """Extract a clean compound name from entry.
        
        Args:
            entry: KEGG compound entry
            
        Returns:
            Clean compound name string
        """
        # Priority: graphics name > entry name > entry ID
        if entry.graphics and entry.graphics.name:
            name = entry.graphics.name
            # Clean up the name
            # Remove line breaks
            name = name.replace('\n', ' ')
            # Remove excess whitespace
            name = ' '.join(name.split())
            return name
        
        # Fallback to entry name
        if entry.name:
            # Extract compound ID (e.g., "cpd:C00001" -> "C00001")
            if ':' in entry.name:
                return entry.name.split(':')[-1]
            return entry.name
        
        # Last resort: use entry ID
        return f"Compound_{entry.id}"
