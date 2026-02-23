"""
Model Repository

Repository pattern implementation for Petri net model persistence and retrieval.
Provides caching, querying, and centralized data access for DocumentModel objects.

Part of Phase 3.2: Repository Pattern Implementation.
"""

import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from shypn.data.canvas.document_model import DocumentModel
from shypn.repositories.base_repository import (
    CachedRepository,
    EntityNotFoundError,
    RepositoryIOError
)
from shypn.events.event_bus import EventBus


class ModelQuery:
    """Fluent query builder for model search.
    
    Provides chainable methods for building complex queries to filter models
    by various criteria. Queries are executed lazily when matches() is called.
    
    Example:
        query = (ModelQuery()
                 .with_name_pattern("MAPK.*")
                 .with_place_count(min_count=5, max_count=50)
                 .with_metadata(source="KEGG"))
        
        matching_models = repository.search(query)
    """
    
    def __init__(self):
        """Initialize empty query."""
        self._name_pattern: Optional[str] = None
        self._min_places: Optional[int] = None
        self._max_places: Optional[int] = None
        self._min_transitions: Optional[int] = None
        self._max_transitions: Optional[int] = None
        self._has_modules: Optional[bool] = None
        self._module_count: Optional[int] = None
        self._has_signal_places: Optional[bool] = None
        self._metadata_filters: Dict[str, Any] = {}
    
    def with_name_pattern(self, pattern: str) -> 'ModelQuery':
        """Filter by model name pattern (regex).
        
        Args:
            pattern: Regular expression pattern to match against model names
        
        Returns:
            self for method chaining
        
        Example:
            >>> query.with_name_pattern("MAPK|ERK")  # Match MAPK or ERK
            >>> query.with_name_pattern("^glycolysis")  # Starts with glycolysis
        """
        self._name_pattern = pattern
        return self
    
    def with_place_count(
        self,
        min_count: Optional[int] = None,
        max_count: Optional[int] = None
    ) -> 'ModelQuery':
        """Filter by number of places.
        
        Args:
            min_count: Minimum number of places (inclusive)
            max_count: Maximum number of places (inclusive)
        
        Returns:
            self for method chaining
        
        Example:
            >>> query.with_place_count(min_count=10)  # At least 10 places
            >>> query.with_place_count(min_count=5, max_count=20)  # 5-20 places
        """
        self._min_places = min_count
        self._max_places = max_count
        return self
    
    def with_transition_count(
        self,
        min_count: Optional[int] = None,
        max_count: Optional[int] = None
    ) -> 'ModelQuery':
        """Filter by number of transitions.
        
        Args:
            min_count: Minimum number of transitions (inclusive)
            max_count: Maximum number of transitions (inclusive)
        
        Returns:
            self for method chaining
        
        Example:
            >>> query.with_transition_count(min_count=5)
        """
        self._min_transitions = min_count
        self._max_transitions = max_count
        return self
    
    def with_modules(self, has_modules: bool = True) -> 'ModelQuery':
        """Filter by presence of modules.
        
        Args:
            has_modules: True to match models with modules, False for models without
        
        Returns:
            self for method chaining
        
        Example:
            >>> query.with_modules(True)  # Only modular models
        """
        self._has_modules = has_modules
        return self
    
    def with_module_count(self, count: int) -> 'ModelQuery':
        """Filter by exact module count.
        
        Args:
            count: Exact number of modules required
        
        Returns:
            self for method chaining
        
        Example:
            >>> query.with_module_count(3)  # Models with exactly 3 modules
        """
        self._module_count = count
        return self
    
    def with_signal_places(self, has_signal_places: bool = True) -> 'ModelQuery':
        """Filter by presence of signal places (SHPN models).
        
        Args:
            has_signal_places: True to match SHPN models with signal places
        
        Returns:
            self for method chaining
        
        Example:
            >>> query.with_signal_places(True)  # Only SHPN models
        """
        self._has_signal_places = has_signal_places
        return self
    
    def with_metadata(self, **kwargs) -> 'ModelQuery':
        """Filter by metadata fields.
        
        Args:
            **kwargs: Metadata key-value pairs to match
        
        Returns:
            self for method chaining
        
        Example:
            >>> query.with_metadata(source="KEGG", organism="hsa")
            >>> query.with_metadata(model_type="SHPN")
        """
        self._metadata_filters.update(kwargs)
        return self
    
    def matches(self, model: DocumentModel) -> bool:
        """Check if model matches all query criteria.
        
        Args:
            model: DocumentModel to test
        
        Returns:
            True if model matches all criteria, False otherwise
        """
        # Name pattern
        if self._name_pattern:
            # Get model name from metadata (if available)
            model_name = model.metadata.get('name', '')
            if not re.search(self._name_pattern, model_name, re.IGNORECASE):
                return False
        
        # Place count
        place_count = len(model.places)
        if self._min_places is not None and place_count < self._min_places:
            return False
        if self._max_places is not None and place_count > self._max_places:
            return False
        
        # Transition count
        transition_count = len(model.transitions)
        if self._min_transitions is not None and transition_count < self._min_transitions:
            return False
        if self._max_transitions is not None and transition_count > self._max_transitions:
            return False
        
        # Modules
        module_count = len(model.modules)
        if self._has_modules is not None:
            has_modules = module_count > 0
            if has_modules != self._has_modules:
                return False
        
        if self._module_count is not None:
            if module_count != self._module_count:
                return False
        
        # Signal places (SHPN)
        if self._has_signal_places is not None:
            has_signal = any(
                getattr(place, 'is_signal_place', False)
                for place in model.places
            )
            if has_signal != self._has_signal_places:
                return False
        
        # Metadata filters
        for key, value in self._metadata_filters.items():
            if model.metadata.get(key) != value:
                return False
        
        return True


