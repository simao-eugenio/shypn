"""
Base Classes for Buffered Parameter System

Defines core abstractions for transaction-safe parameter updates.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class ValidationError(Exception):
    """Raised when parameter validation fails."""
    pass


class BufferStrategy(ABC):
    """Abstract strategy for buffering parameter changes.
    
    Subclasses can implement different buffering strategies:
    - Immediate: Apply changes immediately (no buffering)
    - Manual: Buffer until explicit commit
    - Debounced: Buffer and auto-commit after delay
    """
    
    @abstractmethod
    def should_buffer(self) -> bool:
        """Check if changes should be buffered.
        
        Returns:
            bool: True to buffer changes, False to apply immediately
        """
        pass
    
    @abstractmethod
    def should_commit(self) -> bool:
        """Check if buffered changes should be committed.
        
        Returns:
            bool: True to commit now, False to keep buffering
        """
        pass


class SettingsCloner(ABC):
    """Abstract interface for cloning settings objects.
    
    Different settings classes may need different cloning strategies.
    """
    
    @abstractmethod
    def clone(self, settings: Any) -> Any:
        """Create a deep copy of settings.
        
        Args:
            settings: Settings object to clone
        
        Returns:
            Any: Independent copy of settings
        """
        pass


class SettingsValidator(ABC):
    """Abstract interface for settings validation.
    
    Subclasses implement validation logic specific to their settings type.
    """
    
    @abstractmethod
    def validate(self, settings: Any) -> tuple[bool, str]:
        """Validate settings object.
        
        Args:
            settings: Settings object to validate
        
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        pass
    
    @abstractmethod
    def validate_cross_constraints(self, settings: Any) -> tuple[bool, str]:
        """Validate cross-property constraints.
        
        Some validations require checking multiple properties together
        (e.g., duration/dt combination producing too many steps).
        
        Args:
            settings: Settings object to validate
        
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        pass


class ChangeListener(ABC):
    """Abstract interface for listening to parameter changes."""
    
    @abstractmethod
    def on_parameter_changed(self, parameter_name: str, old_value: Any, new_value: Any):
        """Called when a parameter changes.
        
        Args:
            parameter_name: Name of parameter that changed
            old_value: Previous value
            new_value: New value
        """
        pass
    
    @abstractmethod
    def on_changes_committed(self, changes: Dict[str, tuple[Any, Any]]):
        """Called when buffered changes are committed.
        
        Args:
            changes: Dict mapping parameter names to (old_value, new_value) tuples
        """
        pass
    
    @abstractmethod
    def on_changes_rolled_back(self, changes: Dict[str, tuple[Any, Any]]):
        """Called when buffered changes are rolled back.
        
        Args:
            changes: Dict mapping parameter names to (old_value, new_value) tuples
        """
        pass
