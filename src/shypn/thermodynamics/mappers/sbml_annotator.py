"""SBML annotation-based compound mapping strategy.

This mapper extracts compound identifiers from SBML species annotations
stored in the document metadata.
"""

from typing import Dict, List, Optional
from .base_mapper import CompoundMapperBase


class SBMLAnnotationMapper(CompoundMapperBase):
    """Extracts mappings from SBML species annotations.
    
    This mapper reads SBML species annotations from document.metadata['sbml_species']
    which contains mappings created during SBML import.
    
    Confidence Level:
        1.0: Annotation present (highest confidence)
        0.0: No annotation
    
    Metadata Format Expected:
        document.metadata = {
            "sbml_species": {
                "species_id": {
                    "name": "ATP",
                    "kegg_id": "C00002",
                    "chebi_id": "CHEBI:15422",
                    ...
                },
                ...
            }
        }
    """
    
    def __init__(self):
        """Initialize SBML annotation mapper."""
        self._confidence_cache: Dict[str, float] = {}
        self._species_to_place: Dict[str, str] = {}  # species_id → place_id
    
    def map_places(self, places: List, document=None) -> Dict[str, str]:
        """Extract compound IDs from SBML annotations.
        
        Args:
            places: List of Place objects
            document: DocumentModel with metadata (optional)
            
        Returns:
            Dictionary mapping place_id → compound_id
        """
        mappings = {}
        self._confidence_cache = {}  # Reset cache
        
        if document is None:
            # No document provided, cannot extract annotations
            return mappings
        
        if not hasattr(document, 'metadata') or document.metadata is None:
            # No metadata available
            return mappings
        
        sbml_species = document.metadata.get('sbml_species', {})
        if not sbml_species:
            # No SBML species annotations
            return mappings
        
        # Build place name → place_id lookup (name is the reliable identifier)
        place_lookup = {}
        for place in places:
            if hasattr(place, 'name') and place.name:
                place_lookup[place.name] = place.id
        
        # Extract compound IDs from species annotations
        for species_id, species_data in sbml_species.items():
            # Try to match species to place
            place_id = self._match_species_to_place(species_id, species_data, place_lookup)
            
            if place_id:
                # Extract compound ID (prefer KEGG, fall back to ChEBI)
                compound_id = self._extract_compound_id(species_data)
                if compound_id:
                    mappings[place_id] = compound_id
                    self._confidence_cache[place_id] = 1.0  # Highest confidence
                    self._species_to_place[species_id] = place_id
        
        return mappings
    
    def get_confidence(self, place_id: str) -> float:
        """Return cached confidence from last mapping.
        
        Args:
            place_id: Place identifier
            
        Returns:
            Confidence score (1.0 for annotation-based, 0.0 otherwise)
        """
        return self._confidence_cache.get(place_id, 0.0)
    
    def _match_species_to_place(
        self, 
        species_id: str, 
        species_data: dict, 
        place_lookup: Dict[str, str]
    ) -> Optional[str]:
        """Match SBML species to a place.
        
        Args:
            species_id: SBML species identifier
            species_data: Species annotation data
            place_lookup: Dictionary mapping label/name → place_id
            
        Returns:
            Matched place_id or None
        """
        # Try direct species ID match
        if species_id in place_lookup:
            return place_lookup[species_id]
        
        # Try species name match
        species_name = species_data.get('name', '')
        if species_name and species_name in place_lookup:
            return place_lookup[species_name]
        
        # Try case-insensitive match
        species_id_lower = species_id.lower()
        species_name_lower = species_name.lower() if species_name else ''
        
        for label, place_id in place_lookup.items():
            label_lower = label.lower()
            if label_lower == species_id_lower or label_lower == species_name_lower:
                return place_id
        
        return None
    
    def _extract_compound_id(self, species_data: dict) -> Optional[str]:
        """Extract compound ID from species annotation data.
        
        Preference order:
        1. kegg_id (KEGG compound)
        2. chebi_id (ChEBI)
        3. compound_id (generic)
        
        Args:
            species_data: Species annotation dictionary
            
        Returns:
            Compound identifier or None
        """
        # Prefer KEGG IDs
        if 'kegg_id' in species_data and species_data['kegg_id']:
            compound_id = species_data['kegg_id']
            if self.validate_compound_id(compound_id):
                return compound_id
        
        # Fall back to ChEBI
        if 'chebi_id' in species_data and species_data['chebi_id']:
            compound_id = species_data['chebi_id']
            # Normalize ChEBI format
            compound_id = self.normalize_compound_id(compound_id)
            if self.validate_compound_id(compound_id):
                return compound_id
        
        # Generic compound_id field
        if 'compound_id' in species_data and species_data['compound_id']:
            compound_id = species_data['compound_id']
            if self.validate_compound_id(compound_id):
                return compound_id
        
        return None
    
    def get_species_to_place_mapping(self) -> Dict[str, str]:
        """Get SBML species ID → place ID mapping from last call.
        
        Returns:
            Dictionary mapping species_id → place_id
        """
        return self._species_to_place.copy()
