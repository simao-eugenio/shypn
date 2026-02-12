"""
Dependency Injection Framework

Provides lightweight dependency injection for managing service lifetimes
and dependencies throughout the application.

Part of Phase 3.3: Dependency Injection Framework.

Example:
    from shypn.di import ServiceContainer, get_container
    
    # Get global container
    container = get_container()
    
    # Register services
    container.register_singleton('repo', lambda: ModelRepository("/ws"))
    container.register_transient('builder', lambda: PetriNetBuilder())
    
    # Resolve services
    repo = container.get('repo')
"""

from shypn.di.service_container import (
    ServiceContainer,
    ServiceLifetime,
    get_container,
    set_container,
    reset_container,
    ServiceContainerError,
    ServiceNotFoundError,
    CircularDependencyError,
)

from shypn.di.services import (
    register_core_services,
    register_repositories,
    register_builders,
)

__all__ = [
    'ServiceContainer',
    'ServiceLifetime',
    'get_container',
    'set_container',
    'reset_container',
    'ServiceContainerError',
    'ServiceNotFoundError',
    'CircularDependencyError',
    'register_core_services',
    'register_repositories',
    'register_builders',
]
