"""
Service Container - Lightweight Dependency Injection

Provides a simple dependency injection container for managing service lifetimes
and dependencies. Supports singleton and transient service registration.

Part of Phase 3.3: Dependency Injection Framework.

Example:
    # Create container
    container = ServiceContainer()
    
    # Register singleton (created once, reused)
    container.register_singleton(
        'model_repository',
        lambda: ModelRepository("/workspace")
    )
    
    # Register transient (created per request)
    container.register_transient(
        'petri_net_builder',
        lambda: PetriNetBuilder()
    )
    
    # Register existing instance
    container.register_instance('event_bus', EventBus)
    
    # Resolve services
    repo = container.get('model_repository')
    builder = container.get('petri_net_builder')
"""

from typing import Any, Callable, Dict, Optional, Set
from enum import Enum


class ServiceLifetime(Enum):
    """Service lifetime enumeration."""
    SINGLETON = "singleton"  # Created once, reused
    TRANSIENT = "transient"  # Created per request
    INSTANCE = "instance"    # Pre-existing instance


class ServiceContainer:
    """Lightweight dependency injection container.
    
    Manages service registration and resolution with support for:
    - Singleton services (created once, shared)
    - Transient services (created per request)
    - Instance registration (existing objects)
    
    Services are resolved by name (string keys) and created using
    factory functions (callables).
    
    Attributes:
        _singletons: Dictionary of singleton instances
        _factories: Dictionary of factory functions
        _lifetimes: Dictionary of service lifetimes
        _resolving: Set of services currently being resolved (cycle detection)
    
    Example:
        container = ServiceContainer()
        
        # Register services
        container.register_singleton('repo', lambda: ModelRepository("/ws"))
        container.register_transient('builder', lambda: PetriNetBuilder())
        
        # Resolve services
        repo = container.get('repo')
        builder = container.get('builder')
    """
    
    def __init__(self):
        """Initialize empty service container."""
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._lifetimes: Dict[str, ServiceLifetime] = {}
        self._resolving: Set[str] = set()  # For cycle detection
    
    def register_singleton(self, name: str, factory: Callable[[], Any]) -> 'ServiceContainer':
        """Register singleton service (created once, reused).
        
        The factory is called on first get() and the result is cached.
        Subsequent get() calls return the same instance.
        
        Args:
            name: Service name/key
            factory: Callable that creates the service (takes no args)
        
        Returns:
            self for method chaining
        
        Example:
            >>> container.register_singleton('repo', lambda: ModelRepository("/ws"))
        """
        self._factories[name] = factory
        self._lifetimes[name] = ServiceLifetime.SINGLETON
        return self
    
    def register_transient(self, name: str, factory: Callable[[], Any]) -> 'ServiceContainer':
        """Register transient service (created per request).
        
        The factory is called on every get() and a new instance is returned.
        
        Args:
            name: Service name/key
            factory: Callable that creates the service (takes no args)
        
        Returns:
            self for method chaining
        
        Example:
            >>> container.register_transient('builder', lambda: PetriNetBuilder())
        """
        self._factories[name] = factory
        self._lifetimes[name] = ServiceLifetime.TRANSIENT
        return self
    
    def register_instance(self, name: str, instance: Any) -> 'ServiceContainer':
        """Register existing instance as singleton.
        
        The instance is stored directly and returned on get().
        
        Args:
            name: Service name/key
            instance: Pre-existing service instance
        
        Returns:
            self for method chaining
        
        Example:
            >>> container.register_instance('event_bus', EventBus)
        """
        self._singletons[name] = instance
        self._lifetimes[name] = ServiceLifetime.INSTANCE
        return self
    
    def get(self, name: str) -> Any:
        """Resolve service by name.
        
        Behavior depends on service lifetime:
        - Singleton: Returns cached instance (creates on first call)
        - Transient: Creates and returns new instance
        - Instance: Returns registered instance
        
        Args:
            name: Service name/key
        
        Returns:
            Service instance
        
        Raises:
            ServiceNotFoundError: If service not registered
            CircularDependencyError: If circular dependency detected
        
        Example:
            >>> repo = container.get('model_repository')
        """
        # Check if service registered
        if name not in self._lifetimes:
            raise ServiceNotFoundError(name)
        
        # Detect circular dependencies
        if name in self._resolving:
            raise CircularDependencyError(name, self._resolving)
        
        lifetime = self._lifetimes[name]
        
        # Return existing instance (singleton or pre-registered)
        if lifetime == ServiceLifetime.INSTANCE:
            return self._singletons[name]
        
        if lifetime == ServiceLifetime.SINGLETON:
            # Return cached instance if exists
            if name in self._singletons:
                return self._singletons[name]
            
            # Create and cache singleton
            self._resolving.add(name)
            try:
                instance = self._factories[name]()
                self._singletons[name] = instance
                return instance
            finally:
                self._resolving.discard(name)
        
        # Create transient instance
        if lifetime == ServiceLifetime.TRANSIENT:
            self._resolving.add(name)
            try:
                return self._factories[name]()
            finally:
                self._resolving.discard(name)
        
        # Should never reach here
        raise ServiceContainerError(f"Unknown lifetime: {lifetime}")
    
    def has(self, name: str) -> bool:
        """Check if service is registered.
        
        Args:
            name: Service name/key
        
        Returns:
            True if service registered, False otherwise
        
        Example:
            >>> if container.has('repo'):
            ...     repo = container.get('repo')
        """
        return name in self._lifetimes
    
    def get_optional(self, name: str) -> Optional[Any]:
        """Resolve service if registered, otherwise return None.
        
        Args:
            name: Service name/key
        
        Returns:
            Service instance if registered, None otherwise
        
        Example:
            >>> repo = container.get_optional('repo')
            >>> if repo is not None:
            ...     # Use repo
        """
        if not self.has(name):
            return None
        return self.get(name)
    
    def clear(self):
        """Clear all services and singletons.
        
        Useful for testing or resetting the container.
        Removes all registrations and cached singletons.
        
        Example:
            >>> container.clear()  # Reset for next test
        """
        self._singletons.clear()
        self._factories.clear()
        self._lifetimes.clear()
        self._resolving.clear()
    
    def list_services(self) -> list[str]:
        """Get list of all registered service names.
        
        Returns:
            List of service names
        
        Example:
            >>> services = container.list_services()
            >>> ['model_repository', 'simulation_data_repository', 'event_bus']
        """
        return list(self._lifetimes.keys())
    
    def get_lifetime(self, name: str) -> Optional[ServiceLifetime]:
        """Get service lifetime.
        
        Args:
            name: Service name/key
        
        Returns:
            ServiceLifetime if registered, None otherwise
        
        Example:
            >>> lifetime = container.get_lifetime('repo')
            >>> assert lifetime == ServiceLifetime.SINGLETON
        """
        return self._lifetimes.get(name)
    
    def __repr__(self) -> str:
        """Get string representation for debugging."""
        service_count = len(self._lifetimes)
        singleton_count = sum(1 for lt in self._lifetimes.values() 
                             if lt == ServiceLifetime.SINGLETON)
        transient_count = sum(1 for lt in self._lifetimes.values() 
                             if lt == ServiceLifetime.TRANSIENT)
        instance_count = sum(1 for lt in self._lifetimes.values() 
                            if lt == ServiceLifetime.INSTANCE)
        
        return (f"ServiceContainer(services={service_count}, "
                f"singletons={singleton_count}, "
                f"transients={transient_count}, "
                f"instances={instance_count})")


