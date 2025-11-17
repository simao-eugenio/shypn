#!/usr/bin/env python3
"""Base cache manager for API results.

Abstract base class that defines the interface for caching external API results.
Subclasses implement source-specific caching logic for SABIO-RK, BRENDA, etc.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime


class BaseCacheManager(ABC):
    """Abstract base class for API result caching.
    
    Provides common caching operations while allowing subclasses to implement
    source-specific storage and retrieval logic.
    
    Attributes:
        db: HeuristicDatabase instance
        logger: Logger instance
        source_name: Name of the data source (e.g., 'SABIO-RK', 'BRENDA')
    """
    
    def __init__(self, database, source_name: str):
        """Initialize base cache manager.
        
        Args:
            database: HeuristicDatabase instance
            source_name: Name of the data source
        """
        self.db = database
        self.source_name = source_name
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self._cache_hits = 0
        self._cache_misses = 0
    
    @abstractmethod
    def get_cached_result(self, query_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached result for a query.
        
        Args:
            query_key: Unique identifier for the query
        
        Returns:
            Cached result dict or None if not found
        """
        pass
    
    @abstractmethod
    def store_result(self, query_key: str, result: Dict[str, Any]) -> bool:
        """Store query result in cache.
        
        Args:
            query_key: Unique identifier for the query
            result: Result data to cache
        
        Returns:
            True if stored successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def build_query_key(self, **kwargs) -> str:
        """Build unique query key from parameters.
        
        Args:
            **kwargs: Query parameters
        
        Returns:
            Unique query key string
        """
        pass
    
    def query_with_cache(self, query_func, query_key: str, *args, **kwargs) -> Optional[Dict[str, Any]]:
        """Execute query with caching support.
        
        Checks cache first, executes query on miss, stores result.
        
        Args:
            query_func: Function to execute on cache miss
            query_key: Unique identifier for the query
            *args: Positional arguments for query_func
            **kwargs: Keyword arguments for query_func
        
        Returns:
            Query result (from cache or fresh)
        """
        # Try cache first
        cached = self.get_cached_result(query_key)
        if cached is not None:
            self._cache_hits += 1
            self.logger.info(f"[{self.source_name}] Cache hit: {query_key}")
            return cached
        
        # Cache miss - execute query
        self._cache_misses += 1
        self.logger.info(f"[{self.source_name}] Cache miss: {query_key}")
        
        result = query_func(*args, **kwargs)
        
        # Store in cache
        if result is not None:
            self.store_result(query_key, result)
        
        return result
    
    def invalidate_cache(self, query_key: Optional[str] = None):
        """Invalidate cached entries.
        
        Args:
            query_key: Specific key to invalidate, or None for all
        """
        if query_key:
            self.logger.info(f"[{self.source_name}] Invalidating cache: {query_key}")
        else:
            self.logger.info(f"[{self.source_name}] Invalidating all cache")
        # Subclasses implement actual deletion
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dict with hits, misses, hit rate
        """
        total = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total * 100) if total > 0 else 0.0
        
        return {
            'source': self.source_name,
            'hits': self._cache_hits,
            'misses': self._cache_misses,
            'total_queries': total,
            'hit_rate_percent': round(hit_rate, 2)
        }
    
    def reset_statistics(self):
        """Reset cache statistics counters."""
        self._cache_hits = 0
        self._cache_misses = 0
        self.logger.debug(f"[{self.source_name}] Statistics reset")
