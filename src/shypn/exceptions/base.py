"""Base exception for the SHYPN exception hierarchy."""


class ShypnError(Exception):
    """Base exception for all SHYPN errors.

    All SHYPN-specific exceptions should inherit from this class.
    This allows catching all SHYPN errors with a single except clause.
    """
    pass
