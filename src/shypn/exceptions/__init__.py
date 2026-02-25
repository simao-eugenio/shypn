"""Custom exception hierarchy for SHYPN.

This package provides a structured exception hierarchy for the entire SHYPN
project, split by domain for clarity.

Exception Hierarchy:
    ShypnError (base)
    ├── ModelError                              ← exceptions.model
    ├── SimulationError                         ← exceptions.simulation
    │   ├── SimulationSetupError
    │   ├── SimulationRuntimeError
    │   └── SimulationTimeoutError
    ├── DataValidationError                     ← exceptions.validation
    │   ├── ExpressionError
    │   └── ParameterError
    ├── ImportExportError                       ← exceptions.io
    │   ├── FileFormatError
    │   ├── ParseError
    │   └── ExportError
    ├── ThermodynamicsError                     ← exceptions.thermodynamics
    │   ├── CompoundNotFoundError
    │   └── ThermodynamicConstraintError
    ├── KEGGError                               ← exceptions.external
    │   ├── KEGGConnectionError
    │   └── KEGGDataError
    ├── DocumentError                           ← exceptions.architecture
    └── EventBusError                           ← exceptions.architecture

All names are re-exported from this package so existing imports like
``from shypn.exceptions import SimulationError`` continue to work unchanged.

Usage:
    from shypn.exceptions import SimulationError, ModelError

    try:
        run_simulation(model)
    except SimulationError as e:
        logger.error(f"Simulation failed: {e}")
    except ModelError as e:
        logger.error(f"Invalid model: {e}")

For new code, prefer importing from the domain-specific sub-module:
    from shypn.exceptions.simulation import SimulationError
    from shypn.exceptions.io import ImportExportError
"""

# Base
from shypn.exceptions.base import ShypnError

# Model
from shypn.exceptions.model import ModelError

# Simulation
from shypn.exceptions.simulation import (
    SimulationError,
    SimulationSetupError,
    SimulationRuntimeError,
    SimulationTimeoutError,
)

# Data validation
from shypn.exceptions.validation import (
    DataValidationError,
    ExpressionError,
    ParameterError,
)

# Import / export
from shypn.exceptions.io import (
    ImportExportError,
    FileFormatError,
    ParseError,
    ExportError,
)

# Thermodynamics
from shypn.exceptions.thermodynamics import (
    ThermodynamicsError,
    CompoundNotFoundError,
    ThermodynamicConstraintError,
)

# External APIs
from shypn.exceptions.external import (
    KEGGError,
    KEGGConnectionError,
    KEGGDataError,
)

# Architecture
from shypn.exceptions.architecture import (
    DocumentError,
    EventBusError,
)

# Utilities
from shypn.exceptions.utils import format_exception_chain, is_shypn_error

__all__ = [
    # Base
    "ShypnError",
    # Model
    "ModelError",
    # Simulation
    "SimulationError",
    "SimulationSetupError",
    "SimulationRuntimeError",
    "SimulationTimeoutError",
    # Validation
    "DataValidationError",
    "ExpressionError",
    "ParameterError",
    # I/O
    "ImportExportError",
    "FileFormatError",
    "ParseError",
    "ExportError",
    # Thermodynamics
    "ThermodynamicsError",
    "CompoundNotFoundError",
    "ThermodynamicConstraintError",
    # External
    "KEGGError",
    "KEGGConnectionError",
    "KEGGDataError",
    # Architecture
    "DocumentError",
    "EventBusError",
    # Utils
    "format_exception_chain",
    "is_shypn_error",
]
