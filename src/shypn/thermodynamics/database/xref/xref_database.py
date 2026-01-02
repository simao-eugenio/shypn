"""Cross-reference database implementation with static JSON mapping files."""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, List
from functools import lru_cache

from .base import CrossReferenceMapperBase


class CrossReferenceDatabase(CrossReferenceMapperBase):
    """
    Static cross-reference database for compound ID conversion.
    
    Loads pre-built mapping files for fast lookup between:
    - KEGG Compound IDs (C00002)
    - ChEBI IDs (CHEBI:15422)
    - BiGG IDs (atp_c)
    
    Supports bidirectional mapping and common name aliases.
    Uses LRU caching for performance.
    
    Example:
        >>> xref = CrossReferenceDatabase()
        >>> kegg_id = xref.chebi_to_kegg("CHEBI:15422")
        >>> print(kegg_id)  # C00002 (ATP)
        >>> 
        >>> chebi_ids = xref.kegg_to_chebi("C00002")
        >>> print(chebi_ids)  # ["CHEBI:15422", "CHEBI:30616"]
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize cross-reference database.
        
        Args:
            data_dir: Directory containing mapping files
                     (default: database/xref/data/)
        """
        self.logger = logging.getLogger(__name__)
        
        # Set data directory
        if data_dir is None:
            data_dir = Path(__file__).parent / "data"
        self.data_dir = Path(data_dir)
        
        # Initialize empty maps (will be loaded lazily or fail gracefully)
        self.kegg_to_chebi_map: Dict[str, List[str]] = {}
        self.chebi_to_kegg_map: Dict[str, str] = {}
        self.bigg_to_kegg_map: Dict[str, str] = {}
        self.alias_map: Dict[str, str] = {}
        
        # Load mapping files
        self._load_mappings()
    
    def _load_mappings(self):
        """Load all mapping files into memory."""
        try:
            # KEGG ↔ ChEBI mappings
            self.kegg_to_chebi_map = self._load_json("kegg_to_chebi.json")
            self.chebi_to_kegg_map = self._load_json("chebi_to_kegg.json")
            
            # BiGG → KEGG mappings
            self.bigg_to_kegg_map = self._load_json("bigg_to_kegg.json")
            
            # Alias mappings (e.g., ATP, atp, Atp all map to same)
            self.alias_map = self._load_json("compound_aliases.json")
            
            self.logger.info(
                f"Loaded cross-reference database: "
                f"{len(self.kegg_to_chebi_map)} KEGG→ChEBI, "
                f"{len(self.chebi_to_kegg_map)} ChEBI→KEGG, "
                f"{len(self.bigg_to_kegg_map)} BiGG→KEGG mappings"
            )
            
        except FileNotFoundError as e:
            self.logger.warning(
                f"Cross-reference database files not found: {e}. "
                f"Run scripts/xref_builder.py to generate mapping files."
            )
            # Graceful degradation - continue with empty maps
    
    def _load_json(self, filename: str) -> Dict:
        """
        Load JSON mapping file.
        
        Args:
            filename: Name of JSON file in data directory
            
        Returns:
            Parsed JSON dictionary, or empty dict if file not found
        """
        filepath = self.data_dir / filename
        if not filepath.exists():
            return {}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @lru_cache(maxsize=1024)
    def chebi_to_kegg(self, chebi_id: str) -> Optional[str]:
        """
        Convert ChEBI ID to KEGG compound ID.
        
        Args:
            chebi_id: ChEBI identifier (e.g., "CHEBI:15422" or "15422")
            
        Returns:
            KEGG compound ID (e.g., "C00002") or None
            
        Example:
            >>> xref.chebi_to_kegg("CHEBI:15422")
            'C00002'  # ATP
        """
        # Normalize ChEBI ID (add prefix if missing)
        if not chebi_id.startswith("CHEBI:"):
            chebi_id = f"CHEBI:{chebi_id}"
        
        kegg_id = self.chebi_to_kegg_map.get(chebi_id)
        
        if kegg_id:
            self.logger.debug(f"ChEBI→KEGG: {chebi_id} → {kegg_id}")
        
        return kegg_id
    
    @lru_cache(maxsize=1024)
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
            >>> xref.kegg_to_chebi("C00002")
            ['CHEBI:15422', 'CHEBI:30616']  # ATP variants
        """
        chebi_ids = self.kegg_to_chebi_map.get(kegg_id, [])
        
        # Ensure it's a list (for consistency)
        if isinstance(chebi_ids, str):
            chebi_ids = [chebi_ids]
        
        if chebi_ids:
            self.logger.debug(f"KEGG→ChEBI: {kegg_id} → {chebi_ids}")
        
        return chebi_ids
    
    @lru_cache(maxsize=1024)
    def bigg_to_kegg(self, bigg_id: str) -> Optional[str]:
        """
        Convert BiGG ID to KEGG compound ID.
        
        BiGG IDs often include compartment suffix (e.g., atp_c for cytosolic ATP).
        This method strips compartment suffix if needed.
        
        Args:
            bigg_id: BiGG identifier (e.g., "atp_c" or "atp")
            
        Returns:
            KEGG compound ID (e.g., "C00002") or None
            
        Example:
            >>> xref.bigg_to_kegg("atp_c")
            'C00002'
        """
        # Try exact match first
        kegg_id = self.bigg_to_kegg_map.get(bigg_id)
        if kegg_id:
            self.logger.debug(f"BiGG→KEGG: {bigg_id} → {kegg_id}")
            return kegg_id
        
        # Try without compartment suffix (e.g., atp_c → atp)
        if '_' in bigg_id:
            base_id = bigg_id.rsplit('_', 1)[0]
            kegg_id = self.bigg_to_kegg_map.get(base_id)
            if kegg_id:
                self.logger.debug(f"BiGG→KEGG: {bigg_id} (base: {base_id}) → {kegg_id}")
                return kegg_id
        
        return None
    
    def resolve_alias(self, name: str) -> Optional[str]:
        """
        Resolve common name alias to canonical KEGG ID.
        
        Handles case-insensitive name matching.
        
        Args:
            name: Common name (e.g., "ATP", "atp", "Adenosine triphosphate")
            
        Returns:
            KEGG compound ID or None
            
        Example:
            >>> xref.resolve_alias("ATP")
            'C00002'
            >>> xref.resolve_alias("adenosine triphosphate")
            'C00002'
        """
        # Try exact match (case-sensitive)
        kegg_id = self.alias_map.get(name)
        if kegg_id:
            self.logger.debug(f"Alias→KEGG: '{name}' → {kegg_id}")
            return kegg_id
        
        # Try case-insensitive match
        name_lower = name.lower()
        for alias, kegg_id in self.alias_map.items():
            if alias.lower() == name_lower:
                self.logger.debug(f"Alias→KEGG (case-insensitive): '{name}' → {kegg_id}")
                return kegg_id
        
        return None
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with mapping counts
            
        Example:
            >>> stats = xref.get_statistics()
            >>> print(stats)
            {'kegg_to_chebi': 20000, 'chebi_to_kegg': 18500, ...}
        """
        return {
            'kegg_to_chebi': len(self.kegg_to_chebi_map),
            'chebi_to_kegg': len(self.chebi_to_kegg_map),
            'bigg_to_kegg': len(self.bigg_to_kegg_map),
            'aliases': len(self.alias_map),
        }
    
    def is_available(self) -> bool:
        """
        Check if database is available (mapping files loaded).
        
        Returns:
            True if at least one mapping file was loaded successfully
        """
        return (
            len(self.kegg_to_chebi_map) > 0 or
            len(self.chebi_to_kegg_map) > 0 or
            len(self.bigg_to_kegg_map) > 0
        )
