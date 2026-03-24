"""
Base Species Mapper

Abstract base class for mapping chemical species to standardized compound identifiers.
Supports multiple identifier systems (KEGG, ChEBI, BiGG, etc.) through subclasses.

Architecture:
- Base class defines interface and common utilities
- Subclasses implement source-specific mapping (SBML, KEGG, BiGG)
- Uses CompoundResolver as fallback for name-based matching
- Caches mappings to avoid redundant lookups

Design Principles:
- Separation of concerns: Each mapper handles one source type
- Fallback mechanism: Name matching when annotations unavailable
- Performance: Caching and batch operations
- Extensibility: Easy to add new identifier systems

Note: This base class is for species-centric mapping (SBML species lists).
      For place-centric mapping with confidence scores, see
      thermodynamics/mappers/base_mapper.py (CompoundMapperBase).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import logging
import re


class SpeciesMapperBase(ABC):
    """
    Abstract base class for SBML species-to-compound mapping.

    Maps SBML species/metabolites to standardized KEGG compound IDs using
    annotations (MIRIAM URNs) and name-based fallbacks.

    For place-centric Petri net mapping with confidence scores, see
    thermodynamics.mappers.CompoundMapperBase instead.

    Subclasses must implement:
    - map_species(): Map a single species to a KEGG ID
    - _get_species_id(): Extract the cache key for a species

    Subclasses implement source-specific extraction logic.
    """
    
    def __init__(self, use_cache: bool = True):
        """
        Initialize mapper.
        
        Args:
            use_cache: Enable mapping cache for performance
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.use_cache = use_cache
        self._cache: Dict[str, Optional[str]] = {}
        
    def map_species_list(
        self,
        species_list: List
    ) -> Dict[str, Optional[str]]:
        """
        Map multiple species to KEGG compound IDs.
        
        Batch operation with caching for performance.
        
        Args:
            species_list: List of species objects to map
            
        Returns:
            Dict mapping species_id → KEGG compound ID (or None)
        """
        results = {}
        
        for species in species_list:
            species_id = self._get_species_id(species)
            
            # Check cache first
            if self.use_cache and species_id in self._cache:
                results[species_id] = self._cache[species_id]
                continue
            
            # Perform mapping
            compound_id = self.map_species(species)
            
            # Update cache
            if self.use_cache:
                self._cache[species_id] = compound_id
            
            results[species_id] = compound_id
        
        # Log statistics
        mapped_count = sum(1 for v in results.values() if v is not None)
        self.logger.info(
            f"Mapped {mapped_count}/{len(results)} species to KEGG compounds"
        )
        
        return results
    
    @abstractmethod
    def map_species(self, species) -> Optional[str]:
        """
        Map single species to KEGG compound ID.
        
        Must be implemented by subclasses.
        
        Args:
            species: Species object (format depends on source)
            
        Returns:
            KEGG compound ID (e.g., "C00002") or None
        """
        pass
    
    @abstractmethod
    def _get_species_id(self, species) -> str:
        """
        Extract species identifier for caching.
        
        Must be implemented by subclasses.
        
        Args:
            species: Species object
            
        Returns:
            Unique identifier string
        """
        pass
    
    def _extract_kegg_from_urn(self, urn: str) -> Optional[str]:
        """
        Extract KEGG compound ID from MIRIAM URN.
        
        Handles multiple KEGG URN formats:
        - urn:miriam:kegg.compound:C00002
        - urn:miriam:kegg:C00002
        - kegg.compound:C00002
        
        Args:
            urn: MIRIAM URN string
            
        Returns:
            KEGG compound ID (e.g., "C00002") or None
        """
        if not urn:
            return None
        
        # Match KEGG patterns
        kegg_patterns = [
            r'urn:miriam:kegg\.compound:([CR]\d{5})',  # Standard MIRIAM
            r'urn:miriam:kegg:([CR]\d{5})',            # Alternate format
            r'kegg\.compound:([CR]\d{5})',             # Short format
            r'kegg:([CR]\d{5})',                       # Minimal format
        ]
        
        for pattern in kegg_patterns:
            match = re.search(pattern, urn, re.IGNORECASE)
            if match:
                compound_id = match.group(1).upper()
                # Validate format (C##### or R#####)
                if re.match(r'^[CR]\d{5}$', compound_id):
                    return compound_id
        
        return None
    
    def _extract_chebi_from_urn(self, urn: str) -> Optional[str]:
        """
        Extract ChEBI ID from MIRIAM URN.
        
        Handles multiple ChEBI URN formats:
        - urn:miriam:chebi:CHEBI:15422
        - urn:miriam:obo.chebi:CHEBI%3A15422
        - chebi:CHEBI:15422
        
        Note: ChEBI IDs are returned as-is. Caller responsible for
        converting to KEGG IDs using cross-reference databases.
        
        Args:
            urn: MIRIAM URN string
            
        Returns:
            ChEBI ID (e.g., "CHEBI:15422") or None
        """
        if not urn:
            return None
        
        # Match ChEBI patterns
        chebi_patterns = [
            r'urn:miriam:chebi:CHEBI:(\d+)',           # Standard MIRIAM
            r'urn:miriam:obo\.chebi:CHEBI%3A(\d+)',    # URL-encoded
            r'chebi:CHEBI:(\d+)',                      # Short format
            r'CHEBI:(\d+)',                            # Minimal format
        ]
        
        for pattern in chebi_patterns:
            match = re.search(pattern, urn, re.IGNORECASE)
            if match:
                chebi_id = match.group(1)
                return f"CHEBI:{chebi_id}"
        
        return None
    
    def _extract_bigg_from_urn(self, urn: str) -> Optional[str]:
        """
        Extract BiGG metabolite ID from URN.
        
        Handles BiGG URN formats:
        - http://identifiers.org/bigg.metabolite/atp
        - bigg.metabolite:atp
        
        Note: BiGG IDs are returned as-is. Caller responsible for
        converting to KEGG IDs using BiGG cross-references.
        
        Args:
            urn: URN or URL string
            
        Returns:
            BiGG metabolite ID (e.g., "atp") or None
        """
        if not urn:
            return None
        
        # Match BiGG patterns
        bigg_patterns = [
            r'identifiers\.org/bigg\.metabolite/([a-z0-9_]+)',  # identifiers.org URL
            r'bigg\.metabolite:([a-z0-9_]+)',                   # Short format
        ]
        
        for pattern in bigg_patterns:
            match = re.search(pattern, urn, re.IGNORECASE)
            if match:
                return match.group(1).lower()
        
        return None
    
    def clear_cache(self):
        """Clear the mapping cache."""
        self._cache.clear()
        self.logger.debug("Mapping cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache metrics (size, hits, etc.)
        """
        return {
            'cache_size': len(self._cache),
            'mapped_count': sum(1 for v in self._cache.values() if v is not None),
            'unmapped_count': sum(1 for v in self._cache.values() if v is None),
        }
