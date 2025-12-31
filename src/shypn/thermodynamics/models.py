"""Data models for thermodynamic calculations.

This module defines immutable data structures representing thermodynamic
properties of biochemical compounds and reactions.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any


@dataclass(frozen=True)
class CompoundThermodynamics:
    """Thermodynamic properties of a biochemical compound.
    
    Attributes:
        compound_id: Identifier (KEGG C-number or ChEBI ID)
        name: Common or systematic name
        delta_g_formation: Standard Gibbs free energy of formation (kJ/mol)
        source: Database or reference source
        uncertainty: Experimental uncertainty (kJ/mol)
        conditions: Experimental conditions (pH, T, ionic strength)
    """
    compound_id: str
    name: str
    delta_g_formation: float  # kJ/mol
    source: str
    uncertainty: float = 0.0  # kJ/mol
    conditions: Dict[str, float] = field(default_factory=lambda: {
        'pH': 7.0,
        'temperature': 298.15,  # K
        'ionic_strength': 0.1   # M
    })
    
    def __post_init__(self):
        """Validate thermodynamic data."""
        if not self.compound_id:
            raise ValueError("compound_id cannot be empty")
        if 'temperature' in self.conditions and self.conditions['temperature'] <= 0:
            raise ValueError("Temperature must be positive (Kelvin)")
    
    @property
    def temperature(self) -> float:
        """Get temperature in Kelvin."""
        return self.conditions.get('temperature', 298.15)
    
    @property
    def ph(self) -> float:
        """Get pH value."""
        return self.conditions.get('pH', 7.0)
    
    @property
    def ionic_strength(self) -> float:
        """Get ionic strength in M."""
        return self.conditions.get('ionic_strength', 0.1)


@dataclass(frozen=True)
class ReactionThermodynamics:
    """Thermodynamic properties of a biochemical reaction.
    
    Attributes:
        reaction_id: Reaction identifier
        delta_g_standard: Standard Gibbs free energy change (kJ/mol)
        delta_g_prime: Biochemical standard state at pH 7 (kJ/mol)
        k_eq: Equilibrium constant (dimensionless)
        temperature: Temperature (K)
        ph: pH value
        ionic_strength: Ionic strength (M)
        delta_g_actual: Actual ΔG with current concentrations (kJ/mol)
        reaction_quotient: Q = [products]/[reactants] (dimensionless)
    """
    reaction_id: str
    delta_g_standard: float  # kJ/mol
    delta_g_prime: float  # kJ/mol (biochemical standard)
    k_eq: float  # Dimensionless
    temperature: float = 298.15  # K
    ph: float = 7.0
    ionic_strength: float = 0.1  # M
    delta_g_actual: Optional[float] = None  # kJ/mol (with concentrations)
    reaction_quotient: Optional[float] = None  # Q (dimensionless)
    
    def __post_init__(self):
        """Validate reaction thermodynamics."""
        if not self.reaction_id:
            raise ValueError("reaction_id cannot be empty")
        if self.temperature <= 0:
            raise ValueError("Temperature must be positive (Kelvin)")
        if self.k_eq < 0:
            raise ValueError("Equilibrium constant must be non-negative")
    
    @property
    def is_favorable(self) -> bool:
        """Check if reaction is thermodynamically favorable (ΔG < 0)."""
        delta_g = self.delta_g_actual if self.delta_g_actual is not None else self.delta_g_prime
        return delta_g < 0
    
    @property
    def is_at_equilibrium(self, tolerance: float = 0.1) -> bool:
        """Check if reaction is near equilibrium (|ΔG| < tolerance)."""
        delta_g = self.delta_g_actual if self.delta_g_actual is not None else self.delta_g_prime
        return abs(delta_g) < tolerance


@dataclass(frozen=True)
class ThermodynamicValidation:
    """Result of thermodynamic consistency validation.
    
    Attributes:
        is_valid: Whether validation passed
        message: Human-readable validation message
        delta_g_reaction: Standard Gibbs free energy (kJ/mol)
        k_eq: Equilibrium constant
        details: Additional validation details (k_forward, k_reverse, etc.)
    """
    is_valid: bool
    message: str
    delta_g_reaction: Optional[float] = None
    k_eq: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate and convert details if needed."""
        if self.details is None:
            # Use object.__setattr__ because dataclass is frozen
            object.__setattr__(self, 'details', {})

