"""Compound name ↔ ID bidirectional mapping.

Provides lookup between human-readable compound names and database identifiers
(KEGG, BiGG, ChEBI). Enables auto-suggestion in property dialogs.
"""

from typing import Optional, List, Tuple, Dict


class CompoundMapper:
    """Bidirectional mapper between compound names and database IDs.
    
    Supports:
    - Common metabolite names → KEGG/BiGG IDs
    - Fuzzy matching for partial names
    - Reverse lookup: ID → standard name
    
    Examples:
        >>> mapper = CompoundMapper()
        >>> mapper.name_to_id("ATP")
        'C00002'
        >>> mapper.id_to_name("C00002")
        'ATP'
        >>> mapper.suggest_names("glu")
        [('Glucose', 'C00031'), ('Glutamate', 'C00025'), ('Glutamine', 'C00064')]
    """
    
    # Common metabolites (KEGG compound IDs)
    # Format: canonical_name → KEGG_ID
    _NAME_TO_ID = {
        # Energy metabolites
        'ATP': 'C00002',
        'ADP': 'C00008',
        'AMP': 'C00020',
        'GTP': 'C00044',
        'GDP': 'C00035',
        'GMP': 'C00144',
        'CTP': 'C00063',
        'CDP': 'C00112',
        'CMP': 'C00055',
        'UTP': 'C00075',
        'UDP': 'C00015',
        'UMP': 'C00105',
        
        # Cofactors
        'NAD+': 'C00003',
        'NAD': 'C00003',
        'NADH': 'C00004',
        'NADP+': 'C00006',
        'NADP': 'C00006',
        'NADPH': 'C00005',
        'FAD': 'C00016',
        'FADH2': 'C01352',
        'CoA': 'C00010',
        'Acetyl-CoA': 'C00024',
        
        # Sugars
        'Glucose': 'C00031',
        'D-Glucose': 'C00031',
        'Glucose-6-phosphate': 'C00092',
        'G6P': 'C00092',
        'Fructose-6-phosphate': 'C00085',
        'F6P': 'C00085',
        'Fructose-1,6-bisphosphate': 'C00354',
        'FBP': 'C00354',
        'Glyceraldehyde-3-phosphate': 'C00118',
        'G3P': 'C00118',
        'Pyruvate': 'C00022',
        'Lactate': 'C00186',
        'L-Lactate': 'C00186',
        
        # TCA cycle
        'Citrate': 'C00158',
        'Isocitrate': 'C00311',
        'α-Ketoglutarate': 'C00026',
        'Succinate': 'C00042',
        'Fumarate': 'C00122',
        'Malate': 'C00149',
        'Oxaloacetate': 'C00036',
        
        # Amino acids
        'Glutamate': 'C00025',
        'L-Glutamate': 'C00025',
        'Glutamine': 'C00064',
        'L-Glutamine': 'C00064',
        'Aspartate': 'C00049',
        'L-Aspartate': 'C00049',
        'Alanine': 'C00041',
        'L-Alanine': 'C00041',
        'Glycine': 'C00037',
        'Serine': 'C00065',
        'L-Serine': 'C00065',
        
        # Other metabolites
        'Phosphate': 'C00009',
        'Pi': 'C00009',
        'PPi': 'C00013',
        'Pyrophosphate': 'C00013',
        'H2O': 'C00001',
        'Water': 'C00001',
        'O2': 'C00007',
        'Oxygen': 'C00007',
        'CO2': 'C00011',
        'Ammonia': 'C00014',
        'NH3': 'C00014',
    }
    
    # Reverse mapping: ID → canonical name
    _ID_TO_NAME = {v: k for k, v in _NAME_TO_ID.items()}
    
    # Keep only the first (canonical) name for each ID
    _CANONICAL_ID_TO_NAME = {}
    for name, compound_id in _NAME_TO_ID.items():
        if compound_id not in _CANONICAL_ID_TO_NAME:
            _CANONICAL_ID_TO_NAME[compound_id] = name
    
    # Alternative names (aliases) for fuzzy matching
    _ALIASES = {
        'adenosine triphosphate': 'ATP',
        'adenosine diphosphate': 'ADP',
        'adenosine monophosphate': 'AMP',
        'nicotinamide adenine dinucleotide': 'NAD+',
        'nadh': 'NADH',
        'nadph': 'NADPH',
        'coenzyme a': 'CoA',
        'dextrose': 'Glucose',
        'alpha-ketoglutarate': 'α-Ketoglutarate',
        '2-oxoglutarate': 'α-Ketoglutarate',
        'lactic acid': 'Lactate',
    }
    
    @classmethod
    def name_to_id(cls, name: str) -> Optional[str]:
        """Convert compound name to KEGG ID.
        
        Args:
            name: Compound name (case-insensitive)
        
        Returns:
            KEGG compound ID (e.g., "C00002") or None if not found
        
        Examples:
            >>> CompoundMapper.name_to_id("ATP")
            'C00002'
            >>> CompoundMapper.name_to_id("atp")
            'C00002'
            >>> CompoundMapper.name_to_id("adenosine triphosphate")
            'C00002'
        """
        if not name:
            return None
        
        # Try exact match (case-insensitive)
        name_normalized = name.strip()
        for known_name, compound_id in cls._NAME_TO_ID.items():
            if known_name.lower() == name_normalized.lower():
                return compound_id
        
        # Try alias match
        name_lower = name_normalized.lower()
        if name_lower in cls._ALIASES:
            canonical_name = cls._ALIASES[name_lower]
            return cls._NAME_TO_ID.get(canonical_name)
        
        return None
    
    @classmethod
    def id_to_name(cls, compound_id: str) -> Optional[str]:
        """Convert KEGG ID to canonical compound name.
        
        Args:
            compound_id: KEGG compound ID (e.g., "C00002")
        
        Returns:
            Canonical compound name or None if not found
        
        Examples:
            >>> CompoundMapper.id_to_name("C00002")
            'ATP'
            >>> CompoundMapper.id_to_name("C00031")
            'Glucose'
        """
        if not compound_id:
            return None
        
        return cls._CANONICAL_ID_TO_NAME.get(compound_id.strip())
    
    @classmethod
    def suggest_names(cls, partial: str, max_results: int = 10) -> List[Tuple[str, str]]:
        """Suggest compound names matching partial input.
        
        Args:
            partial: Partial name to match (case-insensitive)
            max_results: Maximum suggestions to return
        
        Returns:
            List of (name, compound_id) tuples
        
        Examples:
            >>> CompoundMapper.suggest_names("glu")
            [('Glucose', 'C00031'), ('Glutamate', 'C00025'), ...]
        """
        if not partial:
            return []
        
        partial_lower = partial.lower()
        matches = []
        
        # Match against canonical names
        for name, compound_id in cls._NAME_TO_ID.items():
            if partial_lower in name.lower():
                matches.append((name, compound_id))
        
        # Sort by match position (earlier = better) and name length (shorter = better)
        def sort_key(item):
            name, _ = item
            name_lower = name.lower()
            position = name_lower.index(partial_lower) if partial_lower in name_lower else 999
            return (position, len(name), name_lower)
        
        matches.sort(key=sort_key)
        return matches[:max_results]
    
    @classmethod
    def suggest_ids(cls, partial: str, max_results: int = 10) -> List[Tuple[str, str]]:
        """Suggest compound IDs matching partial input.
        
        Args:
            partial: Partial ID to match (e.g., "C000")
            max_results: Maximum suggestions to return
        
        Returns:
            List of (compound_id, name) tuples
        
        Examples:
            >>> CompoundMapper.suggest_ids("C0000")
            [('C00002', 'ATP'), ('C00003', 'NAD+'), ...]
        """
        if not partial:
            return []
        
        partial_upper = partial.upper()
        matches = []
        
        for compound_id, name in cls._CANONICAL_ID_TO_NAME.items():
            if partial_upper in compound_id:
                matches.append((compound_id, name))
        
        # Sort by ID
        matches.sort(key=lambda x: x[0])
        return matches[:max_results]
    
    @classmethod
    def is_valid_id(cls, compound_id: str) -> bool:
        """Check if compound ID is known.
        
        Args:
            compound_id: KEGG compound ID
        
        Returns:
            True if ID is in database
        """
        return compound_id in cls._CANONICAL_ID_TO_NAME
    
    @classmethod
    def get_all_names(cls) -> List[str]:
        """Get list of all known compound names.
        
        Returns:
            Sorted list of canonical names
        """
        return sorted(set(cls._NAME_TO_ID.keys()))
    
    @classmethod
    def get_all_ids(cls) -> List[str]:
        """Get list of all known compound IDs.
        
        Returns:
            Sorted list of KEGG IDs
        """
        return sorted(cls._CANONICAL_ID_TO_NAME.keys())
    
    @classmethod
    def add_mapping(cls, name: str, compound_id: str):
        """Add custom compound mapping (runtime only).
        
        Args:
            name: Compound name
            compound_id: KEGG or custom ID
        
        Note:
            This adds to in-memory mapping only, not persisted.
        """
        cls._NAME_TO_ID[name] = compound_id
        if compound_id not in cls._CANONICAL_ID_TO_NAME:
            cls._CANONICAL_ID_TO_NAME[compound_id] = name


# Convenience functions
def name_to_id(name: str) -> Optional[str]:
    """Convert compound name to ID (module-level convenience)."""
    return CompoundMapper.name_to_id(name)


def id_to_name(compound_id: str) -> Optional[str]:
    """Convert compound ID to name (module-level convenience)."""
    return CompoundMapper.id_to_name(compound_id)
