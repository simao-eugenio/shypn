"""
Base Repository Abstract Class

Provides common repository interface and behavior for data access patterns.
Part of Phase 3.2: Repository Pattern Implementation.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List
from pathlib import Path


T = TypeVar('T')  # Entity type


class BaseRepository(ABC, Generic[T]):
    """Abstract base class for repository pattern.
    
    Repositories encapsulate data access logic, providing a clean interface
    for persistence operations. This base class defines the common contract
    that all repositories must implement.
    
    Type Parameters:
        T: The entity type managed by this repository
    
    Benefits:
        - Decouples business logic from storage implementation
        - Enables easy testing with mock repositories
        - Provides consistent API across different data sources
        - Allows caching and query optimization
    
    Example:
        class UserRepository(BaseRepository[User]):
            def get_by_id(self, id: str) -> Optional[User]:
                # Implementation...
                pass
    """
    
    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Retrieve entity by its unique identifier.
        
        Args:
            entity_id: Unique identifier for the entity
        
        Returns:
            Entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_all(self) -> List[T]:
        """Retrieve all entities.
        
        Returns:
            List of all entities (may be empty)
        """
        pass
    
    @abstractmethod
    def save(self, entity: T) -> bool:
        """Save entity (create or update).
        
        Args:
            entity: Entity to save
        
        Returns:
            True if save succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete entity by identifier.
        
        Args:
            entity_id: Unique identifier for entity to delete
        
        Returns:
            True if deletion succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """Check if entity exists.
        
        Args:
            entity_id: Unique identifier to check
        
        Returns:
            True if entity exists, False otherwise
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Get total number of entities.
        
        Returns:
            Count of all entities
        """
        pass


class CachedRepository(BaseRepository[T]):
    """Base class for repositories with caching support.
    
    Provides LRU (Least Recently Used) cache management for frequently
    accessed entities. Subclasses only need to implement disk I/O methods.
    
    Attributes:
        _cache: Dictionary mapping entity IDs to cached entities
        _cache_size: Maximum number of entities to cache
        _cache_hits: Number of successful cache hits (for metrics)
        _cache_misses: Number of cache misses (for metrics)
    """
    
    def __init__(self, cache_size: int = 50):
        """Initialize cached repository.
        
        Args:
            cache_size: Maximum number of entities to cache (default: 50)
        """
        self._cache: dict[str, T] = {}
        self._cache_size = cache_size
        self._cache_hits = 0
        self._cache_misses = 0
        self._access_order: List[str] = []  # Track access for LRU
    
    @abstractmethod
    def _load_from_storage(self, entity_id: str) -> Optional[T]:
        """Load entity from underlying storage.
        
        Args:
            entity_id: Entity identifier
        
        Returns:
            Entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def _save_to_storage(self, entity_id: str, entity: T) -> bool:
        """Save entity to underlying storage.
        
        Args:
            entity_id: Entity identifier
            entity: Entity to save
        
        Returns:
            True if save succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    def _delete_from_storage(self, entity_id: str) -> bool:
        """Delete entity from underlying storage.
        
        Args:
            entity_id: Entity identifier
        
        Returns:
            True if deletion succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    def _exists_in_storage(self, entity_id: str) -> bool:
        """Check if entity exists in storage.
        
        Args:
            entity_id: Entity identifier
        
        Returns:
            True if entity exists, False otherwise
        """
        pass
    
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID (with caching).
        
        Args:
            entity_id: Entity identifier
        
        Returns:
            Entity if found (from cache or storage), None otherwise
        """
        # Check cache
        if entity_id in self._cache:
            self._cache_hits += 1
            self._update_access_order(entity_id)
            return self._cache[entity_id]
        
        # Load from storage
        self._cache_misses += 1
        entity = self._load_from_storage(entity_id)
        
        if entity is not None:
            self._add_to_cache(entity_id, entity)
        
        return entity
    
    def save(self, entity: T) -> bool:
        """Save entity (to both cache and storage).
        
        Args:
            entity: Entity to save
        
        Returns:
            True if save succeeded, False otherwise
        """
        # Extract entity ID (assumes entity has 'id' attribute)
        entity_id = getattr(entity, 'id', None)
        if entity_id is None:
            raise ValueError("Entity must have 'id' attribute")
        
        # Save to storage
        success = self._save_to_storage(entity_id, entity)
        
        # Update cache if save succeeded
        if success:
            self._add_to_cache(entity_id, entity)
        
        return success
    
    def delete(self, entity_id: str) -> bool:
        """Delete entity (from both cache and storage).
        
        Args:
            entity_id: Entity identifier
        
        Returns:
            True if deletion succeeded, False otherwise
        """
        # Delete from storage
        success = self._delete_from_storage(entity_id)
        
        # Remove from cache
        if success:
            self._cache.pop(entity_id, None)
            if entity_id in self._access_order:
                self._access_order.remove(entity_id)
        
        return success
    
    def exists(self, entity_id: str) -> bool:
        """Check if entity exists (checks cache first).
        
        Args:
            entity_id: Entity identifier
        
        Returns:
            True if entity exists, False otherwise
        """
        # Check cache first
        if entity_id in self._cache:
            return True
        
        # Check storage
        return self._exists_in_storage(entity_id)
    
    def clear_cache(self):
        """Clear all cached entities."""
        self._cache.clear()
        self._access_order.clear()
    
    def get_cache_stats(self) -> dict:
        """Get cache performance statistics.
        
        Returns:
            Dictionary with cache metrics
        """
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0.0
        
        return {
            'size': len(self._cache),
            'max_size': self._cache_size,
            'hits': self._cache_hits,
            'misses': self._cache_misses,
            'hit_rate': hit_rate
        }
    
    def _add_to_cache(self, entity_id: str, entity: T):
        """Add entity to cache with LRU eviction.
        
        Args:
            entity_id: Entity identifier
            entity: Entity to cache
        """
        # Evict if cache full
        if len(self._cache) >= self._cache_size and entity_id not in self._cache:
            # Remove least recently used (first in access order)
            if self._access_order:
                lru_id = self._access_order.pop(0)
                self._cache.pop(lru_id, None)
        
        # Add/update cache
        self._cache[entity_id] = entity
        self._update_access_order(entity_id)
    
    def _update_access_order(self, entity_id: str):
        """Update LRU access order.
        
        Args:
            entity_id: Entity that was accessed
        """
        # Remove from current position
        if entity_id in self._access_order:
            self._access_order.remove(entity_id)
        
        # Add to end (most recently used)
        self._access_order.append(entity_id)


class RepositoryError(Exception):
    """Base exception for repository operations."""
    pass


class EntityNotFoundError(RepositoryError):
    """Raised when entity cannot be found."""
    
    def __init__(self, entity_id: str, entity_type: str = "Entity"):
        self.entity_id = entity_id
        self.entity_type = entity_type
        super().__init__(f"{entity_type} not found: {entity_id}")


class RepositoryIOError(RepositoryError):
    """Raised when I/O operation fails."""
    
    def __init__(self, operation: str, reason: str):
        self.operation = operation
        self.reason = reason
        super().__init__(f"{operation} failed: {reason}")
