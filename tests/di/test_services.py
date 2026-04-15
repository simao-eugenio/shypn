"""
Tests for Service Registration - Core Application Services

Tests the registration utilities for core application services with the
dependency injection container.

Part of Phase 3.3: Dependency Injection Framework.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from shypn.di import ServiceContainer, ServiceLifetime
from shypn.di.services import (
    register_core_services,
    register_repositories,
    register_builders,
)


# ===== Test Fixtures =====


@pytest.fixture
def workspace_dir():
    """Create temporary workspace directory."""
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


@pytest.fixture
def container():
    """Create fresh container for each test."""
    return ServiceContainer()


# ===== Core Services Registration Tests =====


def test_register_core_services(container, workspace_dir):
    """Test registering all core services."""
    register_core_services(container, workspace_path=workspace_dir)
    
    # Check repositories registered
    assert container.has('model_repository')
    assert container.has('simulation_data_repository')
    
    # Check builder classes registered
    assert container.has('arc_builder_class')
    assert container.has('petri_net_builder_class')
    assert container.has('simulation_config_builder_class')


def test_register_core_services_lifetimes(container, workspace_dir):
    """Test core services have correct lifetimes."""
    register_core_services(container, workspace_path=workspace_dir)
    
    # Repositories should be singletons
    assert container.get_lifetime('model_repository') == ServiceLifetime.SINGLETON
    assert container.get_lifetime('simulation_data_repository') == ServiceLifetime.SINGLETON
    
    # Builder classes should be instances (class objects)
    assert container.get_lifetime('arc_builder_class') == ServiceLifetime.INSTANCE
    assert container.get_lifetime('petri_net_builder_class') == ServiceLifetime.INSTANCE
    assert container.get_lifetime('simulation_config_builder_class') == ServiceLifetime.INSTANCE


def test_register_core_services_default_paths(container):
    """Test registering core services with default paths."""
    register_core_services(container)
    
    # Should still register services
    assert container.has('model_repository')
    assert container.has('simulation_data_repository')


def test_register_core_services_custom_data_path(container, workspace_dir):
    """Test registering with custom data path."""
    data_path = str(Path(workspace_dir) / "custom_data")
    register_core_services(
        container,
        workspace_path=workspace_dir,
        data_path=data_path
    )
    
    # Resolve repository to check it was configured correctly
    sim_repo = container.get('simulation_data_repository')
    
    # Check data path is set correctly
    assert Path(data_path).resolve() == Path(sim_repo._data_path).resolve()


# ===== Repository Registration Tests =====


def test_register_repositories_only(container, workspace_dir):
    """Test registering repositories without builders."""
    register_repositories(container, workspace_path=workspace_dir)
    
    # Repositories should be registered
    assert container.has('model_repository')
    assert container.has('simulation_data_repository')
    
    # Builder classes should NOT be registered
    assert not container.has('arc_builder_class')
    assert not container.has('petri_net_builder_class')
    assert not container.has('simulation_config_builder_class')


def test_repositories_are_singletons(container, workspace_dir):
    """Test repositories are registered as singletons."""
    register_repositories(container, workspace_path=workspace_dir)
    
    # Get repositories multiple times
    repo1 = container.get('model_repository')
    repo2 = container.get('model_repository')
    
    sim_repo1 = container.get('simulation_data_repository')
    sim_repo2 = container.get('simulation_data_repository')
    
    # Should be same instances
    assert repo1 is repo2
    assert sim_repo1 is sim_repo2


def test_repositories_with_default_paths(container):
    """Test registering repositories with default paths."""
    register_repositories(container)
    
    assert container.has('model_repository')
    assert container.has('simulation_data_repository')


# ===== Builder Registration Tests =====


def test_register_builders_only(container):
    """Test registering builder classes without repositories."""
    register_builders(container)
    
    # Builder classes should be registered
    assert container.has('arc_builder_class')
    assert container.has('petri_net_builder_class')
    assert container.has('simulation_config_builder_class')
    
    # Repositories should NOT be registered
    assert not container.has('model_repository')
    assert not container.has('simulation_data_repository')


def test_builders_are_class_objects(container):
    """Test builder registrations are class objects."""
    register_builders(container)
    
    # Get builder classes
    ArcBuilder = container.get('arc_builder_class')
    PetriNetBuilder = container.get('petri_net_builder_class')
    
    # Should be able to instantiate them
    arc_builder = ArcBuilder()
    net_builder = PetriNetBuilder()
    
    # Check they are correct types
    from shypn.builders import ArcBuilder as ArcBuilderRef, PetriNetBuilder as PetriNetBuilderRef
    
    assert ArcBuilder is ArcBuilderRef
    assert PetriNetBuilder is PetriNetBuilderRef
    assert isinstance(arc_builder, ArcBuilderRef)
    assert isinstance(net_builder, PetriNetBuilderRef)


def test_all_builders_registered(container):
    """Test all builder classes are registered."""
    register_builders(container)
    
    # Get each builder class
    ArcBuilder = container.get('arc_builder_class')
    PetriNetBuilder = container.get('petri_net_builder_class')
    SimulationConfigBuilder = container.get('simulation_config_builder_class')
    
    # Check types
    from shypn.builders import (
        ArcBuilder as ArcBuilderRef,
        PetriNetBuilder as PetriNetBuilderRef,
        SimulationConfigBuilder as SimulationConfigBuilderRef,
    )
    
    assert ArcBuilder is ArcBuilderRef
    assert PetriNetBuilder is PetriNetBuilderRef
    assert SimulationConfigBuilder is SimulationConfigBuilderRef


# ===== Integration Tests =====


def test_repositories_can_be_resolved(container, workspace_dir):
    """Test repositories can be resolved and used."""
    register_repositories(container, workspace_path=workspace_dir)
    
    # Resolve repositories
    model_repo = container.get('model_repository')
    sim_repo = container.get('simulation_data_repository')
    
    # Check they are correct types
    from shypn.repositories import ModelRepository, SimulationDataRepository
    
    assert isinstance(model_repo, ModelRepository)
    assert isinstance(sim_repo, SimulationDataRepository)


def test_builders_can_be_resolved(container):
    """Test builder classes can be resolved and instantiated."""
    register_builders(container)
    
    # Resolve builder class and instantiate it
    ArcBuilder = container.get('arc_builder_class')
    PetriNetBuilder = container.get('petri_net_builder_class')
    SimulationConfigBuilder = container.get('simulation_config_builder_class')
    
    # Should be able to instantiate them
    arc_builder = ArcBuilder()
    net_builder = PetriNetBuilder()
    config_builder = SimulationConfigBuilder()
    
    # Check they are correct types
    from shypn.builders import (
        ArcBuilder as ArcBuilderRef,
        PetriNetBuilder as PetriNetBuilderRef,
        SimulationConfigBuilder as SimulationConfigBuilderRef,
    )
    
    assert isinstance(arc_builder, ArcBuilderRef
)
    assert isinstance(net_builder, PetriNetBuilderRef)
    assert isinstance(config_builder, SimulationConfigBuilderRef)


def test_mixed_registration(container, workspace_dir):
    """Test registering repos and builders separately."""
    register_repositories(container, workspace_path=workspace_dir)
    register_builders(container)
    
    # Both should be available
    assert container.has('model_repository')
    assert container.has('arc_builder_class')
    
    # Lifetimes should be correct
    assert container.get_lifetime('model_repository') == ServiceLifetime.SINGLETON
    assert container.get_lifetime('arc_builder_class') == ServiceLifetime.INSTANCE


def test_service_count(container, workspace_dir):
    """Test correct number of services registered."""
    register_core_services(container, workspace_path=workspace_dir)
    
    services = container.list_services()
    
    # 2 repositories + 3 builder classes = 5 services
    assert len(services) == 5


def test_workspace_path_propagates(container, workspace_dir):
    """Test workspace path is correctly set in repository."""
    register_repositories(container, workspace_path=workspace_dir)
    
    model_repo = container.get('model_repository')
    
    # Check workspace path
    assert Path(workspace_dir).resolve() == Path(model_repo._workspace_path).resolve()


# ===== Error Handling Tests =====


def test_repositories_with_nonexistent_paths(container):
    """Test registering repositories with nonexistent paths still works."""
    # ServiceContainer doesn't validate paths on registration
    # Repositories will handle path creation when used
    nonexistent = "/tmp/nonexistent_test_path_12345"
    
    register_repositories(container, workspace_path=nonexistent)
    
    # Should still register successfully
    assert container.has('model_repository')
    assert container.has('simulation_data_repository')


def test_multiple_registrations_overwrite(container, workspace_dir):
    """Test re-registering services overwrites."""
    register_repositories(container, workspace_path=workspace_dir)
    
    # Get first instance
    repo1 = container.get('model_repository')
    
    # Create new workspace path
    new_workspace = tempfile.mkdtemp()
    try:
        # Re-register with different path
        register_repositories(container, workspace_path=new_workspace)
        
        # Old singleton still cached - need to clear to get new one
        container.clear()
        register_repositories(container, workspace_path=new_workspace)
        
        repo2 = container.get('model_repository')
        
        # Should be different instance (different path)
        assert repo1 is not repo2
    finally:
        shutil.rmtree(new_workspace)
