"""
Tests for ModelRepository

Comprehensive test suite for model repository pattern including caching,
querying, and file operations.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from shypn.repositories import (
    ModelRepository,
    ModelQuery,
    EntityNotFoundError,
    RepositoryIOError
)
from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition


class TestModelRepositoryBasics:
    """Tests for basic repository operations."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def repository(self, temp_workspace):
        """Create repository with temporary workspace."""
        return ModelRepository(temp_workspace, cache_size=10)
    
    @pytest.fixture
    def sample_model(self):
        """Create sample DocumentModel."""
        model = DocumentModel()
        model.metadata['name'] = 'test_model'
        model.metadata['id'] = 'test_id'
        
        # Add some places
        p1 = model.create_place(100, 100, "P1")
        p2 = model.create_place(200, 100, "P2")
        
        # Add transition
        t1 = model.create_transition(150, 150, "T1")
        
        return model
    
    def test_repository_initialization(self, temp_workspace):
        """Test repository initializes correctly."""
        repo = ModelRepository(temp_workspace)
        
        assert repo.get_workspace_path() == Path(temp_workspace)
        assert repo.count() == 0
    
    def test_invalid_workspace_raises_error(self):
        """Test initialization with invalid workspace raises error."""
        with pytest.raises(ValueError, match="does not exist"):
            ModelRepository("/nonexistent/path")
    
    def test_save_and_load_model(self, repository, sample_model, temp_workspace):
        """Test saving and loading a model."""
        model_id = "test_model_1"
        sample_model.metadata['id'] = model_id
        
        # Save model
        success = repository.save(sample_model)
        assert success is True
        
        # Verify file exists
        expected_file = Path(temp_workspace) / f"{model_id}.shy"
        assert expected_file.exists()
        
        # Load model
        loaded_model = repository.get_by_id(model_id)
        assert loaded_model is not None
        assert loaded_model.metadata['id'] == model_id
        assert len(loaded_model.places) == 2
        assert len(loaded_model.transitions) == 1
    
    def test_get_nonexistent_model_returns_none(self, repository):
        """Test getting nonexistent model returns None."""
        model = repository.get_by_id("nonexistent")
        assert model is None
    
    def test_delete_model(self, repository, sample_model):
        """Test deleting a model."""
        model_id = "test_delete"
        sample_model.metadata['id'] = model_id
        
        # Save and verify
        repository.save(sample_model)
        assert repository.exists(model_id) is True
        
        # Delete
        success = repository.delete(model_id)
        assert success is True
        assert repository.exists(model_id) is False
    
    def test_delete_nonexistent_model(self, repository):
        """Test deleting nonexistent model returns False."""
        success = repository.delete("nonexistent")
        assert success is False
    
    def test_exists_method(self, repository, sample_model):
        """Test exists method."""
        model_id = "test_exists"
        sample_model.metadata['id'] = model_id
        
        # Before save
        assert repository.exists(model_id) is False
        
        # After save
        repository.save(sample_model)
        assert repository.exists(model_id) is True
    
    def test_count_models(self, repository, sample_model):
        """Test counting models in workspace."""
        assert repository.count() == 0
        
        # Save 3 models
        for i in range(3):
            model = DocumentModel()
            model.metadata['id'] = f"model_{i}"
            repository.save(model)
        
        assert repository.count() == 3
    
    def test_list_model_ids(self, repository, sample_model):
        """Test listing all model IDs."""
        # Save multiple models
        ids = ['model_a', 'model_b', 'model_c']
        for model_id in ids:
            model = DocumentModel()
            model.metadata['id'] = model_id
            repository.save(model)
        
        listed_ids = repository.list_model_ids()
        assert set(listed_ids) == set(ids)
    
    def test_get_all_models(self, repository):
        """Test getting all models."""
        # Save multiple models
        for i in range(3):
            model = DocumentModel()
            model.metadata['id'] = f"model_{i}"
            model.metadata['name'] = f"Model {i}"
            repository.save(model)
        
        all_models = repository.get_all()
        assert len(all_models) == 3
        assert all(isinstance(m, DocumentModel) for m in all_models)
    
    def test_get_by_name(self, repository, sample_model):
        """Test getting model by name."""
        sample_model.metadata['id'] = 'test_id'
        sample_model.metadata['name'] = 'UniqueModel'
        repository.save(sample_model)
        
        model = repository.get_by_name('UniqueModel')
        assert model is not None
        assert model.metadata['name'] == 'UniqueModel'
    
    def test_get_by_name_not_found(self, repository):
        """Test get_by_name returns None for nonexistent name."""
        model = repository.get_by_name('Nonexistent')
        assert model is None


