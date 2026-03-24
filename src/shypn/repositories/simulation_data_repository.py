"""
Simulation Data Repository

Repository pattern implementation for simulation data persistence and retrieval.
Manages trajectory data, batch experiment results, and analysis cache.

Part of Phase 3.2: Repository Pattern Implementation.
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from shypn.repositories.base_repository import (
    BaseRepository,
    RepositoryIOError
)

logger = logging.getLogger(__name__)


class SimulationTrajectory:
    """Container for simulation trajectory data.
    
    Stores time series data for places and transitions over simulation time.
    
    Attributes:
        simulation_id: Unique identifier for simulation run
        model_id: ID of model that was simulated
        times: List of time points
        place_data: Dict mapping place_id → list of token counts
        transition_data: Dict mapping transition_id → list of firing counts
        metadata: Additional simulation metadata
    """
    
    def __init__(
        self,
        simulation_id: str,
        model_id: str,
        times: List[float],
        place_data: Dict[str, List[float]],
        transition_data: Dict[str, List[int]],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize trajectory.
        
        Args:
            simulation_id: Unique simulation identifier
            model_id: Model identifier
            times: Time points
            place_data: Place trajectories
            transition_data: Transition firing trajectories
            metadata: Optional metadata
        """
        self.simulation_id = simulation_id
        self.model_id = model_id
        self.times = times
        self.place_data = place_data
        self.transition_data = transition_data
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'simulation_id': self.simulation_id,
            'model_id': self.model_id,
            'times': self.times,
            'place_data': self.place_data,
            'transition_data': self.transition_data,
            'metadata': self.metadata,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SimulationTrajectory':
        """Deserialize from dictionary."""
        trajectory = cls(
            simulation_id=data['simulation_id'],
            model_id=data['model_id'],
            times=data['times'],
            place_data=data['place_data'],
            transition_data=data['transition_data'],
            metadata=data.get('metadata', {})
        )
        trajectory.created_at = data.get('created_at', datetime.now().isoformat())
        return trajectory


