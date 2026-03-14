"""Base class for compound mapping strategies.

This module defines the abstract interface that all compound mapping
strategies must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List
import re


class CompoundMapperBase(ABC):
    """Abstract base for compound mapping strategies.
    
    Subclasses must implement:
    - map_places(): Core mapping logic
    - get_confidence(): Confidence scoring
    
    This enables multiple mapping strategies (SBML annotations,
    label parsing, database lookup) with a common interface.
    
    Confidence Scores:
        1.0: Exact match (e.g., from SBML annotation)
        0.9: High confidence (e.g., extracted KEGG ID from label)
        0.6: Medium confidence (e.g., fuzzy name match)
        0.3: Low confidence (e.g., ambiguous match)
        0.0: No match
    """
    
    @abstractmethod
    def map_places(self, places: List) -> Dict[str, str]:
        """Map places to compound IDs.
        
        Args:
            places: List of Place objects
            
        Returns:
            Dictionary mapping place_id → compound_id
            Example: {"P001": "C00002", "P002": "CHEBI:15422"}
        """
        pass
    
    @abstractmethod
    def get_confidence(self, place_id: str) -> float:
        """Get confidence score for a mapping.
        
        Args:
            place_id: Place identifier
            
        Returns:
            Confidence score between 0.0 (uncertain) and 1.0 (certain)
        """
        pass
    
    def validate_compound_id(self, compound_id: str) -> bool:
        """Validate compound ID format (KEGG or ChEBI).
        
        Default implementation, can be overridden.
        
        Args:
            compound_id: Compound identifier to validate
            
        Returns:
            True if format is valid
            
        Supported formats:
            - KEGG: C##### (5 digits, e.g., C00002)
            - ChEBI: CHEBI:##### (e.g., CHEBI:15422)
        """
        # KEGG: C##### (5 digits)
        if re.match(r'^C\d{5}$', compound_id):
            return True
        # ChEBI: CHEBI:#####
        if re.match(r'^CHEBI:\d+$', compound_id):
            return True
        return False
    
    def normalize_compound_id(self, compound_id: str) -> str:
        """Normalize compound ID format.
        
        Default implementation, can be overridden.
        
        Args:
            compound_id: Raw compound identifier
            
        Returns:
            Normalized compound identifier
            
        Examples:
            >>> mapper.normalize_compound_id("c00002")
            "C00002"
            >>> mapper.normalize_compound_id("chebi:15422")
            "CHEBI:15422"
        """
        # Uppercase for consistency
        normalized = compound_id.strip().upper()
        
        # Normalize ChEBI format
        if normalized.startswith("CHEBI:"):
            return normalized
        elif normalized.startswith("CHEBI"):
            # Add missing colon
            return "CHEBI:" + normalized[5:].lstrip(":")
        
        return normalized
