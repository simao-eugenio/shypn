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
    
    # Common metabolite abbreviations (prioritized for naming)
    COMMON_ABBREVIATIONS = {
        'C00002': 'ATP',
        'C00008': 'ADP',
        'C00020': 'AMP',
        'C00001': 'H2O',
        'C00003': 'NAD+',
        'C00004': 'NADH',
        'C00005': 'NADPH',
        'C00006': 'NADP+',
        'C00009': 'Pi',
        'C00010': 'CoA',
        'C00013': 'PPi',
        'C00014': 'NH3',
        'C00015': 'UDP',
        'C00016': 'FAD',
        'C00024': 'Acetyl-CoA',
        'C00035': 'GDP',
        'C00044': 'GTP',
        'C00055': 'CTP',
        'C00063': 'CMP',
        'C00075': 'UTP',
        'C00080': 'H+',
        'C00081': 'ITP',
        'C00104': 'IDP',
        'C00131': 'dATP',
        'C00144': 'GMP',
        'C00206': 'UTP',
    }
    
    def __init__(self):
        """Initialize compound mapper."""
        pass
    
    def _get_biological_name(self, entry: KEGGEntry) -> str:
        """Extract biological name from KEGG entry.
        
        CRITICAL: Names must be biological identifiers, NOT database codes!
        Names represent actual biochemical entities (glucose, ATP, pyruvate).
        
        Priority order (AGGRESSIVE - biological names only):
        1. Common abbreviation from KEGG code (ATP, ADP, NAD+, etc.)
        2. Graphics display name - actual compound name (Glucose, Pyruvate, etc.)
        3. Entry name cleaned (if not a code)
        4. KEGG compound ID ONLY as absolute last resort
        
        Args:
            entry: KEGG compound entry
            
        Returns:
            Biological name for the compound (metabolite name, NOT database code)
        """
        # Extract KEGG compound ID from entry.name (e.g., "cpd:C00002" -> "C00002")
        compound_id = entry.name.split(':')[-1].strip() if ':' in entry.name else entry.name.strip()
        
        # 1. Check for common abbreviation (ATP, not C00002)
        if compound_id in self.COMMON_ABBREVIATIONS:
            return self.COMMON_ABBREVIATIONS[compound_id]
        
        # 2. Try graphics display name (actual compound name - HIGHEST PRIORITY)
        if entry.graphics and entry.graphics.name:
            display_name = entry.graphics.name.strip()
            if display_name and display_name.lower() not in ('undefined', 'unknown', ''):
                # Take first word if multi-word name
                first_word = display_name.split()[0] if ' ' in display_name else display_name
                # Remove common prefixes/suffixes
                first_word = first_word.rstrip(',;:')
                # Must be actual name, not a code
                if first_word and len(first_word) > 1 and not (first_word.startswith('C') and first_word[1:].isdigit()):
                    return first_word
        
        # 3. Try entry name if it's not a compound code
        if hasattr(entry, 'data') and entry.data:
            # Entry.data might contain actual names
            for line in str(entry.data).split('\n')[:3]:  # Check first few lines
                if 'NAME' in line:
                    name_part = line.split('NAME')[-1].strip()
                    if name_part and len(name_part) > 2 and not name_part.startswith('C'):
                        # Extract first word
                        first_word = name_part.split()[0].split(';')[0].rstrip(',;:')
                        if first_word and not (first_word.startswith('C') and len(first_word) == 6):
                            return first_word
        
        # 4. LAST RESORT: Use KEGG compound ID (but this is NOT ideal)
        # This means we couldn't find the actual biological name
        if compound_id.startswith('C') and len(compound_id) == 6:
            return compound_id
        
        # 5. Final fallback
        return f"C{entry.id}"
    
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
    
    def create_place(self, entry: KEGGEntry, options: ConversionOptions, id_manager=None) -> Place:
        """Create a Place from a KEGG compound entry.
        
        Args:
            entry: KEGG compound entry
            options: Conversion options
            id_manager: Optional IDManager for generating unique IDs
            
        Returns:
            Place object representing the compound
        """
        # Calculate position with scaling and offset
        x = entry.graphics.x * options.coordinate_scale + options.center_x
        y = entry.graphics.y * options.coordinate_scale + options.center_y
        
        # Get clean compound name from graphics
        label = self.get_compound_name(entry)
        
        # Create place ID using IDManager if available
        if id_manager:
            place_id = id_manager.generate_place_id()
        else:
            # Fallback to old behavior for backwards compatibility
            place_id = f"P{entry.id}"
        
        # Get biological name for the place
        place_name = self._get_biological_name(entry)
        
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
        place.metadata['data_source'] = 'kegg_import'  # For Report panel colored rendering
        
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
