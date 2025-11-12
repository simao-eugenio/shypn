"""Data cache for efficient repeated queries.

This module provides caching for KB and simulation data queries
to avoid repeated lookups. Cache can be invalidated when model changes.
"""
from typing import Optional, Set, List, Dict, Any
from dataclasses import dataclass, field
from time import time


@dataclass
class CacheEntry:
    """Single cache entry with expiration."""
    value: Any
    timestamp: float
    ttl: Optional[float] = None  # Time to live in seconds
    
    def is_expired(self) -> bool:
        """Check if entry has expired.
        
        Returns:
            True if entry is expired
        """
        if self.ttl is None:
            return False
        
        return (time() - self.timestamp) > self.ttl


class DataCache:
    """Cache for KB and simulation data queries."""
    
    def __init__(self, default_ttl: Optional[float] = None):
        """Initialize data cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (None = no expiration)
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            self._misses += 1
            return None
        
        entry = self._cache[key]
        
        if entry.is_expired():
            del self._cache[key]
            self._misses += 1
            return None
        
        self._hits += 1
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (overrides default)
        """
        if ttl is None:
            ttl = self.default_ttl
        
        self._cache[key] = CacheEntry(
            value=value,
            timestamp=time(),
            ttl=ttl
        )
    
    def invalidate(self, key: str):
        """Remove entry from cache.
        
        Args:
            key: Cache key to invalidate
        """
        if key in self._cache:
            del self._cache[key]
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern.
        
        Args:
            pattern: Pattern to match (supports * wildcard)
        """
        if '*' not in pattern:
            # Exact match
            self.invalidate(pattern)
            return
        
        # Pattern matching
        prefix = pattern.split('*')[0]
        to_remove = [
            key for key in self._cache.keys()
            if key.startswith(prefix)
        ]
        
        for key in to_remove:
            del self._cache[key]
    
    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def size(self) -> int:
        """Get number of cached entries.
        
        Returns:
            Cache size
        """
        return len(self._cache)
    
    def hit_rate(self) -> float:
        """Get cache hit rate.
        
        Returns:
            Hit rate (0.0 to 1.0)
        """
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        
        return self._hits / total
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with hits, misses, size, hit_rate
        """
        return {
            'hits': self._hits,
            'misses': self._misses,
            'size': self.size(),
            'hit_rate': self.hit_rate()
        }
    
    def cleanup_expired(self):
        """Remove all expired entries."""
        to_remove = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        
        for key in to_remove:
            del self._cache[key]


class CachedDataPuller:
    """Data puller with caching layer."""
    
    def __init__(self, data_puller, cache: Optional[DataCache] = None):
        """Initialize cached data puller.
        
        Args:
            data_puller: Underlying DataPuller instance
            cache: Optional cache instance (creates new if None)
        """
        self.puller = data_puller
        self.cache = cache or DataCache(default_ttl=60.0)  # 60 second default
    
    def get_transition(self, transition_id: str):
        """Get transition with caching.
        
        Args:
            transition_id: Transition identifier
            
        Returns:
            Transition object or None
        """
        key = f'transition:{transition_id}'
        cached = self.cache.get(key)
        
        if cached is not None:
            return cached
        
        result = self.puller.get_transition(transition_id)
        if result is not None:
            self.cache.set(key, result, ttl=None)  # KB data doesn't expire
        
        return result
    
    def get_place(self, place_id: str):
        """Get place with caching.
        
        Args:
            place_id: Place identifier
            
        Returns:
            Place object or None
        """
        key = f'place:{place_id}'
        cached = self.cache.get(key)
        
        if cached is not None:
            return cached
        
        result = self.puller.get_place(place_id)
        if result is not None:
            self.cache.set(key, result, ttl=None)  # KB data doesn't expire
        
        return result
    
    def get_arc(self, arc_id: str):
        """Get arc with caching.
        
        Args:
            arc_id: Arc identifier
            
        Returns:
            Arc object or None
        """
        key = f'arc:{arc_id}'
        cached = self.cache.get(key)
        
        if cached is not None:
            return cached
        
        result = self.puller.get_arc(arc_id)
        if result is not None:
            self.cache.set(key, result, ttl=None)  # KB data doesn't expire
        
        return result
    
    def get_input_arcs(self, transition_id: str) -> List:
        """Get input arcs with caching.
        
        Args:
            transition_id: Transition identifier
            
        Returns:
            List of input arc objects
        """
        key = f'input_arcs:{transition_id}'
        cached = self.cache.get(key)
        
        if cached is not None:
            return cached
        
        result = self.puller.get_input_arcs(transition_id)
        self.cache.set(key, result, ttl=None)
        
        return result
    
    def get_output_arcs(self, transition_id: str) -> List:
        """Get output arcs with caching.
        
        Args:
            transition_id: Transition identifier
            
        Returns:
            List of output arc objects
        """
        key = f'output_arcs:{transition_id}'
        cached = self.cache.get(key)
        
        if cached is not None:
            return cached
        
        result = self.puller.get_output_arcs(transition_id)
        self.cache.set(key, result, ttl=None)
        
        return result
    
    def get_current_tokens(self, place_id: str) -> Optional[float]:
        """Get current tokens with short TTL caching.
        
        Args:
            place_id: Place identifier
            
        Returns:
            Token count or None
        """
        key = f'tokens:{place_id}'
        cached = self.cache.get(key)
        
        if cached is not None:
            return cached
        
        result = self.puller.get_current_tokens(place_id)
        if result is not None:
            self.cache.set(key, result, ttl=5.0)  # Short TTL for simulation data
        
        return result
    
    def invalidate_model_changes(self):
        """Invalidate cache after model changes.
        
        Call this when the model structure changes (arcs, transitions, places added/removed).
        """
        self.cache.invalidate_pattern('transition:*')
        self.cache.invalidate_pattern('place:*')
        self.cache.invalidate_pattern('arc:*')
        self.cache.invalidate_pattern('input_arcs:*')
        self.cache.invalidate_pattern('output_arcs:*')
    
    def invalidate_simulation_state(self):
        """Invalidate cache for simulation state.
        
        Call this when simulation runs or resets.
        """
        self.cache.invalidate_pattern('tokens:*')
        self.cache.invalidate_pattern('firings:*')
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Cache stats dictionary
        """
        return self.cache.stats()
