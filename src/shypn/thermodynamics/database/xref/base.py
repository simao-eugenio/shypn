"""Base class for cross-reference mapping."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict


class CrossReferenceMapperBase(ABC):
    """
    Abstract base class for cross-reference mapping between database IDs.
    
    Defines interface for converting between different compound identifier
    systems (KEGG, ChEBI, BiGG, etc.).
    
    Subclasses must implement:
    - chebi_to_kegg: Convert ChEBI ID to KEGG compound ID
    - kegg_to_chebi: Convert KEGG ID to ChEBI ID(s)
    - bigg_to_kegg: Convert BiGG ID to KEGG compound ID
    - resolve_alias: Resolve common name to KEGG ID
    """
    
    @abstractmethod
    def chebi_to_kegg(self, chebi_id: str) -> Optional[str]:
        """
        Convert ChEBI ID to KEGG compound ID.
        
        Args:
            chebi_id: ChEBI identifier (e.g., "CHEBI:15422" or "15422")
            
        Returns:
            KEGG compound ID (e.g., "C00002") or None
            
        Example:
            >>> mapper.chebi_to_kegg("CHEBI:15422")
            'C00002'  # ATP
        """
        pass
    
    @abstractmethod
    def kegg_to_chebi(self, kegg_id: str) -> List[str]:
        """
        Convert KEGG compound ID to ChEBI ID(s).
        
        Note: One KEGG ID may map to multiple ChEBI IDs
        (different protonation states, stereoisomers).
        
        Args:
            kegg_id: KEGG compound identifier (e.g., "C00002")
            
        Returns:
            List of ChEBI IDs (may be empty)
            
        Example:
            >>> mapper.kegg_to_chebi("C00002")
            ['CHEBI:15422', 'CHEBI:30616']  # ATP variants
        """
        pass
    
    @abstractmethod
    def bigg_to_kegg(self, bigg_id: str) -> Optional[str]:
        """
        Convert BiGG ID to KEGG compound ID.
        
        BiGG IDs often include compartment suffix (e.g., atp_c for cytosolic ATP).
        Implementations should handle both with and without compartment suffix.
        
        Args:
            bigg_id: BiGG identifier (e.g., "atp_c" or "atp")
            
        Returns:
            KEGG compound ID (e.g., "C00002") or None
            
        Example:
            >>> mapper.bigg_to_kegg("atp_c")
            'C00002'
        """
        pass
    
    @abstractmethod
    def resolve_alias(self, name: str) -> Optional[str]:
        """
        Resolve common name alias to canonical KEGG ID.
        
        Should handle case-insensitive matching for common names.
        
        Args:
            name: Common name (e.g., "ATP", "atp", "Adenosine triphosphate")
            
        Returns:
            KEGG compound ID or None
            
        Example:
            >>> mapper.resolve_alias("ATP")
            'C00002'
            >>> mapper.resolve_alias("adenosine triphosphate")
            'C00002'
        """
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, int]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with mapping counts
            
        Example:
            >>> stats = mapper.get_statistics()
            >>> print(stats)
            {'kegg_to_chebi': 20000, 'chebi_to_kegg': 18500, 'bigg_to_kegg': 3200}
        """
        pass
