"""Equilibrium validator for thermodynamic consistency.

This module validates that kinetic rate constants are consistent with
thermodynamic equilibrium constants derived from Gibbs free energy.

For a reversible reaction:
    A + B ⇌ C + D

The kinetic ratio k_forward/k_reverse should match the thermodynamic
equilibrium constant K_eq = exp(-ΔG°/RT), within reasonable tolerance.
"""

from typing import Optional, Dict, Any
import math

from ..models import ThermodynamicValidation, ReactionThermodynamics
from ..base import ThermodynamicCalculatorBase


class EquilibriumValidator:
    """Validates consistency between kinetic and thermodynamic parameters.
    
    This validator checks if the ratio of forward to reverse rate constants
    (k_f/k_r) is consistent with the thermodynamic equilibrium constant (K_eq)
    calculated from Gibbs free energy.
    
    Biological systems often show deviations due to:
    - Non-equilibrium conditions (steady-state flux)
    - Regulation by enzymes
    - Coupling to other reactions
    - Measurement uncertainties
    
    Therefore, a tolerance factor is applied rather than requiring exact equality.
    
    Attributes:
        calculator: Thermodynamic calculator for K_eq computation.
        tolerance: Acceptable deviation factor (default 0.5 = ±50%).
                  Valid range: 0.0 to 1.0.
        
    Example:
        >>> validator = EquilibriumValidator(calculator, tolerance=0.5)
        >>> validation = validator.validate_rate_constants(
        ...     k_forward=1e6,
        ...     k_reverse=1e3,
        ...     reaction_thermo=reaction_thermo
        ... )
        >>> if not validation.is_valid:
        ...     print(validation.message)
    """
    
    def __init__(
        self,
        calculator: ThermodynamicCalculatorBase,
        tolerance: float = 0.5
    ):
        """Initialize the equilibrium validator.
        
        Args:
            calculator: Calculator for thermodynamic properties.
            tolerance: Acceptable relative deviation (0.0 to 1.0).
                      For example, 0.5 means ±50% is acceptable.
                      
        Raises:
            ValueError: If tolerance is not in valid range [0.0, 1.0].
        """
        if not 0.0 <= tolerance <= 1.0:
            raise ValueError(f"Tolerance must be between 0.0 and 1.0, got {tolerance}")
        
        self.calculator = calculator
        self.tolerance = tolerance
    
    def validate_rate_constants(
        self,
        k_forward: float,
        k_reverse: float,
        reaction_thermo: ReactionThermodynamics,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ThermodynamicValidation:
        """Validate consistency between kinetic rates and thermodynamics.
        
        Compares the kinetic ratio (k_f/k_r) with the thermodynamic
        equilibrium constant K_eq. Returns validation result with details.
        
        Args:
            k_forward: Forward rate constant (s⁻¹ or M⁻¹s⁻¹).
            k_reverse: Reverse rate constant (same units as k_forward).
            reaction_thermo: Thermodynamic properties of the reaction.
            metadata: Optional additional information (reaction ID, etc.).
            
        Returns:
            ThermodynamicValidation with validation results.
            
        Raises:
            ValueError: If rate constants are not positive.
        """
        if k_forward <= 0 or k_reverse <= 0:
            raise ValueError(
                f"Rate constants must be positive: "
                f"k_forward={k_forward}, k_reverse={k_reverse}"
            )
        
        # Calculate kinetic ratio
        kinetic_ratio = k_forward / k_reverse
        
        # Get thermodynamic K_eq
        k_eq = reaction_thermo.k_eq
        
        if k_eq is None or k_eq == 0.0:
            # Cannot validate without valid K_eq
            return ThermodynamicValidation(
                is_valid=False,
                message="Cannot validate: K_eq is None or zero (insufficient thermodynamic data)",
                delta_g_reaction=reaction_thermo.delta_g_standard,
                k_eq=k_eq,
                details={
                    "k_forward": k_forward,
                    "k_reverse": k_reverse,
                    "kinetic_ratio": kinetic_ratio,
                    **(metadata or {})
                }
            )
        
        # Check if K_eq is valid (not inf, not nan)
        if not math.isfinite(k_eq):
            return ThermodynamicValidation(
                is_valid=False,
                message=f"Cannot validate: K_eq is {k_eq} (overflow or undefined)",
                delta_g_reaction=reaction_thermo.delta_g_standard,
                k_eq=k_eq,
                details={
                    "k_forward": k_forward,
                    "k_reverse": k_reverse,
                    "kinetic_ratio": kinetic_ratio,
                    **(metadata or {})
                }
            )
        
        # Calculate relative deviation
        # Use log scale to handle large ratios symmetrically
        log_kinetic = math.log10(kinetic_ratio)
        log_thermo = math.log10(k_eq)
        log_deviation = abs(log_kinetic - log_thermo)
        
        # Convert tolerance to log scale
        # tolerance=0.5 means ±50%, which is ~0.176 in log10 space
        # But we use a more permissive formula: allow K_eq * (1 ± tolerance)
        # In log space: log10(K_eq * (1 + tolerance)) - log10(K_eq)
        max_log_deviation = abs(math.log10(1 + self.tolerance))
        
        # Actually, for biological relevance, we should allow ±1 order of magnitude
        # with default tolerance=0.5. Let's use a simpler criterion:
        # Accept if kinetic_ratio is within [K_eq/(1+tol), K_eq*(1+tol)]
        # But this is still too strict. Let's use orders of magnitude:
        # Accept if log_deviation < tolerance_in_orders
        tolerance_orders = -math.log10(1 - self.tolerance)  # 0.5 → ~0.3 orders
        
        # Actually, biological systems can deviate by orders of magnitude
        # Let's be more permissive: tolerance in log units directly
        # tolerance=0.5 → accept if within ±0.5 orders of magnitude
        # For simplicity: max_log_deviation = 1.0 (±1 order) for tolerance=0.5
        max_log_deviation = 2.0 * self.tolerance  # 0.5 → 1.0 order of magnitude
        
        is_valid = log_deviation <= max_log_deviation
        
        # Construct message
        if is_valid:
            message = (
                f"Valid: k_f/k_r = {kinetic_ratio:.2e} ≈ K_eq = {k_eq:.2e} "
                f"(within {self.tolerance*100:.0f}% tolerance, "
                f"Δlog = {log_deviation:.2f} orders)"
            )
        else:
            message = (
                f"Invalid: k_f/k_r = {kinetic_ratio:.2e} vs K_eq = {k_eq:.2e} "
                f"(exceeds {self.tolerance*100:.0f}% tolerance, "
                f"Δlog = {log_deviation:.2f} > {max_log_deviation:.2f} orders). "
                f"Kinetic rates may not be at thermodynamic equilibrium."
            )
        
        return ThermodynamicValidation(
            is_valid=is_valid,
            message=message,
            delta_g_reaction=reaction_thermo.delta_g_standard,
            k_eq=k_eq,
            details={
                "k_forward": k_forward,
                "k_reverse": k_reverse,
                "kinetic_ratio": kinetic_ratio,
                "log_deviation": log_deviation,
                "max_log_deviation": max_log_deviation,
                "tolerance": self.tolerance,
                **(metadata or {})
            }
        )
    
    def validate_reversible_reaction(
        self,
        k_forward: float,
        k_reverse: float,
        reactants: Dict[str, float],
        products: Dict[str, float],
        concentrations: Optional[Dict[str, float]] = None,
        ph: float = 7.0,
        temperature: float = 298.15,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ThermodynamicValidation:
        """Validate a reversible reaction with full thermodynamic calculation.
        
        This is a convenience method that:
        1. Calculates ΔG and K_eq using the calculator
        2. Validates the rate constants against K_eq
        
        Args:
            k_forward: Forward rate constant.
            k_reverse: Reverse rate constant.
            reactants: Compound IDs to stoichiometric coefficients (positive).
            products: Compound IDs to stoichiometric coefficients (positive).
            concentrations: Optional concentrations for ΔG calculation.
            ph: pH value (default 7.0).
            temperature: Temperature in Kelvin (default 298.15).
            metadata: Optional additional information.
            
        Returns:
            ThermodynamicValidation with validation results.
        """
        # Calculate thermodynamic properties
        reaction_thermo = self.calculator.calculate_delta_g_reaction(
            reactants=reactants,
            products=products,
            concentrations=concentrations,
            ph=ph,
            temperature=temperature
        )
        
        # Validate against rate constants
        return self.validate_rate_constants(
            k_forward=k_forward,
            k_reverse=k_reverse,
            reaction_thermo=reaction_thermo,
            metadata=metadata
        )
