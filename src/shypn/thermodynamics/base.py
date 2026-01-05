"""Abstract base classes for thermodynamic calculations.

This module defines the interfaces for thermodynamic calculators,
following the Open/Closed Principle for extensibility.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional

from .models import CompoundThermodynamics, ReactionThermodynamics


class ThermodynamicCalculatorBase(ABC):
    """Abstract base class for thermodynamic calculations.
    
    Subclasses must implement core calculation methods for computing
    Gibbs free energy changes and equilibrium constants.
    """
    
    # Gas constant (J/(mol·K))
    R = 8.314
    
    # Standard conditions
    STANDARD_TEMPERATURE = 298.15  # K (25°C)
    STANDARD_PH = 7.0
    STANDARD_IONIC_STRENGTH = 0.1  # M
    
    @abstractmethod
    def calculate_delta_g_reaction(
        self,
        reactants: Dict[str, float],
        products: Dict[str, float],
        concentrations: Optional[Dict[str, float]] = None,
        temperature: float = STANDARD_TEMPERATURE,
        ph: float = STANDARD_PH
    ) -> ReactionThermodynamics:
        """Calculate ΔG for a biochemical reaction.
        
        Args:
            reactants: {compound_id: stoichiometry}
            products: {compound_id: stoichiometry}
            concentrations: Optional {compound_id: concentration_M}
            temperature: Temperature in Kelvin
            ph: pH value
            
        Returns:
            ReactionThermodynamics with ΔG°, ΔG'°, K_eq, and ΔG (if concentrations given)
        """
        pass
    
    @abstractmethod
    def calculate_k_eq(
        self,
        delta_g_standard: float,
        temperature: float = STANDARD_TEMPERATURE
    ) -> float:
        """Calculate equilibrium constant from ΔG°.
        
        K_eq = exp(-ΔG° / RT)
        
        Args:
            delta_g_standard: Standard Gibbs free energy (kJ/mol)
            temperature: Temperature in Kelvin
            
        Returns:
            Equilibrium constant (dimensionless)
        """
        pass
    
    @abstractmethod
    def calculate_reaction_quotient(
        self,
        reactants: Dict[str, float],
        products: Dict[str, float],
        concentrations: Dict[str, float]
    ) -> float:
        """Calculate reaction quotient Q.
        
        Q = ∏[products]^ν / ∏[reactants]^ν
        
        Args:
            reactants: {compound_id: stoichiometry}
            products: {compound_id: stoichiometry}
            concentrations: {compound_id: concentration_M}
            
        Returns:
            Reaction quotient (dimensionless)
        """
        pass
    
    def calculate_delta_g_with_concentrations(
        self,
        delta_g_standard: float,
        reaction_quotient: float,
        temperature: float = STANDARD_TEMPERATURE
    ) -> float:
        """Calculate actual ΔG from ΔG° and Q.
        
        ΔG = ΔG° + RT ln(Q)
        
        Args:
            delta_g_standard: Standard Gibbs free energy (kJ/mol)
            reaction_quotient: Q = [products]/[reactants]
            temperature: Temperature in Kelvin
            
        Returns:
            Actual Gibbs free energy change (kJ/mol)
        """
        import math
        if reaction_quotient <= 0:
            raise ValueError("Reaction quotient must be positive")
        # Convert J to kJ (R is in J/(mol·K))
        return delta_g_standard + (self.R * temperature * math.log(reaction_quotient)) / 1000


class CompoundDataProviderBase(ABC):
    """Abstract base class for providing compound thermodynamic data.
    
    Implementations may use databases (eQuilibrator, MetaCyc),
    local files, or web services.
    """
    
    @abstractmethod
    def get_compound(
        self,
        compound_id: str,
        ph: float = 7.0,
        temperature: float = 298.15,
        ionic_strength: float = 0.1
    ) -> Optional[CompoundThermodynamics]:
        """Retrieve thermodynamic data for a compound.
        
        Args:
            compound_id: KEGG C-number or ChEBI ID
            ph: pH value for biochemical corrections
            temperature: Temperature in Kelvin
            ionic_strength: Ionic strength in M
            
        Returns:
            CompoundThermodynamics if found, None otherwise
        """
        pass
    
    @abstractmethod
    def has_compound(self, compound_id: str) -> bool:
        """Check if compound data is available.
        
        Args:
            compound_id: KEGG C-number or ChEBI ID
            
        Returns:
            True if compound data exists
        """
        pass
