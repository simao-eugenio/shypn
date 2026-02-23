# shypn package

# Import version information from single source of truth
from .version import (
    __version__,
    __version_name__,
    __version_date__,
    __api_version__,
    __required_engine_version__,
    __required_crossfetch_version__,
    __version_history__
)

# Import exception hierarchy for easy access
from .exceptions import (
    # Base exception
    ShypnError,
    
    # Model errors
    ModelError,
    
    # Simulation errors
    SimulationError,
    SimulationSetupError,
    SimulationRuntimeError,
    SimulationTimeoutError,
    
    # Data validation errors
    DataValidationError,
    ExpressionError,
    ParameterError,
    
    # Import/Export errors
    ImportExportError,
    FileFormatError,
    ParseError,
    ExportError,
    
    # Thermodynamics errors
    ThermodynamicsError,
    CompoundNotFoundError,
    ThermodynamicConstraintError,
    
    # External API errors
    KEGGError,
    KEGGConnectionError,
    KEGGDataError,
    
    # Architecture-specific (use carefully)
    DocumentError,
    EventBusError,
    
    # Utility functions
    format_exception_chain,
    is_shypn_error,
)

__all__ = [
    # Version info
    '__version__',
    '__version_name__',
    '__version_date__',
    '__api_version__',
    '__required_engine_version__',
    '__required_crossfetch_version__',
    '__version_history__',
    
    # Exceptions
    'ShypnError',
    'ModelError',
    'SimulationError',
    'SimulationSetupError',
    'SimulationRuntimeError',
    'SimulationTimeoutError',
    'DataValidationError',
    'ExpressionError',
    'ParameterError',
    'ImportExportError',
    'FileFormatError',
    'ParseError',
    'ExportError',
    'ThermodynamicsError',
    'CompoundNotFoundError',
    'ThermodynamicConstraintError',
    'KEGGError',
    'KEGGConnectionError',
    'KEGGDataError',
    'DocumentError',
    'EventBusError',
    'format_exception_chain',
    'is_shypn_error',
]
