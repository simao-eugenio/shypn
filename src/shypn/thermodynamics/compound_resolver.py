"""Compound ID resolver for biochemical databases.

This module maps compound identifiers across different database formats:
- KEGG C-numbers (e.g., C00002 for ATP)
- ChEBI IDs (e.g., CHEBI:15422 for ATP)
- Common names (e.g., "ATP", "adenosine triphosphate")

Architecture: Thin loader that delegates to mapping files and web services.
"""

import logging
import json
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CompoundIdentity:
    """Unified compound identity across databases.
    
    Attributes:
        kegg_id: KEGG C-number (e.g., C00002)
        chebi_id: ChEBI identifier (e.g., CHEBI:15422)
        names: List of common/systematic names
        formula: Chemical formula (optional)
    """
    kegg_id: Optional[str] = None
    chebi_id: Optional[str] = None
    names: List[str] = None
    formula: Optional[str] = None
    
    def __post_init__(self):
        if self.names is None:
            self.names = []
    
    @property
    def primary_name(self) -> str:
        """Get the first/primary name."""
        return self.names[0] if self.names else "Unknown"


class CompoundResolver:
    """Resolve compound identifiers across biochemical databases.
    
    This class provides a unified interface for mapping between:
    - KEGG C-numbers
    - ChEBI identifiers
    - Common names
    
    Data sources (in priority order):
    1. Local mapping files (fast, offline)
    2. Web services (slow, requires internet)
    
    Example:
        >>> resolver = CompoundResolver()
        >>> identity = resolver.resolve("C00002")
        >>> print(identity.chebi_id)  # CHEBI:15422
        >>> print(identity.primary_name)  # ATP
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize resolver with mapping data.
        
        Args:
            data_dir: Directory containing mapping JSON files.
                     If None, uses default data directory.
        """
        if data_dir is None:
            # Default to thermodynamics data directory
            data_dir = Path(__file__).parent / "data"
        
        self.data_dir = Path(data_dir)
        self._kegg_to_chebi: Dict[str, str] = {}
        self._chebi_to_kegg: Dict[str, str] = {}
        self._name_to_kegg: Dict[str, str] = {}
        self._compound_names: Dict[str, List[str]] = {}
        
        # Load mapping data
        self._load_mappings()
    
    def resolve(self, identifier: str) -> Optional[CompoundIdentity]:
        """Resolve any compound identifier to full identity.
        
        Args:
            identifier: KEGG ID, ChEBI ID, or common name
            
        Returns:
            CompoundIdentity if found, None otherwise
        """
        identifier = identifier.strip()
        
        # Try as KEGG ID
        if identifier.startswith("C") and len(identifier) == 6:
            return self._resolve_from_kegg(identifier)
        
        # Try as ChEBI ID
        if identifier.startswith("CHEBI:"):
            return self._resolve_from_chebi(identifier)
        
        # Try as common name
        return self._resolve_from_name(identifier)
    
    def resolve_to_kegg(self, identifier: str) -> Optional[str]:
        """Convert any identifier to KEGG C-number.
        
        Args:
            identifier: KEGG ID, ChEBI ID, or name
            
        Returns:
            KEGG C-number if found, None otherwise
        """
        identity = self.resolve(identifier)
        return identity.kegg_id if identity else None
    
    def resolve_to_chebi(self, identifier: str) -> Optional[str]:
        """Convert any identifier to ChEBI ID.
        
        Args:
            identifier: KEGG ID, ChEBI ID, or name
            
        Returns:
            ChEBI identifier if found, None otherwise
        """
        identity = self.resolve(identifier)
        return identity.chebi_id if identity else None
    
    def get_compound_names(self, identifier: str) -> List[str]:
        """Get all known names for a compound.
        
        Args:
            identifier: Any compound identifier
            
        Returns:
            List of names (empty if not found)
        """
        identity = self.resolve(identifier)
        return identity.names if identity else []
    
    def _resolve_from_kegg(self, kegg_id: str) -> Optional[CompoundIdentity]:
        """Resolve from KEGG C-number."""
        chebi_id = self._kegg_to_chebi.get(kegg_id)
        names = self._compound_names.get(kegg_id, [])
        
        if chebi_id or names:
            return CompoundIdentity(
                kegg_id=kegg_id,
                chebi_id=chebi_id,
                names=names
            )
        
        return None
    
    def _resolve_from_chebi(self, chebi_id: str) -> Optional[CompoundIdentity]:
        """Resolve from ChEBI identifier."""
        kegg_id = self._chebi_to_kegg.get(chebi_id)
        names = self._compound_names.get(kegg_id, []) if kegg_id else []
        
        if kegg_id or names:
            return CompoundIdentity(
                kegg_id=kegg_id,
                chebi_id=chebi_id,
                names=names
            )
        
        return None
    
    def _resolve_from_name(self, name: str) -> Optional[CompoundIdentity]:
        """Resolve from common name (case-insensitive)."""
        name_lower = name.lower()
        
        # Try exact match first
        kegg_id = self._name_to_kegg.get(name_lower)
        
        # Try partial match if exact fails
        if kegg_id is None:
            for stored_name, stored_kegg in self._name_to_kegg.items():
                if name_lower in stored_name or stored_name in name_lower:
                    kegg_id = stored_kegg
                    break
        
        if kegg_id:
            return self._resolve_from_kegg(kegg_id)
        
        return None
    
    def _load_mappings(self):
        """Load compound mappings from JSON files."""
        mapping_file = self.data_dir / "compound_mappings.json"
        
        if not mapping_file.exists():
            logger.warning(f"Compound mapping file not found: {mapping_file}")
            logger.info("Resolver will work with empty mappings (add data to enable)")
            return
        
        try:
            with open(mapping_file, 'r') as f:
                data = json.load(f)
            
            # Load KEGG ↔ ChEBI mappings
            for kegg_id, info in data.get("compounds", {}).items():
                chebi_id = info.get("chebi_id")
                names = info.get("names", [])
                
                if chebi_id:
                    self._kegg_to_chebi[kegg_id] = chebi_id
                    self._chebi_to_kegg[chebi_id] = kegg_id
                
                if names:
                    self._compound_names[kegg_id] = names
                    for name in names:
                        self._name_to_kegg[name.lower()] = kegg_id
            
            logger.info(f"Loaded {len(self._kegg_to_chebi)} compound mappings")
            
        except Exception as e:
            logger.error(f"Failed to load compound mappings: {e}")
    
    def add_mapping(
        self,
        kegg_id: str,
        chebi_id: Optional[str] = None,
        names: Optional[List[str]] = None
    ):
        """Add a compound mapping programmatically.
        
        Useful for testing or dynamic mapping updates.
        
        Args:
            kegg_id: KEGG C-number
            chebi_id: ChEBI identifier (optional)
            names: List of compound names (optional)
        """
        if chebi_id:
            self._kegg_to_chebi[kegg_id] = chebi_id
            self._chebi_to_kegg[chebi_id] = kegg_id
        
        if names:
            self._compound_names[kegg_id] = names
            for name in names:
                self._name_to_kegg[name.lower()] = kegg_id
        
        logger.debug(f"Added mapping: {kegg_id} -> {chebi_id}")
