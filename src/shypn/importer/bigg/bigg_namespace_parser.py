"""BiGG namespace parser for metabolite and reaction IDs.

Parses BiGG-specific ID format to extract metabolite names,
compartment information, and reaction properties.
"""

from typing import Tuple, Optional


class BiGGNamespaceParser:
    """Parser for BiGG database ID format.
    
    BiGG uses a specific naming convention for metabolites and reactions:
    - Metabolites: M_<name>_<compartment> (e.g., M_atp_c)
    - Reactions: R_<name>[r] (e.g., R_ATPS4r, 'r' suffix for reversible)
    
    Compartment codes:
        c: cytosol
        e: extracellular
        p: periplasm
        m: mitochondrion
        n: nucleus
        r: endoplasmic reticulum
        x: peroxisome/glyoxysome
        g: Golgi apparatus
        v: vacuole
        l: lysosome
    """
    
    # Compartment code to full name mapping
    COMPARTMENT_CODES = {
        'c': 'cytosol',
        'e': 'extracellular',
        'p': 'periplasm',
        'm': 'mitochondrion',
        'n': 'nucleus',
        'r': 'endoplasmic_reticulum',
        'x': 'peroxisome',
        'g': 'golgi',
        'v': 'vacuole',
        'l': 'lysosome',
    }
    
    @staticmethod
    def parse_species_id(species_id: str) -> Tuple[str, Optional[str]]:
        """Parse BiGG species (metabolite) ID.
        
        Extracts the metabolite name and compartment code from
        BiGG metabolite IDs.
        
        Args:
            species_id: BiGG species ID (e.g., 'M_atp_c', 'M_glc_D_e')
            
        Returns:
            Tuple of (metabolite_name, compartment_code)
            Example: 'M_atp_c' -> ('atp', 'c')
                    'M_glc_D_e' -> ('glc_D', 'e')
                    'M_h2o' -> ('h2o', None)
        """
        # Remove M_ prefix if present
        if species_id.startswith('M_'):
            species_id = species_id[2:]
        
        # Split by underscore from the right to get compartment
        parts = species_id.rsplit('_', 1)
        
        if len(parts) == 2:
            metabolite, compartment = parts
            # Validate compartment code (should be single letter)
            if len(compartment) == 1 and compartment in BiGGNamespaceParser.COMPARTMENT_CODES:
                return (metabolite, compartment)
        
        # No valid compartment found
        return (species_id, None)
    
    @staticmethod
    def parse_reaction_id(reaction_id: str) -> Tuple[str, bool]:
        """Parse BiGG reaction ID.
        
        Extracts the reaction name and reversibility flag.
        
        Args:
            reaction_id: BiGG reaction ID (e.g., 'R_ATPS4r', 'R_PFK')
            
        Returns:
            Tuple of (reaction_name, is_reversible)
            Example: 'R_ATPS4r' -> ('ATPS4', True)
                    'R_PFK' -> ('PFK', False)
        """
        # Remove R_ prefix if present
        if reaction_id.startswith('R_'):
            reaction_id = reaction_id[2:]
        
        # Check for 'r' suffix indicating reversibility
        if reaction_id.endswith('r'):
            return (reaction_id[:-1], True)
        
        return (reaction_id, False)
    
    @staticmethod
    def get_compartment_name(code: str) -> str:
        """Get full compartment name from code.
        
        Args:
            code: Single-letter compartment code
            
        Returns:
            Full compartment name, or the code itself if not recognized
        """
        return BiGGNamespaceParser.COMPARTMENT_CODES.get(code, code)
    
    @staticmethod
    def format_metabolite_display_name(metabolite_id: str, compartment: Optional[str] = None) -> str:
        """Format metabolite ID for display.
        
        Args:
            metabolite_id: Metabolite name (e.g., 'atp')
            compartment: Compartment code (e.g., 'c')
            
        Returns:
            Formatted display name
            Example: ('atp', 'c') -> 'ATP [cytosol]'
                    ('nad', 'm') -> 'NAD [mitochondrion]'
        """
        # Convert to uppercase for common metabolites
        display_name = metabolite_id.upper()
        
        if compartment:
            compartment_name = BiGGNamespaceParser.get_compartment_name(compartment)
            return f"{display_name} [{compartment_name}]"
        
        return display_name
    
    @classmethod
    def is_energy_metabolite(cls, metabolite_id: str) -> bool:
        """Check if metabolite is an energy carrier.
        
        Identifies common energy metabolites like ATP, NAD, CoA, etc.
        
        Args:
            metabolite_id: Metabolite name (without compartment)
            
        Returns:
            True if metabolite is an energy carrier
        """
        # Common energy metabolites (lowercase for comparison)
        energy_metabolites = {
            # Adenosine phosphates
            'atp', 'adp', 'amp',
            # Guanosine phosphates
            'gtp', 'gdp', 'gmp',
            # Other nucleotides
            'ctp', 'cdp', 'cmp',
            'utp', 'udp', 'ump',
            # NAD cofactors
            'nad', 'nadh', 'nadp', 'nadph',
            # Flavin cofactors
            'fad', 'fadh2', 'fmn', 'fmnh2',
            # Coenzyme A
            'coa', 'accoa', 'succoa',
            # Phosphates
            'pi', 'ppi',
            # Other cofactors
            'h', 'h2o',  # Protons and water (ubiquitous)
        }
        
        return metabolite_id.lower() in energy_metabolites
