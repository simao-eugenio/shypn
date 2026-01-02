"""Abstract base class for compound cross-reference databases.

Defines the interface for compound ID mapping between different biochemical databases
(KEGG, ChEBI, BiGG, etc.). Implementations can use different backends (SQLite, JSON, etc.).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Set
from datetime import datetime


@dataclass
class CompoundIdentity:
    """Unified compound identity across multiple databases.
    
    Attributes:
        kegg_id: KEGG compound identifier (e.g., C00002)
        chebi_id: ChEBI identifier (e.g., CHEBI:15422)
        bigg_id: BiGG identifier (e.g., atp_c)
        primary_name: Primary compound name
        aliases: Alternative names/synonyms
        formula: Chemical formula
        source: Data source (manual, kegg_api, json_import)
        last_updated: Last update timestamp
    """
    kegg_id: str
    chebi_id: Optional[str] = None
    bigg_id: Optional[str] = None
    primary_name: Optional[str] = None
    aliases: List[str] = None
    formula: Optional[str] = None
    source: str = "unknown"
    last_updated: Optional[datetime] = None
    
    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []
    
    @property
    def all_names(self) -> List[str]:
        """Get all names including primary and aliases."""
        names = []
        if self.primary_name:
            names.append(self.primary_name)
        names.extend(self.aliases)
        return names
    
    def has_database_id(self, db_type: str) -> bool:
        """Check if compound has ID for specified database.
        
        Args:
            db_type: Database type ('kegg', 'chebi', 'bigg')
            
        Returns:
            True if ID exists
        """
        if db_type.lower() == 'kegg':
            return bool(self.kegg_id)
        elif db_type.lower() == 'chebi':
            return bool(self.chebi_id)
        elif db_type.lower() == 'bigg':
            return bool(self.bigg_id)
        return False


class CompoundDatabaseBase(ABC):
    """Abstract base class for compound cross-reference databases.
    
    Defines the interface for compound ID mapping and lookup operations.
    Implementations handle different storage backends (SQLite, JSON, etc.).
    """
    
    @abstractmethod
    def get_by_kegg(self, kegg_id: str) -> Optional[CompoundIdentity]:
        """Retrieve compound by KEGG ID.
        
        Args:
            kegg_id: KEGG compound ID (e.g., C00002)
            
        Returns:
            CompoundIdentity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_chebi(self, chebi_id: str) -> Optional[CompoundIdentity]:
        """Retrieve compound by ChEBI ID.
        
        Args:
            chebi_id: ChEBI identifier (e.g., CHEBI:15422)
            
        Returns:
            CompoundIdentity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_bigg(self, bigg_id: str) -> Optional[CompoundIdentity]:
        """Retrieve compound by BiGG ID.
        
        Args:
            bigg_id: BiGG identifier (e.g., atp_c)
            
        Returns:
            CompoundIdentity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_name(self, name: str) -> Optional[CompoundIdentity]:
        """Retrieve compound by common name.
        
        Args:
            name: Compound name (case-insensitive)
            
        Returns:
            CompoundIdentity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def search_by_name(self, query: str, limit: int = 10) -> List[CompoundIdentity]:
        """Search compounds by partial name match.
        
        Args:
            query: Search query (case-insensitive)
            limit: Maximum results to return
            
        Returns:
            List of matching compounds
        """
        pass
    
    @abstractmethod
    def insert(self, identity: CompoundIdentity) -> bool:
        """Insert new compound identity.
        
        Args:
            identity: Compound identity to insert
            
        Returns:
            True if inserted, False if already exists
        """
        pass
    
    @abstractmethod
    def update(self, identity: CompoundIdentity) -> bool:
        """Update existing compound identity.
        
        Args:
            identity: Compound identity with updated data
            
        Returns:
            True if updated, False if not found
        """
        pass
    
    @abstractmethod
    def upsert(self, identity: CompoundIdentity) -> bool:
        """Insert or update compound identity.
        
        Args:
            identity: Compound identity to insert/update
            
        Returns:
            True on success
        """
        pass
    
    @abstractmethod
    def delete(self, kegg_id: str) -> bool:
        """Delete compound by KEGG ID.
        
        Args:
            kegg_id: KEGG compound ID
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    def get_all_kegg_ids(self) -> Set[str]:
        """Get all KEGG IDs in database.
        
        Returns:
            Set of KEGG compound IDs
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Get total number of compounds.
        
        Returns:
            Number of compounds in database
        """
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, int]:
        """Get database statistics.
        
        Returns:
            Dictionary with counts (total, with_chebi, with_bigg, etc.)
        """
        pass
    
    @abstractmethod
    def close(self):
        """Close database connection and cleanup resources."""
        pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
