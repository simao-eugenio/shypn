"""Gibbs free energy calculator implementation.

This module provides concrete implementation of thermodynamic calculations
for biochemical reactions, including ΔG°, K_eq, and concentration-dependent ΔG.
"""

import logging
import math
from typing import Dict, Optional

from .base import ThermodynamicCalculatorBase, CompoundDataProviderBase
from .models import ReactionThermodynamics
from .thermodynamic_corrector import ThermodynamicCorrector

logger = logging.getLogger(__name__)


class GibbsCalculator(ThermodynamicCalculatorBase):
    """Calculate Gibbs free energy changes for biochemical reactions.
    
    This calculator computes:
    - ΔG°_r from compound formation energies
    - K_eq from ΔG° via Boltzmann relationship
    - ΔG from ΔG° and reaction quotient Q
    - Biochemical standard state corrections (pH 7)
    
    Attributes:
        compound_provider: Source of compound thermodynamic data
        
    Example:
        >>> calculator = GibbsCalculator(provider)
        >>> reactants = {"C00002": 1, "C00001": 1}  # ATP + H2O
        >>> products = {"C00008": 1, "C00009": 1}   # ADP + Pi
        >>> thermo = calculator.calculate_delta_g_reaction(reactants, products)
        >>> print(f"ΔG° = {thermo.delta_g_standard:.1f} kJ/mol")
        >>> print(f"K_eq = {thermo.k_eq:.2e}")
    """
    
    def __init__(self, compound_provider: Optional[CompoundDataProviderBase] = None):
        """Initialize calculator with compound data provider.
        
        Args:
            compound_provider: Provider for compound thermodynamic data.
                             If None, uses local cache only.
        """
        self.compound_provider = compound_provider
        self._compound_cache: Dict[str, float] = {}
        self.corrector = ThermodynamicCorrector()
    
    def calculate_delta_g_reaction(
        self,
        reactants: Dict[str, float],
        products: Dict[str, float],
        concentrations: Optional[Dict[str, float]] = None,
        temperature: float = ThermodynamicCalculatorBase.STANDARD_TEMPERATURE,
        ph: float = ThermodynamicCalculatorBase.STANDARD_PH,
        n_protons: int = 0
    ) -> ReactionThermodynamics:
        """Calculate ΔG for a biochemical reaction.
        
        Steps:
        1. Get ΔG°_f for all compounds from provider
        2. Calculate ΔG°_r = Σ(ν_products·ΔG°_f) - Σ(ν_reactants·ΔG°_f)
        3. Apply pH corrections for biochemical standard state (ΔG'°)
        4. Calculate K_eq = exp(-ΔG°/RT)
        5. If concentrations given: ΔG = ΔG° + RT ln(Q)
        
        Args:
            reactants: {compound_id: stoichiometry}
            products: {compound_id: stoichiometry}
            concentrations: Optional {compound_id: concentration_M}
            temperature: Temperature in Kelvin
            ph: pH value
            n_protons: Net protons consumed (negative if produced)
            
        Returns:
            ReactionThermodynamics with all calculated properties
            
        Raises:
            ValueError: If compound data unavailable or invalid stoichiometry
        """
        # Calculate ΔG°_r from compound formation energies
        delta_g_standard = self._calculate_delta_g_standard(reactants, products, ph, temperature)
        
        # Apply pH correction if n_protons specified
        if n_protons != 0:
            delta_g_prime = self.corrector.correct_ph(
                delta_g_standard,
                n_protons=n_protons,
                ph_actual=ph,
                ph_standard=self.STANDARD_PH,
                temperature=temperature
            )
            logger.debug(
                f"Applied pH correction: ΔG° = {delta_g_standard:.2f} kJ/mol, "
                f"ΔG'° = {delta_g_prime:.2f} kJ/mol (n_H+ = {n_protons}, pH = {ph})"
            )
        else:
            delta_g_prime = delta_g_standard
        
        # Calculate equilibrium constant (use corrected value)
        k_eq = self.calculate_k_eq(delta_g_prime, temperature)
        
        # Calculate actual ΔG and Q if concentrations provided
        delta_g_actual = None
        reaction_quotient = None
        if concentrations is not None:
            reaction_quotient = self.calculate_reaction_quotient(
                reactants, products, concentrations
            )
            delta_g_actual = self.calculate_delta_g_with_concentrations(
                delta_g_prime, reaction_quotient, temperature
            )
        
        return ReactionThermodynamics(
            reaction_id="calculated",
            delta_g_standard=delta_g_standard,
            delta_g_prime=delta_g_prime,
            k_eq=k_eq,
            temperature=temperature,
            ph=ph,
            ionic_strength=self.STANDARD_IONIC_STRENGTH,
            delta_g_actual=delta_g_actual,
            reaction_quotient=reaction_quotient
        )
    
    def calculate_k_eq(
        self,
        delta_g_standard: float,
        temperature: float = ThermodynamicCalculatorBase.STANDARD_TEMPERATURE
    ) -> float:
        """Calculate equilibrium constant from ΔG°.
        
        K_eq = exp(-ΔG° / RT)
        
        Args:
            delta_g_standard: Standard Gibbs free energy (kJ/mol)
            temperature: Temperature in Kelvin
            
        Returns:
            Equilibrium constant (dimensionless)
        """
        if temperature <= 0:
            raise ValueError("Temperature must be positive")
        
        # Convert kJ to J for calculation
        delta_g_joules = delta_g_standard * 1000
        exponent = -delta_g_joules / (self.R * temperature)
        
        # Prevent overflow for very large/small ΔG values
        if exponent > 700:  # exp(700) ≈ 1e304
            logger.warning(f"K_eq calculation overflow: ΔG° = {delta_g_standard:.1f} kJ/mol, returning 1e308")
            return 1e308
        elif exponent < -700:
            logger.warning(f"K_eq calculation underflow: ΔG° = {delta_g_standard:.1f} kJ/mol, returning 1e-308")
            return 1e-308
        
        return math.exp(exponent)
    
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
            
        Raises:
            ValueError: If concentrations missing or non-positive
        """
        q_numerator = 1.0
        q_denominator = 1.0
        
        # Products in numerator
        for compound_id, stoich in products.items():
            if compound_id not in concentrations:
                raise ValueError(f"Missing concentration for product {compound_id}")
            conc = concentrations[compound_id]
            if conc <= 0:
                raise ValueError(f"Concentration must be positive: {compound_id} = {conc}")
            q_numerator *= conc ** stoich
        
        # Reactants in denominator
        for compound_id, stoich in reactants.items():
            if compound_id not in concentrations:
                raise ValueError(f"Missing concentration for reactant {compound_id}")
            conc = concentrations[compound_id]
            if conc <= 0:
                raise ValueError(f"Concentration must be positive: {compound_id} = {conc}")
            q_denominator *= conc ** stoich
        
        if q_denominator == 0:
            raise ValueError("Reaction quotient denominator is zero")
        
        return q_numerator / q_denominator
    
    def _calculate_delta_g_standard(
        self,
        reactants: Dict[str, float],
        products: Dict[str, float],
        ph: float,
        temperature: float
    ) -> float:
        """Calculate ΔG°_r from compound formation energies.
        
        ΔG°_r = Σ(ν_products · ΔG°_f) - Σ(ν_reactants · ΔG°_f)
        
        Args:
            reactants: {compound_id: stoichiometry}
            products: {compound_id: stoichiometry}
            ph: pH value
            temperature: Temperature in Kelvin
            
        Returns:
            Standard Gibbs free energy of reaction (kJ/mol)
            
        Raises:
            ValueError: If compound data unavailable
        """
        delta_g = 0.0
        
        # Products contribute positively
        for compound_id, stoich in products.items():
            dg_f = self._get_compound_formation_energy(compound_id, ph, temperature)
            delta_g += stoich * dg_f
        
        # Reactants contribute negatively
        for compound_id, stoich in reactants.items():
            dg_f = self._get_compound_formation_energy(compound_id, ph, temperature)
            delta_g -= stoich * dg_f
        
        return delta_g
    
    def _get_compound_formation_energy(
        self,
        compound_id: str,
        ph: float,
        temperature: float
    ) -> float:
        """Get ΔG°_f for a compound from provider or cache.
        
        Args:
            compound_id: KEGG C-number or ChEBI ID
            ph: pH value
            temperature: Temperature in Kelvin
            
        Returns:
            Standard Gibbs free energy of formation (kJ/mol)
            
        Raises:
            ValueError: If compound data unavailable
        """
        # Check cache first
        cache_key = f"{compound_id}_{ph}_{temperature}"
        if cache_key in self._compound_cache:
            return self._compound_cache[cache_key]
        
        # Query provider
        if self.compound_provider is None:
            raise ValueError(
                f"Compound data unavailable: {compound_id} "
                "(no provider configured)"
            )
        
        compound = self.compound_provider.get_compound(
            compound_id, ph, temperature
        )
        
        if compound is None:
            raise ValueError(
                f"Compound data not found: {compound_id}"
            )
        
        # Cache and return
        dg_f = compound.delta_g_formation
        self._compound_cache[cache_key] = dg_f
        logger.debug(f"Retrieved ΔG°_f for {compound_id}: {dg_f:.2f} kJ/mol")
        
        return dg_f
    
    def clear_cache(self):
        """Clear compound data cache."""
        self._compound_cache.clear()
        logger.debug("Compound cache cleared")
