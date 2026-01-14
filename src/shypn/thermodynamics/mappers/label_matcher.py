"""Label-based compound mapping strategy.

This mapper extracts compound identifiers from place labels using:
1. Direct ID extraction (C00002, CHEBI:15422)
2. Fuzzy name matching (ATP → C00002)
"""

from typing import Dict, List, Optional, Tuple
import re
from .base_mapper import CompoundMapperBase


class LabelBasedMapper(CompoundMapperBase):
    """Maps compounds by parsing place names.
    
    Strategy:
    1. Use place.name (object identifier, not display label)
    2. Try direct ID extraction (C00002, CHEBI:12345)
    3. Fall back to fuzzy name matching (ATP → C00002)
    4. Return confidence based on match type
    
    Note: place.label is NOT used because it's inconsistent display text,
    not a reliable identifier for compound mapping.
    
    Confidence Levels:
        0.95: Direct ID extraction
        0.60: Fuzzy name match
        0.00: No match
    """
    
    def __init__(self):
        """Initialize label-based mapper with common compound database."""
        self._load_common_names()
        self._confidence_cache: Dict[str, float] = {}
    
    def _load_common_names(self):
        """Load common compound name → KEGG ID mappings."""
        self.common_mappings = {
            # Energy carriers
            "ATP": "C00002",
            "ADENOSINE TRIPHOSPHATE": "C00002",
            "ADP": "C00008",
            "ADENOSINE DIPHOSPHATE": "C00008",
            "AMP": "C00020",
            "ADENOSINE MONOPHOSPHATE": "C00020",
            "GTP": "C00044",
            "GUANOSINE TRIPHOSPHATE": "C00044",
            "GDP": "C00035",
            "GUANOSINE DIPHOSPHATE": "C00035",
            "CTP": "C00063",
            "CYTIDINE TRIPHOSPHATE": "C00063",
            "UTP": "C00075",
            "URIDINE TRIPHOSPHATE": "C00075",
            
            # Redox carriers
            "NADH": "C00004",
            "NAD+": "C00003",
            "NADPH": "C00005",
            "NADP+": "C00006",
            "FAD": "C00016",
            "FADH2": "C01352",
            
            # Central carbon metabolism
            "GLUCOSE": "C00031",
            "D-GLUCOSE": "C00031",
            "GLUCOSE-6-PHOSPHATE": "C00092",
            "GLUCOSE-6P": "C00092",
            "G6P": "C00092",
            "FRUCTOSE-6-PHOSPHATE": "C00085",
            "FRUCTOSE-6P": "C00085",
            "F6P": "C00085",
            "FRUCTOSE-1,6-BISPHOSPHATE": "C00354",
            "FRUCTOSE-1,6-BP": "C00354",
            "F1,6BP": "C00354",
            "PYRUVATE": "C00022",
            "ACETYL-COA": "C00024",
            "ACETYL COENZYME A": "C00024",
            "CITRATE": "C00158",
            
            # Amino acids
            "GLYCINE": "C00037",
            "ALANINE": "C00041",
            "L-ALANINE": "C00041",
            "SERINE": "C00065",
            "L-SERINE": "C00065",
            "THREONINE": "C00188",
            "L-THREONINE": "C00188",
            "CYSTEINE": "C00097",
            "L-CYSTEINE": "C00097",
            "GLUTAMATE": "C00025",
            "L-GLUTAMATE": "C00025",
            "GLUTAMIC ACID": "C00025",
            "GLUTAMINE": "C00064",
            "L-GLUTAMINE": "C00064",
            
            # Small molecules
            "WATER": "C00001",
            "H2O": "C00001",
            "PHOSPHATE": "C00009",
            "ORTHOPHOSPHATE": "C00009",
            "PI": "C00009",
            "PYROPHOSPHATE": "C00013",
            "PPI": "C00013",
            "CO2": "C00011",
            "CARBON DIOXIDE": "C00011",
            "AMMONIA": "C00014",
            "NH3": "C00014",
            "OXYGEN": "C00007",
            "O2": "C00007",
            "HYDROGEN": "C00282",
            "H2": "C00282",
        }
        
        # Create lowercase lookup for case-insensitive matching
        self._lowercase_map = {
            k.lower(): v for k, v in self.common_mappings.items()
        }
    
    def map_places(self, places: List) -> Dict[str, str]:
        """Extract compound IDs from place labels.
        
        Args:
            places: List of Place objects with .id and .label attributes
            
        Returns:
            Dictionary mapping place_id → compound_id
        """
        mappings = {}
        self._confidence_cache = {}  # Reset cache
        
        for place in places:
            compound_id, confidence = self._map_single_place(place)
            if compound_id:
                mappings[place.id] = compound_id
                self._confidence_cache[place.id] = confidence
        
        return mappings
    
    def get_confidence(self, place_id: str) -> float:
        """Return cached confidence from last mapping.
        
        Args:
            place_id: Place identifier
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        return self._confidence_cache.get(place_id, 0.0)
    
    def _map_single_place(self, place) -> Tuple[Optional[str], float]:
        """Map single place, return (compound_id, confidence).
        
        Args:
            place: Place object with .name attribute
            
        Returns:
            Tuple of (compound_id or None, confidence score)
        """
        # Use place.name only (NOT place.label)
        if not hasattr(place, 'name') or not place.name:
            return None, 0.0
        
        name_text = place.name.strip()
        if not name_text:
            return None, 0.0
        
        # Strategy 1: Try direct ID extraction
        compound_id = self._extract_id(name_text)
        if compound_id:
            return compound_id, 0.95  # High confidence
        
        # Strategy 2: Try fuzzy matching
        compound_id = self._fuzzy_match(name_text)
        if compound_id:
            return compound_id, 0.60  # Medium confidence
        
        return None, 0.0
    
    def _extract_id(self, name_text: str) -> Optional[str]:
        """Extract compound ID from place name.
        
        Patterns:
            - C##### (KEGG)
            - CHEBI:##### (ChEBI)
            - Parentheses: "ATP (C00002)"
            - Brackets: "ATP [C00002]"
        
        Args:
            name_text: Place name text
            
        Returns:
            Extracted compound ID or None
        """
        # Try KEGG C-number
        kegg_match = re.search(r'\b(C\d{5})\b', name_text, re.IGNORECASE)
        if kegg_match:
            return kegg_match.group(1).upper()
        
        # Try ChEBI identifier
        chebi_match = re.search(r'\b(CHEBI:\d+)\b', name_text, re.IGNORECASE)
        if chebi_match:
            return self.normalize_compound_id(chebi_match.group(1))
        
        return None
    
    def _fuzzy_match(self, name_text: str) -> Optional[str]:
        """Match place name against common compound names.
        
        Args:
            name_text: Place name text
            
        Returns:
            Matched KEGG compound ID or None
        """
        # Clean name for matching
        clean_name = name_text.upper().strip()
        
        # Remove common prefixes/suffixes
        clean_name = re.sub(r'^(D-|L-)', '', clean_name)
        clean_name = re.sub(r'\s*\(.*\)\s*$', '', clean_name)  # Remove parentheses
        clean_name = re.sub(r'\s*\[.*\]\s*$', '', clean_name)  # Remove brackets
        clean_name = clean_name.strip()
        
        # Exact match (case-insensitive)
        if clean_name in self.common_mappings:
            return self.common_mappings[clean_name]
        
        # Try lowercase lookup
        if clean_name.lower() in self._lowercase_map:
            return self._lowercase_map[clean_name.lower()]
        
        # Partial match (contains keyword)
        for name, compound_id in self.common_mappings.items():
            if name in clean_name or clean_name in name:
                return compound_id
        
        return None
