"""
Deprecation tracking and warning system for shypn.

This module provides utilities to mark APIs as deprecated and track their
lifecycle through version changes. It helps maintain backward compatibility
while guiding users toward modern APIs.

Usage:
    from shypn.deprecation import deprecated
    
    @deprecated(
        deprecated_in="2.5.0",
        removed_in="3.0.0",
        replacement="new_function()",
        reason="Old implementation was inefficient"
    )
    def old_function():
        pass
"""

import warnings
import functools
from typing import Optional, Callable, Dict, Any


class DeprecationRegistry:
    """Central registry for deprecated APIs."""
    
    def __init__(self):
        self._deprecated_apis: Dict[str, Dict[str, Any]] = {}
    
    def register(
        self,
        api_name: str,
        deprecated_in: str,
        removed_in: str,
        replacement: Optional[str] = None,
        reason: Optional[str] = None
    ):
        """
        Register a deprecated API.
        
        Args:
            api_name: Full qualified name of the API
            deprecated_in: Version when API was deprecated
            removed_in: Version when API will be removed
            replacement: Suggested replacement API (optional)
            reason: Reason for deprecation (optional)
        """
        self._deprecated_apis[api_name] = {
            'deprecated_in': deprecated_in,
            'removed_in': removed_in,
            'replacement': replacement,
            'reason': reason
        }
    
    def get_deprecation_message(self, api_name: str) -> str:
        """
        Get deprecation message for an API.
        
        Args:
            api_name: Full qualified name of the API
            
        Returns:
            Formatted deprecation message
        """
        if api_name not in self._deprecated_apis:
            return ""
        
        info = self._deprecated_apis[api_name]
        msg = (
            f"{api_name} is deprecated since version {info['deprecated_in']} "
            f"and will be removed in version {info['removed_in']}."
        )
        
        if info['replacement']:
            msg += f" Use {info['replacement']} instead."
        
        if info['reason']:
            msg += f" Reason: {info['reason']}"
        
        return msg
    
    def get_all_deprecated(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all registered deprecated APIs.
        
        Returns:
            Dictionary mapping API names to their deprecation info
        """
        return self._deprecated_apis.copy()
    
    def is_deprecated(self, api_name: str) -> bool:
        """
        Check if an API is deprecated.
        
        Args:
            api_name: Full qualified name of the API
            
        Returns:
            True if API is deprecated, False otherwise
        """
        return api_name in self._deprecated_apis


# Global registry instance
_registry = DeprecationRegistry()


def deprecated(
    deprecated_in: str,
    removed_in: str,
    replacement: Optional[str] = None,
    reason: Optional[str] = None
):
    """
    Decorator to mark functions/methods as deprecated.
    
    This decorator will emit a DeprecationWarning when the decorated function
    is called, providing information about when it was deprecated, when it
    will be removed, and what to use instead.
    
    Args:
        deprecated_in: Version when the API was deprecated (e.g., "2.5.0")
        removed_in: Version when the API will be removed (e.g., "3.0.0")
        replacement: Suggested replacement API (e.g., "new_function()")
        reason: Reason for deprecation (e.g., "Old implementation was inefficient")
    
    Returns:
        Decorator function
    
    Example:
        @deprecated(
            deprecated_in="2.5.0",
            removed_in="3.0.0",
            replacement="new_function()",
            reason="Old implementation was inefficient"
        )
        def old_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        # Register the API in the global registry
        api_name = f"{func.__module__}.{func.__qualname__}"
        _registry.register(api_name, deprecated_in, removed_in, replacement, reason)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            msg = _registry.get_deprecation_message(api_name)
            warnings.warn(msg, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        
        # Mark the wrapper as deprecated for introspection
        wrapper.__deprecated__ = True
        wrapper.__deprecated_info__ = {
            'deprecated_in': deprecated_in,
            'removed_in': removed_in,
            'replacement': replacement,
            'reason': reason
        }
        
        return wrapper
    
    return decorator


def get_deprecated_apis() -> Dict[str, Dict[str, Any]]:
    """
    Get all registered deprecated APIs.
    
    Returns:
        Dictionary mapping API names to their deprecation info
    """
    return _registry.get_all_deprecated()


def is_deprecated(func: Callable) -> bool:
    """
    Check if a function is marked as deprecated.
    
    Args:
        func: Function to check
        
    Returns:
        True if function is deprecated, False otherwise
    """
    return hasattr(func, '__deprecated__') and func.__deprecated__


def get_deprecation_info(func: Callable) -> Optional[Dict[str, Any]]:
    """
    Get deprecation information for a function.
    
    Args:
        func: Function to get info for
        
    Returns:
        Deprecation info dict or None if not deprecated
    """
    if is_deprecated(func):
        return func.__deprecated_info__
    return None
