"""
Tests for SimulationDataRepository

Comprehensive test suite for simulation data repository including trajectory
management, batch results, and storage operations.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from shypn.repositories import (
    SimulationDataRepository,
    SimulationTrajectory,
    BatchResults,
    RepositoryIOError
)


class TestSimulationTrajectory:
    """Tests for SimulationTrajectory container."""
    
    def test_trajectory_creation(self):
        """Test creating a trajectory."""
        trajectory = SimulationTrajectory(
            simulation_id="sim_001",
            model_id="test_model",
            times=[0.0, 1.0, 2.0],
            place_data={"P1": [10, 12, 15], "P2": [5, 7, 8]},
            transition_data={"T1": [2, 3, 5]},
            metadata={"seed": 42}
        )
        
        assert trajectory.simulation_id == "sim_001"
        assert trajectory.model_id == "test_model"
        assert len(trajectory.times) == 3
        assert "P1" in trajectory.place_data
        assert trajectory.metadata["seed"] == 42
        assert trajectory.created_at is not None
    
    def test_trajectory_to_dict(self):
        """Test trajectory serialization to dict."""
        trajectory = SimulationTrajectory(
            simulation_id="sim_001",
            model_id="test_model",
            times=[0.0, 1.0],
            place_data={"P1": [10, 12]},
            transition_data={"T1": [2, 3]}
        )
        
        data = trajectory.to_dict()
        assert data["simulation_id"] == "sim_001"
        assert data["model_id"] == "test_model"
        assert data["times"] == [0.0, 1.0]
        assert data["place_data"]["P1"] == [10, 12]
    
    def test_trajectory_from_dict(self):
        """Test trajectory deserialization from dict."""
        data = {
            'simulation_id': 'sim_001',
            'model_id': 'test_model',
            'times': [0.0, 1.0, 2.0],
            'place_data': {'P1': [10, 12, 15]},
            'transition_data': {'T1': [2, 3, 5]},
            'metadata': {'seed': 42}
        }
        
        trajectory = SimulationTrajectory.from_dict(data)
        assert trajectory.simulation_id == "sim_001"
        assert trajectory.model_id == "test_model"
        assert len(trajectory.times) == 3
        assert trajectory.metadata["seed"] == 42


class TestBatchResults:
    """Tests for BatchResults container."""
    
    def test_batch_results_creation(self):
        """Test creating batch results."""
        results = BatchResults(
            experiment_id="exp_001",
            model_id="test_model",
            replicate_count=100,
            metadata={"ic_noise": 0.2}
        )
        
        assert results.experiment_id == "exp_001"
        assert results.model_id == "test_model"
        assert results.replicate_count == 100
        assert results.metadata["ic_noise"] == 0.2
        assert results.created_at is not None
    
    def test_batch_results_save_load(self):
        """Test batch results save and load."""
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # Create batch results with trajectories
            trajectory = SimulationTrajectory(
                simulation_id="sim_001",
                model_id="test_model",
                times=[0.0, 1.0],
                place_data={"P1": [10, 12]},
                transition_data={"T1": [2, 3]}
            )
            
            results = BatchResults(
                experiment_id="exp_001",
                model_id="test_model",
                replicate_count=1,
                trajectories=[trajectory],
                statistics={"mean_p1": 11.0}
            )
            
            # Save
            filepath = temp_dir / "test.json.gz"
            results.save_to_file(filepath)
            assert filepath.exists()
            
            # Load
            loaded = BatchResults.load_from_file(filepath)
            assert loaded.experiment_id == "exp_001"
            assert loaded.replicate_count == 1
            assert len(loaded.trajectories) == 1
            assert loaded.statistics["mean_p1"] == 11.0
            
        finally:
            shutil.rmtree(temp_dir)


class TestSimulationDataRepositoryBasics:
    """Tests for basic repository operations."""
    
    @pytest.fixture
    def temp_data_path(self):
        """Create temporary data directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def repository(self, temp_data_path):
        """Create repository with temporary directory."""
        return SimulationDataRepository(temp_data_path)
    
    @pytest.fixture
    def sample_trajectory(self):
        """Create sample trajectory."""
        return SimulationTrajectory(
            simulation_id="sim_001",
            model_id="test_model",
            times=[0.0, 1.0, 2.0, 3.0],
            place_data={
                "P1": [10, 12, 15, 18],
                "P2": [5, 7, 8, 10]
            },
            transition_data={
                "T1": [2, 3, 5, 7]
            },
            metadata={"seed": 42}
        )
    
    def test_repository_initialization(self, temp_data_path):
        """Test repository initializes correctly."""
        repo = SimulationDataRepository(temp_data_path)
        
        assert repo.get_data_path() == Path(temp_data_path)
        assert (Path(temp_data_path) / 'trajectories').exists()
        assert (Path(temp_data_path) / 'batch').exists()
    
    def test_save_and_load_trajectory(self, repository, sample_trajectory):
        """Test saving and loading a trajectory."""
        # Save
        success = repository.save_trajectory(sample_trajectory)
        assert success is True
        
        # Load
        loaded = repository.load_trajectory("sim_001")
        assert loaded is not None
        assert loaded.simulation_id == "sim_001"
        assert loaded.model_id == "test_model"
        assert len(loaded.times) == 4
        assert "P1" in loaded.place_data
        assert loaded.metadata["seed"] == 42
    
    def test_load_nonexistent_trajectory_returns_none(self, repository):
        """Test loading nonexistent trajectory returns None."""
        trajectory = repository.load_trajectory("nonexistent")
        assert trajectory is None
    
    def test_delete_trajectory(self, repository, sample_trajectory):
        """Test deleting a trajectory."""
        # Save
        repository.save_trajectory(sample_trajectory)
        assert repository.exists("sim_001") is True
        
        # Delete
        success = repository.delete_trajectory("sim_001")
        assert success is True
        assert repository.exists("sim_001") is False
    
    def test_delete_nonexistent_trajectory(self, repository):
        """Test deleting nonexistent trajectory returns False."""
        success = repository.delete_trajectory("nonexistent")
        assert success is False
    
    def test_exists_method(self, repository, sample_trajectory):
        """Test exists method."""
        assert repository.exists("sim_001") is False
        
        repository.save_trajectory(sample_trajectory)
        assert repository.exists("sim_001") is True
    
    def test_list_simulations(self, repository):
        """Test listing all simulations."""
        # Save multiple simulations
        for i in range(3):
            trajectory = SimulationTrajectory(
                simulation_id=f"sim_{i:03d}",
                model_id="test_model",
                times=[0.0, 1.0],
                place_data={"P1": [10, 12]},
                transition_data={"T1": [2, 3]}
            )
            repository.save_trajectory(trajectory)
        
        sim_ids = repository.list_simulations()
        assert len(sim_ids) == 3
        assert "sim_000" in sim_ids
        assert "sim_001" in sim_ids
        assert "sim_002" in sim_ids
    
    def test_list_simulations_filtered_by_model(self, repository):
        """Test listing simulations filtered by model ID."""
        # Save simulations for different models
        for model_id in ["model_a", "model_b"]:
            for i in range(2):
                trajectory = SimulationTrajectory(
                    simulation_id=f"{model_id}_sim_{i}",
                    model_id=model_id,
                    times=[0.0, 1.0],
                    place_data={"P1": [10, 12]},
                    transition_data={"T1": [2, 3]}
                )
                repository.save_trajectory(trajectory)
        
        # Filter by model_a
        model_a_sims = repository.list_simulations(model_id="model_a")
        assert len(model_a_sims) == 2
        assert all("model_a" in sim_id for sim_id in model_a_sims)
    
    def test_count_trajectories(self, repository):
        """Test counting trajectories."""
        assert repository.count() == 0
        
        # Save 3 trajectories
        for i in range(3):
            trajectory = SimulationTrajectory(
                simulation_id=f"sim_{i}",
                model_id="test_model",
                times=[0.0],
                place_data={"P1": [10]},
                transition_data={"T1": [2]}
            )
            repository.save_trajectory(trajectory)
        
        assert repository.count() == 3
    
    def test_get_all_trajectories(self, repository):
        """Test getting all trajectories."""
        # Save multiple trajectories
        for i in range(3):
            trajectory = SimulationTrajectory(
                simulation_id=f"sim_{i}",
                model_id="test_model",
                times=[0.0],
                place_data={"P1": [10]},
                transition_data={"T1": [2]}
            )
            repository.save_trajectory(trajectory)
        
        all_trajectories = repository.get_all()
        assert len(all_trajectories) == 3
        assert all(isinstance(t, SimulationTrajectory) for t in all_trajectories)


