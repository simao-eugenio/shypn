"""Standard compound to place mapping strategy."""

from shypn.netobjs import Place
from shypn.netobjs.signal_type import SignalType
from .converter_base import CompoundMapper, ConversionOptions
from .models import KEGGEntry

# Import CompoundResolver for cross-reference database lookups
try:
    from shypn.thermodynamics.compound_resolver import CompoundResolver
    _resolver = CompoundResolver()
except ImportError:
    _resolver = None


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

# Energy metabolites that should be marked as signal places (Ψₑ)
# These are universal currency metabolites that couple multiple pathways
KEY_ENERGY_COFACTORS = {
    'C00002',  # ATP - primary energy currency
    'C00008',  # ADP - energy currency
    'C00020',  # AMP - energy currency
    'C00003',  # NAD+ - redox currency
    'C00004',  # NADH - redox currency
    'C00006',  # NADP+ - redox currency
    'C00005',  # NADPH - redox currency
    'C00016',  # FAD - redox currency
    'C00010',  # CoA - acyl group carrier
    'C00024',  # Acetyl-CoA - central metabolite
    'C00044',  # GTP - energy/signaling
    'C00035',  # GDP - energy currency
    'C00063',  # CTP - nucleotide synthesis
    'C00009',  # Pi - phosphate group donor
    'C00013',  # PPi - energy coupling
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
        
        Priority order (ENHANCED with cross-reference database):
        1. Cross-reference database lookup (most comprehensive)
        2. Common abbreviation from KEGG code (ATP, ADP, NAD+, etc.)
        3. Graphics display name - actual compound name (Glucose, Pyruvate, etc.)
        4. Entry name cleaned (if not a code)
        5. KEGG compound ID ONLY as absolute last resort
        
        Args:
            entry: KEGG compound entry
            
        Returns:
            Biological name for the compound (metabolite name, NOT database code)
        """
        # Extract KEGG compound ID from entry.name (e.g., "cpd:C00002" -> "C00002")
        compound_id = entry.name.split(':')[-1].strip() if ':' in entry.name else entry.name.strip()
        
        # 1. NEW: Try cross-reference database first (most comprehensive)
        if _resolver is not None:
            try:
                identity = _resolver.resolve(compound_id)
                if identity and identity.names:
                    # Use primary name (first in list)
                    name = identity.primary_name
                    # Prefer shorter names if available
                    if len(identity.names) > 1:
                        # Find shortest non-empty name
                        short_names = [n for n in identity.names if n and len(n) <= 20]
                        if short_names:
                            name = min(short_names, key=len)
                    return name
            except (KeyError, AttributeError, IndexError) as e:
                self.logger.debug(f"Failed to get compound name from identity service for {compound_id}: {e}")
        
        # 2. Check for common abbreviation (ATP, not C00002)
        if compound_id in self.COMMON_ABBREVIATIONS:
            return self.COMMON_ABBREVIATIONS[compound_id]
        
        # 3. Try graphics display name (actual compound name)
        if entry.graphics and entry.graphics.name:
            display_name = entry.graphics.name.strip()
            # Skip invalid placeholders: undefined, unknown, empty, ellipsis, asterisk
            invalid_names = ('undefined', 'unknown', '', '...', '*', '.', '..', 'n/a', 'na', 'null')
            if display_name and display_name.lower() not in invalid_names:
                # IMPROVED: More aggressive name extraction
                # Handle multi-word names better (e.g., "D-Glucose 6-phosphate")
                # Take full name if reasonable length, otherwise first word
                if len(display_name) <= 25:
                    # Use full name if short enough
                    clean_name = display_name.rstrip(',;:')
                    if clean_name and len(clean_name) >= 3:
                        # Check if it's not a KEGG code (C00002 format)
                        if not (clean_name.startswith('C') and len(clean_name) == 6 and clean_name[1:].isdigit()):
                            return clean_name
                else:
                    # Take first meaningful word for long names
                    first_word = display_name.split()[0]
                    first_word = first_word.rstrip(',;:')
                    if (first_word and 
                        len(first_word) >= 3 and 
                        not (first_word.startswith('C') and first_word[1:].isdigit()) and
                        not first_word.replace('.', '').replace('*', '').replace('-', '') == ''):
                        return first_word
        
        # 4. Try entry name if it's not a compound code
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
        
        # 5. LAST RESORT: Use prefixed KEGG compound ID
        # CRITICAL: Never return bare KEGG codes (C00002) as place names!
        # They look like database IDs and should not be used in rate formulas.
        # Use descriptive format: Compound_C00002 (eval-safe, descriptive)
        if compound_id.startswith('C') and len(compound_id) == 6:
            return f"Compound_{compound_id}"
        
        # 6. Final fallback
        return f"Compound_C{entry.id}"
    
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
        
        # Create place ID using IDManager if available
        if id_manager:
            place_id = id_manager.generate_place_id()
        else:
            # Fallback to old behavior for backwards compatibility
            place_id = f"P{entry.id}"
        
        # Get biological name for the place (ATP, Glucose, etc.)
        biological_name = self._get_biological_name(entry)
        
        # Determine initial marking
        marking = options.initial_tokens if options.add_initial_marking else 0
        
        # Create place with correct arguments: (x, y, id, name, radius, label)
        # Architecture:
        # - id: System ID (P1, P2, etc.) - read-only, never changes
        # - name: User-editable alias (ATP, Glucose, etc.) - used in rate formulas
        # - label: Display text (same as name typically, or description)
        place = Place(x, y, place_id, biological_name, label=biological_name)
        
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
        
        # Mark energy metabolites as signal places (Ψₑ)
        # Extract clean compound ID from entry.name (e.g., "cpd:C00002" -> "C00002")
        compound_id = entry.name.split(':')[-1] if ':' in entry.name else entry.name
        if compound_id in KEY_ENERGY_COFACTORS:
            place.is_signal_place = True
            place.signal_type = SignalType.ENERGY
            # Apply color schema immediately after setting semantic flag
            from shypn.utils.color_schema_manager import ColorSchemaManager
            ColorSchemaManager.reset_place_color(place)
            place.metadata['signal_type'] = 'Ψₑ'  # Energy signal type
            place.metadata['is_energy_signal'] = True
        
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