# Global container instance (can be overridden for testing)
_global_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """Get global service container.
    
    Creates container on first call. Use set_container() to override
    (useful for testing).
    
    Returns:
        Global ServiceContainer instance
    
    Example:
        >>> container = get_container()
        >>> repo = container.get('model_repository')
    """
    global _global_container
    if _global_container is None:
        _global_container = ServiceContainer()
    return _global_container


def set_container(container: ServiceContainer):
    """Set global service container.
    
    Used primarily for testing to inject mock containers.
    
    Args:
        container: ServiceContainer to use as global
    
    Example:
        >>> test_container = ServiceContainer()
        >>> set_container(test_container)  # Use in tests
    """
    global _global_container
    _global_container = container


def reset_container():
    """Reset global container to None.
    
    Forces new container creation on next get_container() call.
    Useful for test isolation.
    
    Example:
        >>> reset_container()  # Clean slate for next test
    """
    global _global_container
    _global_container = None


# ===== Exceptions =====

class ServiceContainerError(Exception):
    """Base exception for service container errors."""
    pass


class ServiceNotFoundError(ServiceContainerError):
    """Raised when service cannot be found."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__(f"Service not found: {service_name}")


class CircularDependencyError(ServiceContainerError):
    """Raised when circular dependency detected."""
    
    def __init__(self, service_name: str, resolving_chain: Set[str]):
        self.service_name = service_name
        self.resolving_chain = resolving_chain
        chain_str = " -> ".join(sorted(resolving_chain))
        super().__init__(
            f"Circular dependency detected while resolving '{service_name}'. "
            f"Resolution chain: {chain_str}"
        )