class TestBatchResultsManagement:
    """Tests for batch experiment results management."""
    
    @pytest.fixture
    def temp_data_path(self):
        """Create temporary data directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def repository(self, temp_data_path):
        """Create repository."""
        return SimulationDataRepository(temp_data_path)
    
    @pytest.fixture
    def sample_batch_results(self):
        """Create sample batch results."""
        trajectories = []
        for i in range(5):
            trajectory = SimulationTrajectory(
                simulation_id=f"sim_{i:03d}",
                model_id="test_model",
                times=[0.0, 1.0, 2.0],
                place_data={"P1": [10 + i, 12 + i, 15 + i]},
                transition_data={"T1": [2, 3, 5]}
            )
            trajectories.append(trajectory)
        
        return BatchResults(
            experiment_id="exp_001",
            model_id="test_model",
            replicate_count=5,
            trajectories=trajectories,
            statistics={"mean_p1_final": 17.0, "std_p1_final": 1.58},
            metadata={"ic_noise": 0.2, "seed_start": 100}
        )
    
    def test_save_and_load_batch_results(self, repository, sample_batch_results):
        """Test saving and loading batch results."""
        # Save
        success = repository.save_batch_results(sample_batch_results)
        assert success is True
        
        # Load
        loaded = repository.load_batch_results("exp_001")
        assert loaded is not None
        assert loaded.experiment_id == "exp_001"
        assert loaded.model_id == "test_model"
        assert loaded.replicate_count == 5
        assert len(loaded.trajectories) == 5
        assert loaded.statistics["mean_p1_final"] == 17.0
        assert loaded.metadata["ic_noise"] == 0.2
    
    def test_load_nonexistent_batch_results(self, repository):
        """Test loading nonexistent batch results returns None."""
        results = repository.load_batch_results("nonexistent")
        assert results is None
    
    def test_delete_batch_results(self, repository, sample_batch_results):
        """Test deleting batch results."""
        # Save
        repository.save_batch_results(sample_batch_results)
        
        # Verify file exists
        batch_path = repository._get_batch_path("exp_001")
        assert batch_path.exists()
        
        # Delete
        success = repository.delete_batch_results("exp_001")
        assert success is True
        assert not batch_path.exists()
    
    def test_delete_nonexistent_batch_results(self, repository):
        """Test deleting nonexistent batch results returns False."""
        success = repository.delete_batch_results("nonexistent")
        assert success is False
    
    def test_list_experiments(self, repository):
        """Test listing all experiments."""
        # Save multiple experiments
        for i in range(3):
            results = BatchResults(
                experiment_id=f"exp_{i:03d}",
                model_id="test_model",
                replicate_count=10
            )
            repository.save_batch_results(results)
        
        exp_ids = repository.list_experiments()
        assert len(exp_ids) == 3
        assert "exp_000" in exp_ids
        assert "exp_001" in exp_ids
        assert "exp_002" in exp_ids


class TestStorageManagement:
    """Tests for storage statistics and cleanup."""
    
    @pytest.fixture
    def temp_data_path(self):
        """Create temporary data directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def repository(self, temp_data_path):
        """Create repository."""
        return SimulationDataRepository(temp_data_path)
    
    def test_get_storage_stats_empty(self, repository):
        """Test storage stats for empty repository."""
        stats = repository.get_storage_stats()
        
        assert stats['trajectories_count'] == 0
        assert stats['trajectories_bytes'] == 0
        assert stats['batch_count'] == 0
        assert stats['batch_bytes'] == 0
        assert stats['total_bytes'] == 0
    
    def test_get_storage_stats_with_data(self, repository):
        """Test storage stats with data."""
        # Save trajectories
        for i in range(3):
            trajectory = SimulationTrajectory(
                simulation_id=f"sim_{i}",
                model_id="test_model",
                times=[0.0, 1.0],
                place_data={"P1": [10, 12]},
                transition_data={"T1": [2, 3]}
            )
            repository.save_trajectory(trajectory)
        
        # Save batch results
        for i in range(2):
            results = BatchResults(
                experiment_id=f"exp_{i}",
                model_id="test_model",
                replicate_count=10
            )
            repository.save_batch_results(results)
        
        stats = repository.get_storage_stats()
        assert stats['trajectories_count'] == 3
        assert stats['trajectories_bytes'] > 0
        assert stats['batch_count'] == 2
        assert stats['batch_bytes'] > 0
        assert stats['total_bytes'] > 0
    
    def test_cleanup_old_data(self, repository):
        """Test cleaning up old data."""
        import time
        import os
        
        # Save trajectory
        trajectory = SimulationTrajectory(
            simulation_id="old_sim",
            model_id="test_model",
            times=[0.0],
            place_data={"P1": [10]},
            transition_data={"T1": [2]}
        )
        repository.save_trajectory(trajectory)
        
        # Manually set old mtime (simulate old file)
        trajectory_path = repository._get_trajectory_path("old_sim")
        old_time = time.time() - (40 * 24 * 60 * 60)  # 40 days ago
        os.utime(trajectory_path, (old_time, old_time))
        
        # Cleanup files older than 30 days
        deleted_count = repository.cleanup_old_data(days=30)
        
        assert deleted_count == 1
        assert not repository.exists("old_sim")


class TestRepositoryRepr:
    """Tests for string representation."""
    
    @pytest.fixture
    def temp_data_path(self):
        """Create temporary data directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def repository(self, temp_data_path):
        """Create repository."""
        return SimulationDataRepository(temp_data_path)
    
    def test_repr(self, repository):
        """Test __repr__ method."""
        repr_str = repr(repository)
        
        assert 'SimulationDataRepository' in repr_str
        assert 'path=' in repr_str
        assert 'trajectories=' in repr_str
        assert 'experiments=' in repr_str