class TestModelRepositoryCaching:
    """Tests for repository caching behavior."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def repository(self, temp_workspace):
        """Create repository with small cache."""
        return ModelRepository(temp_workspace, cache_size=3)
    
    def test_cache_hit_on_second_load(self, repository):
        """Test second load hits cache."""
        # Create and save model
        model = DocumentModel()
        model.metadata['id'] = 'cached_model'
        repository.save(model)
        
        # Clear cache stats
        repository._cache_hits = 0
        repository._cache_misses = 0
        
        # First load (cache miss)
        model1 = repository.get_by_id('cached_model')
        assert repository._cache_misses == 0  # Already cached from save
        assert repository._cache_hits == 1
        
        # Second load (cache hit)
        model2 = repository.get_by_id('cached_model')
        assert repository._cache_hits == 2
        assert model1 is model2  # Same instance
    
    def test_lru_eviction(self, repository):
        """Test LRU cache eviction."""
        # Save 5 models (cache size = 3)
        for i in range(5):
            model = DocumentModel()
            model.metadata['id'] = f"model_{i}"
            repository.save(model)
        
        # Cache should only have 3 models
        assert len(repository._cache) <= 3
    
    def test_clear_cache(self, repository):
        """Test clearing cache."""
        # Save and load model
        model = DocumentModel()
        model.metadata['id'] = 'test'
        repository.save(model)
        repository.get_by_id('test')
        
        assert len(repository._cache) > 0
        
        # Clear cache
        repository.clear_cache()
        assert len(repository._cache) == 0
    
    def test_cache_stats(self, repository):
        """Test cache statistics."""
        # Initial stats
        stats = repository.get_cache_stats()
        assert stats['size'] == 0
        assert stats['max_size'] == 3
        
        # Save and load models
        for i in range(2):
            model = DocumentModel()
            model.metadata['id'] = f"model_{i}"
            repository.save(model)
        
        # Check stats
        stats = repository.get_cache_stats()
        assert stats['size'] == 2
        assert stats['hits'] >= 0
        assert stats['misses'] >= 0
    
    def test_delete_removes_from_cache(self, repository):
        """Test deletion removes model from cache."""
        model = DocumentModel()
        model.metadata['id'] = 'test_delete_cache'
        repository.save(model)
        
        # Verify in cache
        assert 'test_delete_cache' in repository._cache
        
        # Delete
        repository.delete('test_delete_cache')
        
        # Verify removed from cache
        assert 'test_delete_cache' not in repository._cache


class TestModelQuery:
    """Tests for ModelQuery filtering."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def repository(self, temp_workspace):
        """Create repository with test models."""
        repo = ModelRepository(temp_workspace)
        
        # Create diverse test models
        # Small model (5 places, 3 transitions)
        small = DocumentModel()
        small.metadata['id'] = 'small_model'
        small.metadata['name'] = 'Small Model'
        for i in range(5):
            small.create_place(i * 50, 100, f"P{i}")
        for i in range(3):
            small.create_transition(i * 50, 200, f"T{i}")
        repo.save(small)
        
        # Large model (20 places, 15 transitions)
        large = DocumentModel()
        large.metadata['id'] = 'large_model'
        large.metadata['name'] = 'Large Model'
        for i in range(20):
            large.create_place(i * 50, 100, f"P{i}")
        for i in range(15):
            large.create_transition(i * 50, 200, f"T{i}")
        repo.save(large)
        
        # Modular model
        modular = DocumentModel()
        modular.metadata['id'] = 'modular_model'
        modular.metadata['name'] = 'Modular Model'
        from shypn.netobjs.module import Module
        modular.modules['mod1'] = Module('mod1', 'Module 1')
        modular.modules['mod2'] = Module('mod2', 'Module 2')
        for i in range(10):
            modular.create_place(i * 50, 100, f"P{i}")
        repo.save(modular)
        
        return repo
    
    def test_query_by_name_pattern(self, repository):
        """Test filtering by name pattern."""
        query = ModelQuery().with_name_pattern("Small.*")
        results = repository.search(query)
        
        assert len(results) == 1
        assert results[0].metadata['name'] == 'Small Model'
    
    def test_query_by_place_count_min(self, repository):
        """Test filtering by minimum place count."""
        query = ModelQuery().with_place_count(min_count=15)
        results = repository.search(query)
        
        assert len(results) == 1
        assert results[0].metadata['name'] == 'Large Model'
    
    def test_query_by_place_count_range(self, repository):
        """Test filtering by place count range."""
        query = ModelQuery().with_place_count(min_count=5, max_count=15)
        results = repository.search(query)
        
        assert len(results) == 2  # small (5) and modular (10)
    
    def test_query_by_transition_count(self, repository):
        """Test filtering by transition count."""
        query = ModelQuery().with_transition_count(min_count=10)
        results = repository.search(query)
        
        assert len(results) == 1
        assert results[0].metadata['name'] == 'Large Model'
    
    def test_query_with_modules(self, repository):
        """Test filtering models with modules."""
        query = ModelQuery().with_modules(True)
        results = repository.search(query)
        
        assert len(results) == 1
        assert results[0].metadata['name'] == 'Modular Model'
    
    def test_query_without_modules(self, repository):
        """Test filtering models without modules."""
        query = ModelQuery().with_modules(False)
        results = repository.search(query)
        
        assert len(results) == 2
        names = [r.metadata['name'] for r in results]
        assert 'Small Model' in names
        assert 'Large Model' in names
    
    def test_query_by_module_count(self, repository):
        """Test filtering by exact module count."""
        query = ModelQuery().with_module_count(2)
        results = repository.search(query)
        
        assert len(results) == 1
        assert results[0].metadata['name'] == 'Modular Model'
    
    def test_query_chaining(self, repository):
        """Test chaining multiple query filters."""
        query = (ModelQuery()
                 .with_place_count(min_count=5, max_count=15)
                 .with_modules(False))
        results = repository.search(query)
        
        assert len(results) == 1
        assert results[0].metadata['name'] == 'Small Model'
    
    def test_query_with_metadata(self, repository):
        """Test filtering by metadata."""
        # Add metadata to one model
        model = repository.get_by_id('small_model')
        model.metadata['source'] = 'KEGG'
        repository.save(model)
        
        query = ModelQuery().with_metadata(source='KEGG')
        results = repository.search(query)
        
        assert len(results) == 1
        assert results[0].metadata['id'] == 'small_model'
    
    def test_empty_query_returns_all(self, repository):
        """Test empty query returns all models."""
        query = ModelQuery()
        results = repository.search(query)
        
        assert len(results) == 3