class ModelRepository(CachedRepository[DocumentModel]):
    """Repository for Petri net model persistence and retrieval.
    
    Provides centralized model data access with:
    - File-based persistence (.shy JSON format)
    - LRU caching for frequently accessed models
    - Query interface for model search
    - Workspace management
    
    The repository wraps DocumentModel's native save/load but adds caching,
    query capabilities, and consistent error handling.
    
    Example:
        # Create repository for workspace
        repo = ModelRepository("/path/to/workspace")
        
        # Load model (cached)
        model = repo.get_by_id("glycolysis_v1")
        
        # Search models
        query = ModelQuery().with_place_count(min_count=10)
        large_models = repo.search(query)
        
        # Save model
        repo.save(model)
    """
    
    def __init__(self, workspace_path: str, cache_size: int = 50):
        """Initialize model repository.
        
        Args:
            workspace_path: Path to workspace directory containing .shy files
            cache_size: Maximum number of models to cache (default: 50)
        
        Raises:
            ValueError: If workspace_path is invalid
        """
        super().__init__(cache_size)
        
        self._workspace_path = Path(workspace_path)
        if not self._workspace_path.exists():
            raise ValueError(f"Workspace path does not exist: {workspace_path}")
        
        if not self._workspace_path.is_dir():
            raise ValueError(f"Workspace path is not a directory: {workspace_path}")
        
        # Subscribe to file.saved event for automatic cache invalidation
        EventBus.subscribe('file.saved', self._on_file_saved)
    
    def _on_file_saved(self, event_data: Dict[str, Any]) -> None:
        """Handle file.saved event to invalidate cache for externally modified models.
        
        Args:
            event_data: Event data containing 'filepath', 'document', 'timestamp'
        """
        filepath = event_data.get('filepath')
        if not filepath:
            return
        
        # Convert filepath to model_id
        file_path = Path(filepath)
        
        # Only process .shy files in our workspace
        if file_path.suffix != '.shy':
            return
        
        # Check if this file is in our workspace
        try:
            relative = file_path.relative_to(self._workspace_path)
            model_id = file_path.stem
        except (ValueError, Exception):
            # File is not in our workspace, ignore
            return
        
        # Invalidate cache for this model_id if it exists
        if model_id in self._cache:
            print(f"🔄 Model '{model_id}' was saved - invalidating cache")
            self._cache.pop(model_id, None)
            if model_id in self._access_order:
                self._access_order.remove(model_id)
    
    # ===== Public API =====
    
    def get_by_id(self, entity_id: str) -> Optional[DocumentModel]:
        """Get model by ID (with event-driven cache invalidation).
        
        Cache is automatically invalidated when files are saved via EventBus.
        No file system polling - pure event-driven architecture.
        
        Args:
            entity_id: Model ID (filename without .shy extension)
        
        Returns:
            DocumentModel if found, None otherwise
        """
        # Use parent's caching logic - cache invalidation happens via events
        return super().get_by_id(entity_id)
    
    def get_by_name(self, name: str) -> Optional[DocumentModel]:
        """Get model by name (searches metadata).
        
        Args:
            name: Model name to search for
        
        Returns:
            DocumentModel if found, None otherwise
        
        Note:
            This method searches all models in workspace, which may be slow
            for large workspaces. Consider using search() with caching.
        """
        for model_id in self._list_model_ids():
            model = self.get_by_id(model_id)
            if model and model.metadata.get('name') == name:
                return model
        return None
    
    def get_all(self) -> List[DocumentModel]:
        """Get all models in workspace.
        
        Returns:
            List of all DocumentModel objects (may be large)
        
        Note:
            For large workspaces, consider using search() with filters
            or list_model_ids() to avoid loading all models at once.
        """
        models = []
        for model_id in self._list_model_ids():
            model = self.get_by_id(model_id)
            if model:
                models.append(model)
        return models
    
    def count(self) -> int:
        """Get total number of models in workspace.
        
        Returns:
            Count of .shy files in workspace
        """
        return len(self._list_model_ids())
    
    def search(self, query: ModelQuery) -> List[DocumentModel]:
        """Search models by query criteria.
        
        Args:
            query: ModelQuery with filter criteria
        
        Returns:
            List of matching DocumentModel objects
        
        Example:
            >>> query = ModelQuery().with_place_count(min_count=10)
            >>> large_models = repo.search(query)
        """
        results = []
        for model_id in self._list_model_ids():
            model = self.get_by_id(model_id)
            if model and query.matches(model):
                results.append(model)
        return results
    
    def list_model_ids(self) -> List[str]:
        """Get list of all model IDs in workspace.
        
        Returns:
            List of model IDs (filenames without .shy extension)
        
        Example:
            >>> ids = repo.list_model_ids()
            >>> ['glycolysis_v1', 'mapk_cascade', 'tca_cycle']
        """
        return self._list_model_ids()
    
    # ===== CachedRepository Implementation =====
    
    def save(self, entity: DocumentModel) -> bool:
        """Save model (override to handle metadata['id'] and update mtime tracking).
        
        Args:
            entity: DocumentModel to save
        
        Returns:
            True if save succeeded, False otherwise
        
        Raises:
            ValueError: If model has no ID in metadata
        """
        # Extract entity ID from metadata
        entity_id = entity.metadata.get('id')
        if entity_id is None:
            raise ValueError("Model must have 'id' in metadata")
        
        # Save to storage
        success = self._save_to_storage(entity_id, entity)
        
        # Update cache if save succeeded
        if success:
            self._add_to_cache(entity_id, entity)
        
        return success
    
    def delete(self, entity_id: str) -> bool:
        """Delete model.
        
        Args:
            entity_id: Model ID to delete
        
        Returns:
            True if deletion succeeded, False otherwise
        """
        # Use parent delete (handles storage and cache)
        return super().delete(entity_id)
    
    def clear_cache(self):
        """Clear all cached models."""
        super().clear_cache()
        print("✅ Model cache cleared (event-driven invalidation active)")
    
    def _load_from_storage(self, entity_id: str) -> Optional[DocumentModel]:
        """Load model from .shy file.
        
        Args:
            entity_id: Model ID (filename without extension)
        
        Returns:
            DocumentModel if file exists and loads successfully, None otherwise
        """
        file_path = self._get_model_path(entity_id)
        
        if not file_path.exists():
            return None
        
        try:
            model = DocumentModel.load_from_file(str(file_path))
            # Store model ID in metadata for reference
            if 'id' not in model.metadata:
                model.metadata['id'] = entity_id
            return model
        except Exception as e:
            raise RepositoryIOError('load', f"Failed to load {file_path}: {e}")
    
    def _save_to_storage(self, entity_id: str, entity: DocumentModel) -> bool:
        """Save model to .shy file.
        
        Args:
            entity_id: Model ID (filename without extension)
            entity: DocumentModel to save
        
        Returns:
            True if save succeeded, False otherwise
        """
        file_path = self._get_model_path(entity_id)
        
        try:
            # Ensure model ID is stored in metadata
            entity.metadata['id'] = entity_id
            entity.save_to_file(str(file_path))
            return True
        except Exception as e:
            raise RepositoryIOError('save', f"Failed to save {file_path}: {e}")
    
    def _delete_from_storage(self, entity_id: str) -> bool:
        """Delete model .shy file.
        
        Args:
            entity_id: Model ID (filename without extension)
        
        Returns:
            True if deletion succeeded, False otherwise
        """
        file_path = self._get_model_path(entity_id)
        
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            return True
        except Exception as e:
            raise RepositoryIOError('delete', f"Failed to delete {file_path}: {e}")
    
    def _exists_in_storage(self, entity_id: str) -> bool:
        """Check if model .shy file exists.
        
        Args:
            entity_id: Model ID (filename without extension)
        
        Returns:
            True if file exists, False otherwise
        """
        file_path = self._get_model_path(entity_id)
        return file_path.exists() and file_path.is_file()
    
    # ===== Helper Methods =====
    
    def _get_model_path(self, model_id: str) -> Path:
        """Get file path for model.
        
        Args:
            model_id: Model ID
        
        Returns:
            Path to .shy file
        """
        return self._workspace_path / f"{model_id}.shy"
    
    def _list_model_ids(self) -> List[str]:
        """List all model IDs in workspace.
        
        Returns:
            List of model IDs (filenames without .shy extension)
        """
        return [
            path.stem
            for path in self._workspace_path.glob("*.shy")
            if path.is_file()
        ]
    
    # ===== Additional Features =====
    
    def import_model(self, source_path: str, model_id: Optional[str] = None) -> str:
        """Import model from external file.
        
        Args:
            source_path: Path to source .shy file
            model_id: Target model ID (default: use source filename)
        
        Returns:
            Imported model ID
        
        Raises:
            ValueError: If source file doesn't exist
            RepositoryIOError: If import fails
        """
        source = Path(source_path)
        if not source.exists():
            raise ValueError(f"Source file not found: {source_path}")
        
        # Determine target model ID
        if model_id is None:
            model_id = source.stem
        
        # Load model and save to workspace
        try:
            model = DocumentModel.load_from_file(str(source))
            model.metadata['id'] = model_id
            model.metadata['imported_from'] = str(source)
            self.save(model)
            return model_id
        except Exception as e:
            raise RepositoryIOError('import', f"Failed to import {source}: {e}")
    
    def export_model(self, model_id: str, target_path: str) -> bool:
        """Export model to external file.
        
        Args:
            model_id: Model ID to export
            target_path: Path to target .shy file
        
        Returns:
            True if export succeeded
        
        Raises:
            EntityNotFoundError: If model doesn't exist
            RepositoryIOError: If export fails
        """
        model = self.get_by_id(model_id)
        if model is None:
            raise EntityNotFoundError(model_id, "Model")
        
        try:
            target = Path(target_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            model.save_to_file(str(target))
            return True
        except Exception as e:
            raise RepositoryIOError('export', f"Failed to export to {target_path}: {e}")
    
    def get_workspace_path(self) -> Path:
        """Get workspace directory path.
        
        Returns:
            Path to workspace
        """
        return self._workspace_path
    
    def __repr__(self) -> str:
        """Get string representation for debugging."""
        return (f"ModelRepository(workspace={self._workspace_path}, "
                f"models={self.count()}, cache={len(self._cache)}/{self._cache_size})")
