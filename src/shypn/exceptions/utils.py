"""Utility functions for working with SHYPN exceptions."""

from shypn.exceptions.base import ShypnError


def format_exception_chain(exc: Exception) -> str:
    """Format exception chain for logging.

    Args:
        exc: Exception instance

    Returns:
        Formatted string with full exception chain

    Example:
        >>> try:
        ...     raise SimulationError("Failed") from ValueError("Bad value")
        ... except SimulationError as e:
        ...     print(format_exception_chain(e))
        SimulationError: Failed
        Caused by: ValueError: Bad value
    """
    parts = [f"{type(exc).__name__}: {exc}"]

    cause = exc.__cause__
    while cause:
        parts.append(f"Caused by: {type(cause).__name__}: {cause}")
        cause = cause.__cause__

    return "\n".join(parts)


def is_shypn_error(exc: Exception) -> bool:
    """Check if exception is a SHYPN-specific error.

    Args:
        exc: Exception instance

    Returns:
        True if exception is a ShypnError subclass

    Example:
        >>> is_shypn_error(SimulationError("test"))
        True
        >>> is_shypn_error(ValueError("test"))
        False
    """
    return isinstance(exc, ShypnError)
