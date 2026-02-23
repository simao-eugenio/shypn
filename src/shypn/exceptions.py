"""Custom exception hierarchy for SHYPN.

This module provides a structured exception hierarchy for the entire SHYPN project.
All custom exceptions inherit from ShypnError to allow catching all SHYPN-specific errors.

Exception Hierarchy:
    ShypnError (base)
    ├── ModelError (model structure/validation)
    ├── SimulationError (simulation execution)
    │   ├── SimulationSetupError
    │   ├── SimulationRuntimeError
    │   └── SimulationTimeoutError
    ├── DataValidationError (data validation/parsing)
    │   ├── ExpressionError
    │   └── ParameterError
    ├── ImportExportError (file I/O operations)
    │   ├── FileFormatError
    │   ├── ParseError
    │   └── ExportError
    ├── ThermodynamicsError (thermodynamic calculations)
    │   ├── CompoundNotFoundError
    │   └── ThermodynamicConstraintError
    ├── KEGGError (KEGG API/data errors)
    │   ├── KEGGConnectionError
    │   └── KEGGDataError
    ├── DocumentError (document lifecycle - use carefully)
    └── EventBusError (EventBus issues - should be rare)

Usage:
    from shypn.exceptions import SimulationError, ModelError
    
    try:
        run_simulation(model)
    except SimulationError as e:
        logger.error(f"Simulation failed: {e}")
        # Handle gracefully
    except ModelError as e:
        logger.error(f"Invalid model: {e}")
        # Show error to user
"""


class ShypnError(Exception):
    """Base exception for all SHYPN errors.
    
    All SHYPN-specific exceptions should inherit from this class.
    This allows catching all SHYPN errors with a single except clause.
    """
    pass


# ============================================================================
# Model-related errors
# ============================================================================

class ModelError(ShypnError):
    """Errors related to model structure or validation.
    
    Raised when:
    - Model structure is invalid (missing required elements)
    - Model validation fails
    - Model constraints are violated
    - Inconsistent model state
    """
    pass


# ============================================================================
# Simulation-related errors
# ============================================================================

class SimulationError(ShypnError):
    """Base class for errors during simulation execution.
    
    Raised when simulation cannot complete successfully.
    """
    pass


class SimulationSetupError(SimulationError):
    """Errors during simulation setup/initialization.
    
    Raised when:
    - Simulation parameters are invalid
    - Initial state is invalid
    - Required resources are unavailable
    """
    pass


class SimulationRuntimeError(SimulationError):
    """Errors during simulation execution.
    
    Raised when:
    - Numerical instability occurs
    - Deadlock detected
    - Invalid state transition
    - Integration fails
    """
    pass


class SimulationTimeoutError(SimulationError):
    """Simulation exceeded time limit.
    
    Raised when simulation takes longer than configured timeout.
    """
    pass


# ============================================================================
# Data validation errors
# ============================================================================

class DataValidationError(ShypnError):
    """Errors in data validation or parsing.
    
    Raised when input data fails validation checks.
    """
    pass


class ExpressionError(DataValidationError):
    """Invalid mathematical expression.
    
    Raised when:
    - Rate function syntax is invalid
    - Guard expression cannot be parsed
    - Assignment rule is malformed
    """
    pass


class ParameterError(DataValidationError):
    """Invalid parameter value or configuration.
    
    Raised when:
    - Parameter value is out of valid range
    - Required parameter is missing
    - Parameter type is incorrect
    """
    pass


# ============================================================================
# Import/Export errors
# ============================================================================

class ImportExportError(ShypnError):
    """Errors during import or export operations.
    
    Base class for all file I/O related errors.
    """
    pass


class FileFormatError(ImportExportError):
    """Unsupported or invalid file format.
    
    Raised when:
    - File format is not recognized
    - File structure is invalid
    - Required file elements are missing
    """
    pass


class ParseError(ImportExportError):
    """Error parsing file content.
    
    Raised when file content cannot be parsed correctly.
    """
    pass


class ExportError(ImportExportError):
    """Error exporting model or data.
    
    Raised when export operation fails.
    """
    pass


# ============================================================================
# Thermodynamics errors
# ============================================================================

class ThermodynamicsError(ShypnError):
    """Errors in thermodynamic calculations.
    
    Raised when thermodynamic analysis or validation fails.
    """
    pass


class CompoundNotFoundError(ThermodynamicsError):
    """Compound not found in database.
    
    Raised when requested compound ID is not in the database.
    """
    pass


class ThermodynamicConstraintError(ThermodynamicsError):
    """Thermodynamic constraint violated.
    
    Raised when:
    - Gibbs free energy constraint violated
    - Entropy production is negative
    - Energy conservation violated
    """
    pass


# ============================================================================
# External API errors
# ============================================================================

class KEGGError(ShypnError):
    """Errors related to KEGG API or data.
    
    Base class for KEGG-related errors.
    """
    pass


class KEGGConnectionError(KEGGError):
    """Cannot connect to KEGG API.
    
    Raised when:
    - Network connection fails
    - KEGG API is unavailable
    - Request times out
    """
    pass


class KEGGDataError(KEGGError):
    """Invalid or unexpected KEGG data.
    
    Raised when:
    - KEGG response is malformed
    - Expected data is missing
    - Data format is unexpected
    """
    pass


# ============================================================================
# Architecture-specific errors (USE CAREFULLY)
# ============================================================================

class DocumentError(ShypnError):
    """Errors in document lifecycle management.
    
    ⚠️ WARNING: Use this exception carefully!
    
    This should ONLY be used for document-specific errors in the
    Multi-Document Architecture. Most errors should use more specific
    exception types (ModelError, SimulationError, etc.)
    
    Raised when:
    - Document cannot be created
    - Document state is invalid
    - Document cleanup fails
    """
    pass


class EventBusError(ShypnError):
    """Errors in EventBus operation.
    
    ⚠️ WARNING: This should be EXTREMELY RARE!
    
    The EventBus is part of the protected A+ architecture and should
    be highly reliable. If you're seeing this error, there may be a
    fundamental architecture issue.
    
    Raised when:
    - Event dispatch fails unexpectedly
    - Subscriber registration fails
    - Event bus state is corrupted
    """
    pass


# ============================================================================
# Convenience functions
# ============================================================================

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
