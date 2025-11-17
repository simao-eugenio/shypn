#!/usr/bin/env python3
"""BRENDA cache manager.

Manages caching of BRENDA API results including raw data and
pre-calculated statistics.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from .base_cache_manager import BaseCacheManager


class BRENDACacheManager(BaseCacheManager):
    """Cache manager for BRENDA API results.
    
    Leverages existing BRENDA tables in HeuristicDatabase:
    - brenda_raw_data: Individual parameter measurements
    - brenda_statistics: Aggregated statistics (mean, median, etc.)
    
    Attributes:
        db: HeuristicDatabase instance
    """
    
    def __init__(self, database):
        """Initialize BRENDA cache manager.
        
        Args:
            database: HeuristicDatabase instance
        """
        super().__init__(database, 'BRENDA')
    
    def build_query_key(self, 
                       ec_number: str,
                       parameter_type: str,
                       organism: Optional[str] = None,
                       substrate: Optional[str] = None) -> str:
        """Build unique query key for BRENDA query.
        
        Args:
            ec_number: EC number (e.g., '2.7.1.1')
            parameter_type: 'Km', 'Kcat', 'Ki', or 'Vmax'
            organism: Organism name (optional)
            substrate: Substrate name (optional)
        
        Returns:
            Unique query key
        """
        org_part = organism if organism else 'all'
        sub_part = substrate if substrate else 'all'
        return f"brenda|{ec_number}|{parameter_type}|{org_part}|{sub_part}"
    
    def get_cached_result(self, query_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached BRENDA statistics.
        
        Args:
            query_key: Unique identifier for the query
        
        Returns:
            Cached statistics dict or None if not found
        """
        # Parse query key
        parts = query_key.split('|')
        if len(parts) < 3:
            return None
        
        ec_number = parts[1]
        parameter_type = parts[2]
        organism = parts[3] if len(parts) > 3 and parts[3] != 'all' else None
        substrate = parts[4] if len(parts) > 4 and parts[4] != 'all' else None
        
        # Use existing DB method
        stats = self.db.get_brenda_statistics(
            ec_number=ec_number,
            parameter_type=parameter_type,
            organism=organism,
            substrate=substrate
        )
        
        return stats
    
    def store_result(self, query_key: str, result: Dict[str, Any]) -> bool:
        """Store BRENDA result in cache.
        
        This method stores raw BRENDA data and calculates statistics.
        
        Args:
            query_key: Unique identifier for the query
            result: Result dict with 'raw_data' list
        
        Returns:
            True if stored successfully
        """
        try:
            # Parse query key
            parts = query_key.split('|')
            if len(parts) < 3:
                return False
            
            ec_number = parts[1]
            parameter_type = parts[2]
            organism = parts[3] if len(parts) > 3 and parts[3] != 'all' else None
            substrate = parts[4] if len(parts) > 4 and parts[4] != 'all' else None
            
            # Store raw data
            raw_data = result.get('raw_data', [])
            if raw_data:
                inserted = self.db.insert_brenda_raw_data(raw_data)
                self.logger.debug(f"Stored {inserted} BRENDA raw records")
            
            # Calculate and cache statistics
            stats = self.db.calculate_brenda_statistics(
                ec_number=ec_number,
                parameter_type=parameter_type,
                organism=organism,
                substrate=substrate
            )
            
            if stats:
                self.logger.debug(f"Calculated statistics for {query_key}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to store BRENDA result: {e}")
            return False
    
    def invalidate_cache(self, query_key: Optional[str] = None):
        """Invalidate BRENDA cache entries.
        
        Args:
            query_key: Specific key to invalidate, or None for all
        """
        super().invalidate_cache(query_key)
        
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            if query_key:
                # Parse query key and delete specific statistics
                parts = query_key.split('|')
                if len(parts) >= 3:
                    ec_number = parts[1]
                    parameter_type = parts[2]
                    cursor.execute("""
                        DELETE FROM brenda_statistics
                        WHERE ec_number = ? AND parameter_type = ?
                    """, (ec_number, parameter_type))
            else:
                # Clear all statistics (keep raw data for recalculation)
                cursor.execute("DELETE FROM brenda_statistics")
            
            deleted = cursor.rowcount
            conn.commit()
            self.logger.info(f"Invalidated {deleted} BRENDA statistics entries")
    
    def store_raw_data_batch(self, raw_data_list: List[Dict[str, Any]]) -> int:
        """Bulk store BRENDA raw data.
        
        Convenience method for storing multiple BRENDA records at once.
        
        Args:
            raw_data_list: List of BRENDA result dicts
        
        Returns:
            Number of records inserted
        """
        return self.db.insert_brenda_raw_data(raw_data_list)
    
    def query_raw_data(self,
                      ec_number: str,
                      parameter_type: str,
                      organism: Optional[str] = None,
                      min_quality: float = 0.0) -> List[Dict[str, Any]]:
        """Query cached BRENDA raw data.
        
        Args:
            ec_number: EC number
            parameter_type: Parameter type
            organism: Optional organism filter
            min_quality: Minimum quality score
        
        Returns:
            List of raw BRENDA records
        """
        return self.db.query_brenda_data(
            ec_number=ec_number,
            parameter_type=parameter_type,
            organism=organism,
            min_quality=min_quality
        )
    
    def get_cache_summary(self) -> Dict[str, Any]:
        """Get summary of cached BRENDA data.
        
        Returns:
            Dict with cache statistics
        """
        summary = self.db.get_brenda_summary()
        summary.update(self.get_statistics())
        return summary
