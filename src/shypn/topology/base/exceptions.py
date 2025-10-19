"""Exceptions for topology analysis."""


class TopologyError(Exception):
    """Base exception for topology analysis errors."""
    pass


class TopologyAnalysisError(TopologyError):
    """Exception raised when topology analysis fails."""
    pass


class InvalidModelError(TopologyError):
    """Exception raised when model is invalid for analysis."""
    pass


class AnalysisTimeoutError(TopologyError):
    """Exception raised when analysis times out."""
    pass