class TestModelRepositoryImportExport:
    """Tests for import/export functionality."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def repository(self, temp_workspace):
        """Create repository."""
        return ModelRepository(temp_workspace)
    
    def test_export_model(self, repository, temp_workspace):
        """Test exporting a model."""
        # Create and save model
        model = DocumentModel()
        model.metadata['id'] = 'export_test'
        model.metadata['name'] = 'Export Model'
        repository.save(model)
        
        # Export to external file
        export_path = Path(temp_workspace) / 'exported' / 'model.shy'
        success = repository.export_model('export_test', str(export_path))
        
        assert success is True
        assert export_path.exists()
    
    def test_export_nonexistent_model_raises_error(self, repository, temp_workspace):
        """Test exporting nonexistent model raises error."""
        export_path = Path(temp_workspace) / 'exported.shy'
        
        with pytest.raises(EntityNotFoundError):
            repository.export_model('nonexistent', str(export_path))
    
    def test_import_model(self, repository, temp_workspace):
        """Test importing a model."""
        # Create external model file
        external_model = DocumentModel()
        external_model.metadata['name'] = 'Imported Model'
        external_path = Path(temp_workspace) / 'external.shy'
        external_model.save_to_file(str(external_path))
        
        # Import
        model_id = repository.import_model(str(external_path), 'imported_model')
        
        assert model_id == 'imported_model'
        assert repository.exists('imported_model') is True
        
        # Verify imported model
        model = repository.get_by_id('imported_model')
        assert model.metadata['name'] == 'Imported Model'
        assert 'imported_from' in model.metadata
    
    def test_import_model_auto_id(self, repository, temp_workspace):
        """Test importing model with automatic ID."""
        # Create external model file
        external_model = DocumentModel()
        external_path = Path(temp_workspace) / 'auto_id_model.shy'
        external_model.save_to_file(str(external_path))
        
        # Import without specifying ID
        model_id = repository.import_model(str(external_path))
        
        assert model_id == 'auto_id_model'  # Use filename
        assert repository.exists('auto_id_model') is True
    
    def test_import_nonexistent_file_raises_error(self, repository):
        """Test importing nonexistent file raises error."""
        with pytest.raises(ValueError, match="not found"):
            repository.import_model('/nonexistent/file.shy')


class TestModelRepositoryRepr:
    """Tests for string representation."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def repository(self, temp_workspace):
        """Create repository."""
        return ModelRepository(temp_workspace, cache_size=10)
    
    def test_repr(self, repository):
        """Test __repr__ method."""
        repr_str = repr(repository)
        
        assert 'ModelRepository' in repr_str
        assert 'workspace=' in repr_str
        assert 'models=' in repr_str
        assert 'cache=' in repr_str
