"""Thermodynamic constraints module for shypn.

This module provides thermodynamic validation for biochemical reaction networks,
ensuring that kinetic rate constants are consistent with equilibrium constants
derived from Gibbs free energy calculations.

Main Components:
    - GibbsCalculator: Calculate ΔG°, K_eq from compound data
    - CompoundResolver: Map between KEGG/ChEBI identifiers
    - MultiSourceProvider: Database access with caching
    - CompoundThermodynamics: Data model for compound properties
    - ReactionThermodynamics: Data model for reaction thermodynamics
    - ThermodynamicValidation: Validation results for K_eq consistency

Example:
    >>> from shypn.thermodynamics import GibbsCalculator, MultiSourceProvider
    >>> provider = MultiSourceProvider()
    >>> calculator = GibbsCalculator(provider)
    >>> reactants = {"C00002": 1}  # ATP
    >>> products = {"C00008": 1}   # ADP
    >>> thermo = calculator.calculate_delta_g_reaction(reactants, products)
    >>> print(f"K_eq = {thermo.k_eq:.2e}")
"""

__version__ = "0.3.0"

# Export models
from .models import (
    CompoundThermodynamics,
    ReactionThermodynamics,
    ThermodynamicValidation
)

# Export base classes
from .base import (
    ThermodynamicCalculatorBase,
    CompoundDataProviderBase
)

# Export concrete implementations
from .gibbs_calculator import GibbsCalculator
from .compound_resolver import CompoundResolver, CompoundIdentity
from .thermodynamic_corrector import ThermodynamicCorrector

# Export validators
from .validators import EquilibriumValidator

# Export database providers
from .database import (
    CacheProvider,
    StaticDataProvider,
    MultiSourceProvider,
    EquilibratorProvider,
    MockEquilibratorProvider
)

__all__ = [
    # Version
    "__version__",
    
    # Models
    "CompoundThermodynamics",
    "ReactionThermodynamics",
    "ThermodynamicValidation",
    
    # Base classes
    "ThermodynamicCalculatorBase",
    "CompoundDataProviderBase",
    
    # Implementations
    "GibbsCalculator",
    "CompoundResolver",
    "CompoundIdentity",
    "ThermodynamicCorrector",
    
    # Validators
    "EquilibriumValidator",
    
    # Database providers
    "CacheProvider",
    "StaticDataProvider",
    "MultiSourceProvider",
    "EquilibratorProvider",
    "MockEquilibratorProvider",
]
