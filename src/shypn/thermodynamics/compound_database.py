"""Local SQLite database for compound thermodynamic properties.

Provides caching layer between in-memory mapper and remote APIs.
Stores fetched compounds to minimize API calls and enable offline usage.
"""

import sqlite3
from typing import Optional, Dict, List, Any
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class CompoundRecord:
    """Compound thermodynamic data record."""
    compound_id: str
    compound_name: str
    delta_g_formation: Optional[float] = None  # kJ/mol
    charge: int = 0  # at pH 7
    n_protons: int = 0
    pKa_values: Optional[str] = None  # JSON array or comma-separated
    source: str = "manual"  # manual, equilibrator, brenda
    fetch_date: Optional[str] = None
    notes: Optional[str] = None


class CompoundDatabase:
    """Local SQLite database for compound properties.
    
    Provides:
    - Fast local lookup (no API calls)
    - Caching of remote fetch results
    - Offline usage support
    - Query history tracking
    
    Database schema:
        compounds(
            compound_id PRIMARY KEY,
            compound_name,
            delta_g_formation,
            charge,
            n_protons,
            pKa_values,  -- JSON array or comma-separated
            source,      -- manual, equilibrator, brenda
            fetch_date,  -- ISO format
            notes
        )
    
    Example:
        >>> db = CompoundDatabase()
        >>> atp = db.get_compound("C00002")
        >>> if not atp:
        ...     atp = db.fetch_remote("C00002", source="equilibrator")
        ...     db.cache_compound(atp)
    """
    
    DEFAULT_DB_PATH = "workspace/compound_cache.db"
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize compound database.
        
        Args:
            db_path: Path to SQLite database (creates if not exists)
        """
        self.db_path = db_path or self.DEFAULT_DB_PATH
        
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_schema()
        
        logger.info(f"CompoundDatabase initialized: {self.db_path}")
    
    def _init_schema(self):
        """Create database schema if not exists."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS compounds (
                    compound_id TEXT PRIMARY KEY,
                    compound_name TEXT NOT NULL,
                    delta_g_formation REAL,
                    charge INTEGER DEFAULT 0,
                    n_protons INTEGER DEFAULT 0,
                    pKa_values TEXT,
                    source TEXT DEFAULT 'manual',
                    fetch_date TEXT,
                    notes TEXT
                )
            """)
            
            # Index for fast name lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_compound_name 
                ON compounds(compound_name)
            """)
            
            conn.commit()
    
    def get_compound(self, compound_id: str) -> Optional[Dict[str, Any]]:
        """Get compound from local database.
        
        Args:
            compound_id: KEGG/BiGG compound ID
        
        Returns:
            Compound data dict or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM compounds WHERE compound_id = ?",
                (compound_id,)
            )
            row = cursor.fetchone()
            
            if row:
                data = dict(row)
                # Parse pKa_values from string to list
                if data.get('pKa_values'):
                    try:
                        import json
                        data['pKa_values'] = json.loads(data['pKa_values'])
                    except (json.JSONDecodeError, ValueError, TypeError) as e:
                        # Fallback: comma-separated values
                        logger.debug(f"Failed to parse pKa JSON for {compound_id}, trying CSV format: {e}")
                        pka_str = data['pKa_values']
                        try:
                            data['pKa_values'] = [float(x.strip()) for x in pka_str.split(',') if x.strip()]
                        except (ValueError, AttributeError) as e2:
                            logger.warning(f"Failed to parse pKa values for {compound_id}: {e2}")
                            data['pKa_values'] = []
                
                logger.debug(f"Found compound {compound_id} in local cache")
                return data
            
            return None
    
    def get_compound_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get compound by name (case-insensitive).
        
        Args:
            name: Compound name
        
        Returns:
            Compound data dict or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM compounds WHERE LOWER(compound_name) = LOWER(?)",
                (name,)
            )
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            
            return None
    
    def cache_compound(self, data: Dict[str, Any]) -> bool:
        """Cache compound data in local database.
        
        Args:
            data: Compound data dict (must include compound_id)
        
        Returns:
            True if cached successfully
        """
        if 'compound_id' not in data:
            logger.error("Cannot cache compound without compound_id")
            return False
        
        try:
            # Serialize pKa_values to JSON if it's a list
            pka_values = data.get('pKa_values')
            if isinstance(pka_values, list):
                import json
                pka_values = json.dumps(pka_values)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO compounds 
                    (compound_id, compound_name, delta_g_formation, charge, 
                     n_protons, pKa_values, source, fetch_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data['compound_id'],
                    data.get('compound_name', ''),
                    data.get('delta_g_formation'),
                    data.get('charge', 0),
                    data.get('n_protons', 0),
                    pka_values,
                    data.get('source', 'manual'),
                    data.get('fetch_date', datetime.now().isoformat()),
                    data.get('notes'),
                ))
                conn.commit()
            
            logger.info(f"Cached compound {data['compound_id']} ({data.get('compound_name')})")
            return True
        
        except Exception as e:
            logger.error(f"Failed to cache compound: {e}")
            return False
    
    def search_compounds(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search compounds by name or ID.
        
        Args:
            query: Search query (partial match)
            limit: Maximum results
        
        Returns:
            List of compound data dicts
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM compounds 
                WHERE compound_id LIKE ? OR compound_name LIKE ?
                ORDER BY compound_name
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def has_compound(self, compound_id: str) -> bool:
        """Check if compound exists in local database.
        
        Args:
            compound_id: KEGG/BiGG compound ID
        
        Returns:
            True if compound exists locally
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM compounds WHERE compound_id = ?",
                (compound_id,)
            )
            return cursor.fetchone() is not None
    
    def get_cached_count(self) -> int:
        """Get number of cached compounds.
        
        Returns:
            Count of compounds in database
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM compounds")
            return cursor.fetchone()[0]
    
    def get_all_cached(self) -> List[Dict[str, Any]]:
        """Get all cached compounds from the database.
        
        Returns:
            List of all compound data dicts
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT compound_id, compound_name, delta_g_formation, 
                       charge, n_protons, pKa_values, source, fetch_date
                FROM compounds 
                ORDER BY compound_name
            """)
            
            compounds = []
            for row in cursor.fetchall():
                compound = dict(row)
                # Parse pKa_values from JSON string to list
                if compound.get('pKa_values'):
                    try:
                        import json
                        compound['pKa_values'] = json.loads(compound['pKa_values'])
                    except (json.JSONDecodeError, ValueError, TypeError) as e:
                        logger.debug(f"Failed to parse pKa JSON for {compound.get('compound_id')}: {e}")
                        compound['pKa_values'] = []
                else:
                    compound['pKa_values'] = []
                compounds.append(compound)
            
            return compounds
    
    def fetch_remote(self, compound_id: str, source: str = "equilibrator") -> Optional[Dict[str, Any]]:
        """Fetch compound from remote API.
        
        Args:
            compound_id: KEGG/BiGG compound ID
            source: API source (equilibrator, brenda)
        
        Returns:
            Compound data dict or None if not found
        
        Implementation:
            - Uses EquilibratorProvider for ΔGf° (real API data)
            - Falls back to placeholder for charge/pKa (structural properties)
            - BRENDA support planned for Week 3
        """
        # Get compound name from mapper
        from shypn.thermodynamics.compound_mapper import CompoundMapper
        compound_name = CompoundMapper.id_to_name(compound_id)
        if not compound_name:
            compound_name = f'Compound_{compound_id}'
        
        # Structural property placeholders (charge, pKa, n_protons)
        # These would ideally come from ChEBI/PubChem in future
        structural_data = {
            'C00002': {'charge': -4, 'n_protons': 12, 'pKa_values': [6.5, 4.0, 2.0]},
            'C00008': {'charge': -3, 'n_protons': 12, 'pKa_values': [6.5, 4.0, 2.0]},
            'C00020': {'charge': -2, 'n_protons': 12, 'pKa_values': [6.5, 3.8]},
            'C00003': {'charge': -1, 'n_protons': 21, 'pKa_values': [3.5]},
            'C00004': {'charge': -2, 'n_protons': 22, 'pKa_values': [13.0]},
            'C00006': {'charge': -3, 'n_protons': 21, 'pKa_values': [6.5]},
            'C00005': {'charge': -4, 'n_protons': 22, 'pKa_values': [13.0]},
            'C00031': {'charge': 0, 'n_protons': 12, 'pKa_values': [12.3]},
            'C00022': {'charge': -1, 'n_protons': 3, 'pKa_values': [2.5]},
            'C00024': {'charge': -4, 'n_protons': 20, 'pKa_values': [8.3]},
        }
        
        # Default structural properties for unknown compounds
        structure = structural_data.get(compound_id, {
            'charge': 0,
            'n_protons': 1,
            'pKa_values': []
        })
        
        # Fetch thermodynamic data from API
        delta_g_formation = None
        api_notes = None
        
        if source == "equilibrator":
            try:
                from shypn.thermodynamics.database import EquilibratorProvider
                
                # Create provider (uses official equilibrator-api package)
                provider = EquilibratorProvider()
                
                # Check if API is available (handles import/initialization errors)
                if provider._check_availability():
                    compound = provider.get_compound(
                        compound_id=compound_id,
                        ph=7.0,  # Biochemical standard state
                        temperature=298.15,  # 25°C
                        ionic_strength=0.1  # 0.1 M
                    )
                    
                    if compound:
                        delta_g_formation = compound.delta_g_formation
                        compound_name = compound.name  # Use API name if available
                        api_notes = f"ΔGf° from eQuilibrator API (uncertainty: ±{compound.uncertainty:.1f} kJ/mol)"
                        logger.info(f"Fetched {compound_id} from eQuilibrator: ΔGf°={delta_g_formation:.2f} kJ/mol")
                    else:
                        logger.warning(f"Compound {compound_id} not found in eQuilibrator")
                        api_notes = None
                else:
                    # API unavailable (SSL, network, etc)
                    logger.warning("eQuilibrator API unavailable")
                    api_notes = None
                    
            except ImportError as e:
                logger.error(f"EquilibratorProvider not available: {e}")
                api_notes = None
            except Exception as e:
                logger.error(f"eQuilibrator error: {e}")
                api_notes = None
        
        elif source == "brenda":
            # BRENDA support planned for Week 3
            logger.info("BRENDA support not yet implemented (Week 3)")
            api_notes = None
        
        # If API fetch failed, return None (user can enter manually)
        if delta_g_formation is None:
            logger.warning(f"No thermodynamic data available for {compound_id} from {source}")
            logger.info("User can enter data manually or try different compound ID")
            return None
        
        # Build complete response
        return {
            'compound_id': compound_id,
            'compound_name': compound_name,
            'delta_g_formation': delta_g_formation,
            'charge': structure['charge'],
            'n_protons': structure['n_protons'],
            'pKa_values': structure['pKa_values'],
            'source': source,
            'fetch_date': datetime.now().isoformat(),
            'notes': api_notes or f"Fetched from {source}"
        }
    
    def get_or_fetch(self, compound_id: str, source: str = "equilibrator", 
                     cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get compound from local cache, or fetch remotely if not found.
        
        This is the main entry point for compound lookup.
        
        Args:
            compound_id: KEGG/BiGG compound ID
            source: Remote API source (if needed)
            cache: Whether to cache remote results
        
        Returns:
            Compound data dict or None if not found anywhere
        
        Example:
            >>> db = CompoundDatabase()
            >>> atp = db.get_or_fetch("C00002")
            >>> # First call: fetches from remote, caches locally
            >>> atp = db.get_or_fetch("C00002")
            >>> # Second call: returns from cache (fast)
        """
        # Try local cache first
        data = self.get_compound(compound_id)
        if data:
            logger.debug(f"Cache hit: {compound_id}")
            return data
        
        # Cache miss - fetch from remote
        logger.info(f"Cache miss: {compound_id}, fetching from {source}")
        data = self.fetch_remote(compound_id, source)
        
        if data and cache:
            self.cache_compound(data)
        
        return data
    
    def populate_from_mapper(self):
        """Populate database from CompoundMapper (one-time seed).
        
        Seeds the local database with known compounds from
        the in-memory CompoundMapper.
        """
        from shypn.thermodynamics.compound_mapper import CompoundMapper
        
        count = 0
        for compound_id in CompoundMapper.get_all_ids():
            if not self.has_compound(compound_id):
                name = CompoundMapper.id_to_name(compound_id)
                self.cache_compound({
                    'compound_id': compound_id,
                    'compound_name': name,
                    'source': 'mapper',
                    'fetch_date': datetime.now().isoformat(),
                    'notes': 'Seeded from CompoundMapper'
                })
                count += 1
        
        logger.info(f"Populated database with {count} compounds from mapper")
        return count
    
    def clear_cache(self):
        """Clear all cached compounds (destructive)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM compounds")
            conn.commit()
        
        logger.warning("Cleared all cached compounds")
    
    def get_statistics(self) -> Dict[str, int]:
        """Get database statistics.
        
        Returns:
            Statistics dict with counts by source
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Total count
            total = conn.execute("SELECT COUNT(*) as count FROM compounds").fetchone()['count']
            
            # Count by source
            cursor = conn.execute("""
                SELECT source, COUNT(*) as count 
                FROM compounds 
                GROUP BY source
            """)
            by_source = {row['source']: row['count'] for row in cursor}
            
            return {
                'total': total,
                'by_source': by_source
            }