class BatchResults:
    """Container for batch experiment results.
    
    Stores results from multiple replicate simulations with statistical analysis.
    
    Attributes:
        experiment_id: Unique identifier for batch experiment
        model_id: ID of model that was simulated
        replicate_count: Number of replicates run
        trajectories: List of SimulationTrajectory objects (one per replicate)
        statistics: Statistical summaries (mean, std, percentiles)
        metadata: Additional experiment metadata
    """
    
    def __init__(
        self,
        experiment_id: str,
        model_id: str,
        replicate_count: int,
        trajectories: Optional[List[SimulationTrajectory]] = None,
        statistics: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize batch results.
        
        Args:
            experiment_id: Unique experiment identifier
            model_id: Model identifier
            replicate_count: Number of replicates
            trajectories: List of replicate trajectories
            statistics: Statistical summaries
            metadata: Optional metadata
        """
        self.experiment_id = experiment_id
        self.model_id = model_id
        self.replicate_count = replicate_count
        self.trajectories = trajectories or []
        self.statistics = statistics or {}
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()
    
    def save_to_file(self, filepath: Path):
        """Save batch results to compressed JSON file.
        
        Args:
            filepath: Path to save file
        """
        import gzip
        
        data = {
            'experiment_id': self.experiment_id,
            'model_id': self.model_id,
            'replicate_count': self.replicate_count,
            'trajectories': [t.to_dict() for t in self.trajectories],
            'statistics': self.statistics,
            'metadata': self.metadata,
            'created_at': self.created_at
        }
        
        # Save as compressed JSON for efficiency
        with gzip.open(str(filepath), 'wt', encoding='utf-8') as f:
            json.dump(data, f)
    
    @classmethod
    def load_from_file(cls, filepath: Path) -> 'BatchResults':
        """Load batch results from compressed JSON file.
        
        Args:
            filepath: Path to load from
        
        Returns:
            BatchResults object
        """
        import gzip
        
        with gzip.open(str(filepath), 'rt', encoding='utf-8') as f:
            data = json.load(f)
        
        trajectories = [
            SimulationTrajectory.from_dict(t_data)
            for t_data in data.get('trajectories', [])
        ]
        
        results = cls(
            experiment_id=data['experiment_id'],
            model_id=data['model_id'],
            replicate_count=data['replicate_count'],
            trajectories=trajectories,
            statistics=data.get('statistics', {}),
            metadata=data.get('metadata', {})
        )
        results.created_at = data.get('created_at', datetime.now().isoformat())
        return results


class SimulationDataRepository(BaseRepository[SimulationTrajectory]):
    """Repository for simulation data persistence.
    
    Manages:
    - Trajectory data (single simulation runs)
    - Batch experiment results (multiple replicates)
    - Storage organization and cleanup
    
    Directory structure:
        data/
        ├── trajectories/
        │   ├── {simulation_id}.json
        │   └── ...
        └── batch/
            ├── {experiment_id}.json.gz
            └── ...
    
    Example:
        repo = SimulationDataRepository("/workspace/data")
        
        # Save trajectory
        trajectory = SimulationTrajectory(
            simulation_id="sim_001",
            model_id="glycolysis",
            times=[0, 1, 2],
            place_data={"P1": [10, 12, 15]},
            transition_data={"T1": [2, 3, 5]}
        )
        repo.save_trajectory(trajectory)
        
        # Load trajectory
        loaded = repo.load_trajectory("sim_001")
        
        # Save batch results
        batch = BatchResults(
            experiment_id="exp_001",
            model_id="glycolysis",
            replicate_count=100,
            trajectories=[...]
        )
        repo.save_batch_results(batch)
    """
    
    def __init__(self, data_path: str):
        """Initialize simulation data repository.
        
        Args:
            data_path: Path to data directory
        
        Creates directory structure if needed.
        """
        self._data_path = Path(data_path)
        self._data_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self._trajectories_path = self._data_path / 'trajectories'
        self._trajectories_path.mkdir(exist_ok=True)
        
        self._batch_path = self._data_path / 'batch'
        self._batch_path.mkdir(exist_ok=True)
    
    # ===== Trajectory Management =====
    
    def save_trajectory(self, trajectory: SimulationTrajectory) -> bool:
        """Save simulation trajectory.
        
        Args:
            trajectory: SimulationTrajectory to save
        
        Returns:
            True if save succeeded
        
        Raises:
            RepositoryIOError: If save fails
        """
        file_path = self._get_trajectory_path(trajectory.simulation_id)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(trajectory.to_dict(), f)
            return True
        except Exception as e:
            raise RepositoryIOError('save_trajectory', f"Failed to save {file_path}: {e}")
    
    def load_trajectory(self, simulation_id: str) -> Optional[SimulationTrajectory]:
        """Load simulation trajectory.
        
        Args:
            simulation_id: Simulation identifier
        
        Returns:
            SimulationTrajectory if found, None otherwise
        
        Raises:
            RepositoryIOError: If load fails
        """
        file_path = self._get_trajectory_path(simulation_id)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return SimulationTrajectory.from_dict(json.load(f))
        except Exception as e:
            raise RepositoryIOError('load_trajectory', f"Failed to load {file_path}: {e}")
    
    def delete_trajectory(self, simulation_id: str) -> bool:
        """Delete simulation trajectory.
        
        Args:
            simulation_id: Simulation identifier
        
        Returns:
            True if deletion succeeded, False if not found
        """
        file_path = self._get_trajectory_path(simulation_id)
        
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            return True
        except Exception as e:
            raise RepositoryIOError('delete_trajectory', f"Failed to delete {file_path}: {e}")
    
    def list_simulations(self, model_id: Optional[str] = None) -> List[str]:
        """List all saved simulations.
        
        Args:
            model_id: Optional model ID to filter by
        
        Returns:
            List of simulation IDs
        """
        pattern = f"{model_id}_*.json" if model_id else "*.json"
        return [
            path.stem
            for path in self._trajectories_path.glob(pattern)
            if path.is_file()
        ]
    
    # ===== Batch Results Management =====
    
    def save_batch_results(self, results: BatchResults) -> bool:
        """Save batch experiment results.
        
        Args:
            results: BatchResults to save
        
        Returns:
            True if save succeeded
        
        Raises:
            RepositoryIOError: If save fails
        """
        file_path = self._get_batch_path(results.experiment_id)
        
        try:
            results.save_to_file(file_path)
            return True
        except Exception as e:
            raise RepositoryIOError('save_batch_results', f"Failed to save {file_path}: {e}")
    
    def load_batch_results(self, experiment_id: str) -> Optional[BatchResults]:
        """Load batch experiment results.
        
        Args:
            experiment_id: Experiment identifier
        
        Returns:
            BatchResults if found, None otherwise
        
        Raises:
            RepositoryIOError: If load fails
        """
        file_path = self._get_batch_path(experiment_id)
        
        if not file_path.exists():
            return None
        
        try:
            return BatchResults.load_from_file(file_path)
        except Exception as e:
            raise RepositoryIOError('load_batch_results', f"Failed to load {file_path}: {e}")
    
    def delete_batch_results(self, experiment_id: str) -> bool:
        """Delete batch experiment results.
        
        Args:
            experiment_id: Experiment identifier
        
        Returns:
            True if deletion succeeded, False if not found
        """
        file_path = self._get_batch_path(experiment_id)
        
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            return True
        except Exception as e:
            raise RepositoryIOError('delete_batch_results', f"Failed to delete {file_path}: {e}")
    
    def list_experiments(self) -> List[str]:
        """List all batch experiments.
        
        Returns:
            List of experiment IDs
        """
        return [
            path.stem.replace('.json', '')  # Remove both .json and .gz
            for path in self._batch_path.glob("*.json.gz")
            if path.is_file()
        ]
    
    # ===== BaseRepository Implementation =====
    
    def get_by_id(self, entity_id: str) -> Optional[SimulationTrajectory]:
        """Get trajectory by simulation ID.
        
        Args:
            entity_id: Simulation ID
        
        Returns:
            SimulationTrajectory if found, None otherwise
        """
        return self.load_trajectory(entity_id)
    
    def get_all(self) -> List[SimulationTrajectory]:
        """Get all trajectories.
        
        Returns:
            List of all SimulationTrajectory objects
        
        Note:
            May be memory-intensive for large datasets
        """
        trajectories = []
        for sim_id in self.list_simulations():
            trajectory = self.load_trajectory(sim_id)
            if trajectory:
                trajectories.append(trajectory)
        return trajectories
    
    def save(self, entity: SimulationTrajectory) -> bool:
        """Save trajectory (alias for save_trajectory).
        
        Args:
            entity: SimulationTrajectory to save
        
        Returns:
            True if save succeeded
        """
        return self.save_trajectory(entity)
    
    def delete(self, entity_id: str) -> bool:
        """Delete trajectory (alias for delete_trajectory).
        
        Args:
            entity_id: Simulation ID
        
        Returns:
            True if deletion succeeded
        """
        return self.delete_trajectory(entity_id)
    
    def exists(self, entity_id: str) -> bool:
        """Check if trajectory exists.
        
        Args:
            entity_id: Simulation ID
        
        Returns:
            True if trajectory file exists
        """
        file_path = self._get_trajectory_path(entity_id)
        return file_path.exists() and file_path.is_file()
    
    def count(self) -> int:
        """Get total number of trajectories.
        
        Returns:
            Count of trajectory files
        """
        return len(self.list_simulations())
    
    # ===== Storage Statistics =====
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics.
        
        Returns:
            Dictionary with storage metrics:
            - trajectories_count: Number of trajectory files
            - trajectories_bytes: Total size of trajectories
            - batch_count: Number of batch result files
            - batch_bytes: Total size of batch results
            - total_bytes: Total storage usage
        """
        stats = {
            'trajectories_count': 0,
            'trajectories_bytes': 0,
            'batch_count': 0,
            'batch_bytes': 0,
            'total_bytes': 0
        }
        
        # Count trajectories
        for file_path in self._trajectories_path.glob('*.json'):
            if file_path.is_file():
                stats['trajectories_count'] += 1
                stats['trajectories_bytes'] += file_path.stat().st_size
        
        # Count batch results
        for file_path in self._batch_path.glob('*.json.gz'):
            if file_path.is_file():
                stats['batch_count'] += 1
                stats['batch_bytes'] += file_path.stat().st_size
        
        stats['total_bytes'] = stats['trajectories_bytes'] + stats['batch_bytes']
        
        return stats
    
    def cleanup_old_data(self, days: int = 30) -> int:
        """Delete simulation data older than specified days.
        
        Args:
            days: Age threshold in days
        
        Returns:
            Number of files deleted
        """
        import time
        
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        deleted_count = 0
        
        # Clean trajectories
        for file_path in self._trajectories_path.glob('*.json'):
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except (OSError, PermissionError) as e:
                    logger.debug(f"Failed to delete trajectory file {file_path}: {e}")
        
        # Clean batch results
        for file_path in self._batch_path.glob('*.json.gz'):
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except (OSError, PermissionError) as e:
                    logger.debug(f"Failed to delete batch result file {file_path}: {e}")
        
        return deleted_count
    
    # ===== Helper Methods =====
    
    def _get_trajectory_path(self, simulation_id: str) -> Path:
        """Get file path for trajectory.
        
        Args:
            simulation_id: Simulation ID
        
        Returns:
            Path to trajectory file
        """
        return self._trajectories_path / f"{simulation_id}.json"
    
    def _get_batch_path(self, experiment_id: str) -> Path:
        """Get file path for batch results.
        
        Args:
            experiment_id: Experiment ID
        
        Returns:
            Path to batch results file
        """
        return self._batch_path / f"{experiment_id}.json.gz"
    
    def get_data_path(self) -> Path:
        """Get data directory path.
        
        Returns:
            Path to data directory
        """
        return self._data_path
    
    def __repr__(self) -> str:
        """Get string representation for debugging."""
        stats = self.get_storage_stats()
        return (f"SimulationDataRepository(path={self._data_path}, "
                f"trajectories={stats['trajectories_count']}, "
                f"experiments={stats['batch_count']})")
