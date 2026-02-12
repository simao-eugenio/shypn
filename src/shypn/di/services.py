"""
Service Registration - Core Application Services

Provides utilities for registering core application services with the
dependency injection container.

Part of Phase 3.3: Dependency Injection Framework.

Example:
    from shypn.di import get_container
    from shypn.di.services import register_core_services
    
    # Register all core services
    container = get_container()
    register_core_services(container, workspace_path="/home/user/workspace")
    
    # Services now available
    repo = container.get('model_repository')
    builder = container.get('place_builder')
"""

from pathlib import Path
from typing import Optional

from shypn.di.service_container import ServiceContainer


def register_core_services(
    container: ServiceContainer,
    workspace_path: Optional[str] = None,
    data_path: Optional[str] = None
):
    """Register core application services with container.
    
    Registers:
    - Repositories (singleton):
        - model_repository: ModelRepository for .shy file persistence
        - simulation_data_repository: SimulationDataRepository for results
    
    - Builder classes (instance):
        - arc_builder_class: ArcBuilder class for creating arc builders
        - petri_net_builder_class: PetriNetBuilder class for creating net builders
        - simulation_config_builder_class: SimulationConfigBuilder class
    
    Note: PlaceBuilder and TransitionBuilder require constructor arguments
    (id/name), so they are not registered. Create them directly:
        place_builder = PlaceBuilder('p1')
        transition_builder = TransitionBuilder('t1')
    
    Args:
        container: ServiceContainer to register services with
        workspace_path: Path to workspace directory (for model storage)
        data_path: Path to data directory (for simulation results)
    
    Example:
        >>> container = ServiceContainer()
        >>> register_core_services(container, workspace_path="/home/user/ws")
        >>> repo = container.get('model_repository')
        >>> ArcBuilder = container.get('arc_builder_class')
        >>> arc_builder = ArcBuilder()
    """
    # Import here to avoid circular dependencies
    from shypn.repositories import ModelRepository, SimulationDataRepository
    from shypn.builders import (
        ArcBuilder,
        PetriNetBuilder,
        SimulationConfigBuilder,
    )
    
    # Set default paths
    if workspace_path is None:
        workspace_path = str(Path.cwd())
    if data_path is None:
        data_path = str(Path(workspace_path) / "data")
    
    # Register repositories as singletons (shared instances)
    container.register_singleton(
        'model_repository',
        lambda: ModelRepository(workspace_path=workspace_path)
    )
    
    container.register_singleton(
        'simulation_data_repository',
        lambda: SimulationDataRepository(data_path=data_path)
    )
    
    # Register builder classes as instances (for instantiation by users)
    # These don't require constructor arguments
    container.register_instance('arc_builder_class', ArcBuilder)
    container.register_instance('petri_net_builder_class', PetriNetBuilder)
    container.register_instance('simulation_config_builder_class', SimulationConfigBuilder)


def register_repositories(
    container: ServiceContainer,
    workspace_path: Optional[str] = None,
    data_path: Optional[str] = None
):
    """Register repository services only.
    
    Convenience function for registering just repositories without builders.
    Useful for testing or minimal setups.
    
    Args:
        container: ServiceContainer to register services with
        workspace_path: Path to workspace directory
        data_path: Path to data directory
    
    Example:
        >>> container = ServiceContainer()
        >>> register_repositories(container, workspace_path="/tmp/test")
    """
    from shypn.repositories import ModelRepository, SimulationDataRepository
    
    if workspace_path is None:
        workspace_path = str(Path.cwd())
    if data_path is None:
        data_path = str(Path(workspace_path) / "data")
    
    container.register_singleton(
        'model_repository',
        lambda: ModelRepository(workspace_path=workspace_path)
    )
    
    container.register_singleton(
        'simulation_data_repository',
        lambda: SimulationDataRepository(data_path=data_path)
    )


def register_builders(container: ServiceContainer):
    """Register builder classes only.
    
    Registers builder classes that don't require constructor arguments.
    PlaceBuilder and TransitionBuilder are not registered since they require
    id/name parameters - create them directly as needed.
    
    Registers:
    - arc_builder_class: ArcBuilder class
    - petri_net_builder_class: PetriNetBuilder class
    - simulation_config_builder_class: SimulationConfigBuilder class
    
    Args:
        container: ServiceContainer to register services with
    
    Example:
        >>> container = ServiceContainer()
        >>> register_builders(container)
        >>> ArcBuilder = container.get('arc_builder_class')
        >>> builder = ArcBuilder()
    """
    from shypn.builders import (
        ArcBuilder,
        PetriNetBuilder,
        SimulationConfigBuilder,
    )
    
    container.register_instance('arc_builder_class', ArcBuilder)
    container.register_instance('petri_net_builder_class', PetriNetBuilder)
    container.register_instance('simulation_config_builder_class', SimulationConfigBuilder)
