"""
Runtime compatibility checking for shypn package and submodules.

This module provides utilities to verify that all components are using
compatible API versions, preventing runtime errors due to version mismatches.
"""

from typing import Tuple
import logging
import warnings

logger = logging.getLogger(__name__)


class CompatibilityError(Exception):
    """Raised when incompatible versions are detected."""
    pass


class CompatibilityWarning(UserWarning):
    """Warning for potentially incompatible versions."""
    pass


def parse_version(version_str: str) -> Tuple[int, int, int]:
    """
    Parse semantic version string into (major, minor, patch) tuple.
    
    Args:
        version_str: Version string in format "MAJOR.MINOR.PATCH"
        
    Returns:
        Tuple of (major, minor, patch) integers
        
    Raises:
        ValueError: If version string is not valid semantic version
    """
    try:
        parts = version_str.strip().split('.')
        if len(parts) != 3:
            raise ValueError(f"Version must have 3 parts, got {len(parts)}")
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid version string '{version_str}': {e}")


def check_compatibility(
    module_name: str,
    actual_version: str,
    required_version: str,
    strict: bool = False
) -> bool:
    """
    Check if actual version is compatible with required version.
    
    Compatibility rules (semantic versioning):
    - MAJOR version must match exactly (breaking changes)
    - MINOR version can be >= required (backward compatible features)
    - PATCH version is ignored (bug fixes only)
    
    Args:
        module_name: Name of the module being checked
        actual_version: Version string of the installed module
        required_version: Minimum required version string
        strict: If True, raise CompatibilityError; if False, issue warning
        
    Returns:
        True if compatible, False otherwise
        
    Raises:
        CompatibilityError: If versions are incompatible and strict=True
    """
    try:
        actual_maj, actual_min, actual_patch = parse_version(actual_version)
        required_maj, required_min, required_patch = parse_version(required_version)
        
        # Major version must match exactly
        if actual_maj != required_maj:
            msg = (
                f"{module_name} version incompatibility detected:\n"
                f"  Installed: {actual_version} (MAJOR {actual_maj})\n"
                f"  Required:  {required_version} (MAJOR {required_maj})\n"
                f"  Major version mismatch indicates breaking API changes."
            )
            if strict:
                raise CompatibilityError(msg)
            else:
                warnings.warn(msg, CompatibilityWarning, stacklevel=2)
                return False
        
        # Minor version must be >= required (backward compatible)
        if actual_min < required_min:
            msg = (
                f"{module_name} version may be incompatible:\n"
                f"  Installed: {actual_version} (MINOR {actual_min})\n"
                f"  Required:  {required_version} (MINOR {required_min})\n"
                f"  Some features may be missing."
            )
            if strict:
                raise CompatibilityError(msg)
            else:
                warnings.warn(msg, CompatibilityWarning, stacklevel=2)
                return False
        
        return True
        
    except ValueError as e:
        msg = f"Cannot check compatibility for {module_name}: {e}"
        if strict:
            raise CompatibilityError(msg)
        else:
            warnings.warn(msg, CompatibilityWarning, stacklevel=2)
            return False


def verify_submodule_compatibility(strict: bool = False) -> bool:
    """
    Verify that all shypn submodules are compatible with the main package.
    
    Args:
        strict: If True, raise errors on incompatibility; if False, issue warnings
        
    Returns:
        True if all submodules are compatible, False otherwise
        
    Raises:
        CompatibilityError: If any submodule is incompatible and strict=True
    """
    from shypn.version import __required_engine_version__, __required_crossfetch_version__
    
    all_compatible = True
    
    # Check engine compatibility
    try:
        from shypn.engine import __version__ as engine_version
        if not check_compatibility(
            "shypn.engine",
            engine_version,
            __required_engine_version__,
            strict=strict
        ):
            all_compatible = False
    except ImportError:
        msg = "shypn.engine not found - skipping compatibility check"
        warnings.warn(msg, CompatibilityWarning, stacklevel=2)
    
    # Check crossfetch compatibility
    try:
        from shypn.crossfetch import __version__ as crossfetch_version
        if not check_compatibility(
            "shypn.crossfetch",
            crossfetch_version,
            __required_crossfetch_version__,
            strict=strict
        ):
            all_compatible = False
    except ImportError:
        msg = "shypn.crossfetch not found - skipping compatibility check"
        warnings.warn(msg, CompatibilityWarning, stacklevel=2)
    
    return all_compatible


# Automatically check compatibility on import (non-strict by default)
def _auto_check_compatibility():
    """Automatically verify compatibility when module is imported."""
    try:
        verify_submodule_compatibility(strict=False)
    except Exception as e:
        # Don't let compatibility checking break imports
        logger.debug("Compatibility check failed (non-fatal): %s", e)


# Run auto-check on import
_auto_check_compatibility()
