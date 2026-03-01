#!/usr/bin/env python3
"""SABIO-RK cache manager.

Manages caching of SABIO-RK API results including kinetic parameters,
raw data, and aggregated statistics.
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base_cache_manager import BaseCacheManager


class SabioRKCacheManager(BaseCacheManager):
    """Cache manager for SABIO-RK API results.
    
    Caches:
    - Raw query results (parameters for EC number + organism)
    - Parameter statistics (median, mean, etc.)
    - Query metadata (timestamp, result count)
    
    Attributes:
        db: HeuristicDatabase instance
    """
    
    def __init__(self, database):
        """Initialize SABIO-RK cache manager.
        
        Args:
            database: HeuristicDatabase instance
        """
        super().__init__(database, 'SABIO-RK')
        self._ensure_table()
    
    def _ensure_table(self):
        """Ensure SABIO-RK cache table exists in database."""
        # Schema extension for SABIO-RK caching
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='sabio_rk_cache'
            """)
            
            if not cursor.fetchone():
                self.logger.info("Creating sabio_rk_cache table...")
                cursor.execute("""
                    CREATE TABLE sabio_rk_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query_key TEXT UNIQUE NOT NULL,
                        ec_number TEXT,
                        organism TEXT,
                        result_count INTEGER,
                        parameters TEXT NOT NULL,  -- JSON blob with all parameters
                        statistics TEXT,           -- JSON blob with aggregated stats
                        query_date TEXT NOT NULL,  -- ISO8601 timestamp
                        last_accessed TEXT,        -- ISO8601 timestamp
                        access_count INTEGER DEFAULT 0,
                        UNIQUE(ec_number, organism)
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX idx_sabio_cache_ec ON sabio_rk_cache(ec_number)
                """)
                
                cursor.execute("""
                    CREATE INDEX idx_sabio_cache_key ON sabio_rk_cache(query_key)
                """)
                
                conn.commit()
                self.logger.info("sabio_rk_cache table created")
    
    def build_query_key(self, ec_number: str, organism: Optional[str] = None) -> str:  # type: ignore[override]
        """Build unique query key for SABIO-RK query.
        
        Args:
            ec_number: EC number (e.g., '2.7.1.1')
            organism: Organism name (optional)
        
        Returns:
            Unique query key
        """
        org_part = organism if organism else 'all'
        return f"sabio_rk|{ec_number}|{org_part}"
    
    def get_cached_result(self, query_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached SABIO-RK result.
        
        Args:
            query_key: Unique identifier for the query
        
        Returns:
            Cached result dict or None if not found
        """
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT parameters, statistics, result_count, query_date
                FROM sabio_rk_cache
                WHERE query_key = ?
            """, (query_key,))
            
            row = cursor.fetchone()
            
            if row:
                # Update access tracking
                cursor.execute("""
                    UPDATE sabio_rk_cache
                    SET access_count = access_count + 1,
                        last_accessed = ?
                    WHERE query_key = ?
                """, (datetime.now().isoformat(), query_key))
                
                conn.commit()
                
                return {
                    'parameters': json.loads(row[0]),
                    'statistics': json.loads(row[1]) if row[1] else None,
                    'result_count': row[2],
                    'cached_date': row[3]
                }
            
            return None
    
    def store_result(self, query_key: str, result: Dict[str, Any]) -> bool:
        """Store SABIO-RK result in cache.
        
        Args:
            query_key: Unique identifier for the query
            result: Result dict with 'parameters', optional 'statistics'
        
        Returns:
            True if stored successfully
        """
        try:
            # Extract EC number and organism from query_key
            parts = query_key.split('|')
            ec_number = parts[1] if len(parts) > 1 else None
            organism = parts[2] if len(parts) > 2 and parts[2] != 'all' else None
            
            parameters = result.get('parameters', [])
            statistics = result.get('statistics', None)
            
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                
                now = datetime.now().isoformat()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO sabio_rk_cache
                    (query_key, ec_number, organism, result_count, 
                     parameters, statistics, query_date, last_accessed, access_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 
                            COALESCE((SELECT access_count FROM sabio_rk_cache WHERE query_key = ?), 0))
                """, (
                    query_key,
                    ec_number,
                    organism,
                    len(parameters),
                    json.dumps(parameters),
                    json.dumps(statistics) if statistics else None,
                    now,
                    now,
                    query_key
                ))
                
                conn.commit()
                self.logger.debug(f"Stored {len(parameters)} parameters for {query_key}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to store result: {e}")
            return False
    
    def invalidate_cache(self, query_key: Optional[str] = None):
        """Invalidate SABIO-RK cache entries.
        
        Args:
            query_key: Specific key to invalidate, or None for all
        """
        super().invalidate_cache(query_key)
        
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            if query_key:
                cursor.execute("DELETE FROM sabio_rk_cache WHERE query_key = ?", (query_key,))
            else:
                cursor.execute("DELETE FROM sabio_rk_cache")
            
            deleted = cursor.rowcount
            conn.commit()
            self.logger.info(f"Invalidated {deleted} cache entries")
    
    def get_cache_summary(self) -> Dict[str, Any]:
        """Get summary of cached SABIO-RK data.
        
        Returns:
            Dict with cache statistics
        """
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM sabio_rk_cache")
            total_entries = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT ec_number) FROM sabio_rk_cache")
            unique_ecs = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(result_count) FROM sabio_rk_cache")
            total_parameters = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT SUM(access_count) FROM sabio_rk_cache")
            total_accesses = cursor.fetchone()[0] or 0
            
            return {
                'total_cached_queries': total_entries,
                'unique_ec_numbers': unique_ecs,
                'total_parameters': total_parameters,
                'total_cache_accesses': total_accesses,
                **self.get_statistics()
            }
