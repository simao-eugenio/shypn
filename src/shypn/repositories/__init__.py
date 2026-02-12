"""
Repositories Package

Repository pattern implementations for data access and persistence.
Part of Phase 3.2: Repository Pattern Implementation.

This package provides:
- BaseRepository: Abstract base for all repositories
- CachedRepository: Base with LRU caching support
- ModelRepository: Petri net model persistence with caching and querying
- ModelQuery: Fluent query builder for model search
- SimulationDataRepository: Simulation trajectory and batch results persistence
- SimulationTrajectory: Time series data container
- BatchResults: Batch experiment results container

Example:
    from shypn.repositories import ModelRepository, ModelQuery
    
    # Create repository
    repo = ModelRepository("/workspace")
    
    # Load model (cached)
    model = repo.get_by_id("glycolysis")
    
    # Query models
    query = ModelQuery().with_place_count(min_count=10)
    large_models = repo.search(query)
"""

from shypn.repositories.base_repository import (
    BaseRepository,
    CachedRepository,
    RepositoryError,
    EntityNotFoundError,
    RepositoryIOError
)
from shypn.repositories.model_repository import (
    ModelRepository,
    ModelQuery
)
from shypn.repositories.simulation_data_repository import (
    SimulationDataRepository,
    SimulationTrajectory,
    BatchResults
)

__all__ = [
    # Base classes
    'BaseRepository',
    'CachedRepository',
    
    # Exceptions
    'RepositoryError',
    'EntityNotFoundError',
    'RepositoryIOError',
    
    # Model repository
    'ModelRepository',
    'ModelQuery',
    
    # Simulation data repository
    'SimulationDataRepository',
    'SimulationTrajectory',
    'BatchResults',
]
