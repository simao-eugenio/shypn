"""Thermodynamic corrections for non-standard conditions.

This module provides corrections for Gibbs free energy calculations
under varying pH, temperature, and ionic strength conditions.

References:
    - Alberty, R.A. (2003). Thermodynamics of Biochemical Reactions.
    - Flamholz et al. (2012). eQuilibrator - the biochemical thermodynamics calculator.
    - van 't Hoff equation for temperature dependence.
"""

from typing import Optional
import math

from .base import ThermodynamicCalculatorBase


class ThermodynamicCorrector:
    """Apply corrections to Gibbs free energy for biochemical conditions.
    
    This class provides methods to correct ΔG° values for:
    1. pH changes (proton activity)
    2. Temperature changes (van 't Hoff equation)
    3. Ionic strength changes (Debye-Hückel theory)
    
    The corrections allow accurate thermodynamic calculations under
    physiological or experimental conditions that differ from standard state.
    
    Attributes:
        R: Gas constant (8.314 J/(mol·K) = 0.008314 kJ/(mol·K))
        STANDARD_PH: Standard pH (7.0 for biochemical standard state)
        STANDARD_TEMPERATURE: Standard temperature (298.15 K = 25°C)
        STANDARD_IONIC_STRENGTH: Standard ionic strength (0.1 M)
        
    Example:
        >>> corrector = ThermodynamicCorrector()
        >>> delta_g_std = -30.5  # kJ/mol at pH 7.0, 298.15 K
        >>> delta_g_corrected = corrector.correct_ph(
        ...     delta_g_std, n_protons=-1, ph_actual=6.5, ph_standard=7.0
        ... )
        >>> print(f"ΔG at pH 6.5: {delta_g_corrected:.2f} kJ/mol")
    """
    
    # Constants
    R = 0.008314  # kJ/(mol·K) - converted from base class J/(mol·K)
    STANDARD_PH = ThermodynamicCalculatorBase.STANDARD_PH  # 7.0
    STANDARD_TEMPERATURE = ThermodynamicCalculatorBase.STANDARD_TEMPERATURE  # 298.15 K
    STANDARD_IONIC_STRENGTH = 0.1  # M
    
    # Debye-Hückel parameters for water at 25°C
    DEBYE_HUCKEL_A = 0.509  # (mol/L)^(-1/2) at 25°C
    DEBYE_HUCKEL_B = 0.33   # Å^(-1)(mol/L)^(-1/2)
    ION_SIZE_PARAMETER = 4.0  # Å (typical for biochemical ions)
    
    def correct_ph(
        self,
        delta_g_standard: float,
        n_protons: int,
        ph_actual: float,
        ph_standard: float = STANDARD_PH,
        temperature: float = STANDARD_TEMPERATURE
    ) -> float:
        """Correct ΔG° for pH change.
        
        The correction accounts for the fact that biochemical reactions
        often involve proton transfer. The standard state uses pH 7.0,
        but actual conditions may differ.
        
        Formula:
            ΔG'(pH) = ΔG°(pH_std) + n_H+ · RT · ln(10) · (pH_actual - pH_std)
        
        Where:
            n_H+ is the net number of protons consumed (negative if produced)
        
        Args:
            delta_g_standard: ΔG° at standard pH (kJ/mol)
            n_protons: Net protons consumed in reaction (can be negative)
            ph_actual: Actual pH value
            ph_standard: Standard state pH (default 7.0)
            temperature: Temperature in Kelvin (default 298.15)
            
        Returns:
            Corrected ΔG° at actual pH (kJ/mol)
            
        Example:
            >>> # ATP hydrolysis: ATP + H2O → ADP + Pi + H+
            >>> # n_protons = -1 (produces 1 proton)
            >>> corrector = ThermodynamicCorrector()
            >>> dg_ph7 = -30.5  # kJ/mol
            >>> dg_ph6 = corrector.correct_ph(dg_ph7, n_protons=-1, ph_actual=6.0)
            >>> # At pH 6 (more acidic), reaction is less favorable
        """
        # ΔG'(pH) = ΔG°(pH_std) + n_H+ · RT · ln(10) · ΔpH
        # RT · ln(10) ≈ 5.708 kJ/mol at 298.15 K
        
        rt_ln10 = self.R * temperature * math.log(10)
        delta_ph = ph_actual - ph_standard
        
        correction = n_protons * rt_ln10 * delta_ph
        
        return delta_g_standard + correction
    
    def correct_temperature(
        self,
        delta_g_standard: float,
        delta_h_standard: Optional[float],
        temperature_actual: float,
        temperature_standard: float = STANDARD_TEMPERATURE
    ) -> float:
        """Correct ΔG° for temperature change using van 't Hoff equation.
        
        The correction requires knowing the standard enthalpy change (ΔH°).
        If ΔH° is not available, this method cannot be applied.
        
        Integrated van 't Hoff equation:
            ΔG(T) = ΔH° - T · ΔS°
            
        Where ΔS° can be derived from:
            ΔS° = (ΔH° - ΔG°(T_std)) / T_std
        
        Then:
            ΔG(T) = ΔH° - T · (ΔH° - ΔG°(T_std)) / T_std
            ΔG(T) = ΔH° · (1 - T/T_std) + ΔG°(T_std) · (T/T_std)
        
        Args:
            delta_g_standard: ΔG° at standard temperature (kJ/mol)
            delta_h_standard: ΔH° standard enthalpy change (kJ/mol)
                            If None, returns uncorrected value
            temperature_actual: Actual temperature (K)
            temperature_standard: Standard temperature (K, default 298.15)
            
        Returns:
            Corrected ΔG° at actual temperature (kJ/mol)
            
        Note:
            This assumes ΔH° and ΔS° are temperature-independent (valid
            for small temperature ranges ~20°C).
        """
        if delta_h_standard is None:
            # Cannot correct without enthalpy data
            return delta_g_standard
        
        if temperature_actual == temperature_standard:
            # No correction needed
            return delta_g_standard
        
        # Calculate ΔS° from standard conditions
        # ΔG° = ΔH° - T·ΔS°  →  ΔS° = (ΔH° - ΔG°) / T
        delta_s_standard = (delta_h_standard - delta_g_standard) / temperature_standard
        
        # Apply to new temperature
        # ΔG(T) = ΔH° - T·ΔS°
        delta_g_actual = delta_h_standard - temperature_actual * delta_s_standard
        
        return delta_g_actual
    
    def correct_temperature_k_eq(
        self,
        k_eq_standard: float,
        delta_h_standard: Optional[float],
        temperature_actual: float,
        temperature_standard: float = STANDARD_TEMPERATURE
    ) -> float:
        """Correct K_eq for temperature change using van 't Hoff equation.
        
        Alternative form of van 't Hoff equation:
            ln(K₂/K₁) = -ΔH°/R · (1/T₂ - 1/T₁)
        
        Args:
            k_eq_standard: K_eq at standard temperature
            delta_h_standard: ΔH° standard enthalpy change (kJ/mol)
                            If None, returns uncorrected K_eq
            temperature_actual: Actual temperature (K)
            temperature_standard: Standard temperature (K, default 298.15)
            
        Returns:
            Corrected K_eq at actual temperature
        """
        if delta_h_standard is None:
            # Cannot correct without enthalpy data
            return k_eq_standard
        
        if temperature_actual == temperature_standard:
            # No correction needed
            return k_eq_standard
        
        # ln(K₂/K₁) = -ΔH°/R · (1/T₂ - 1/T₁)
        exponent = -(delta_h_standard / self.R) * (
            1.0 / temperature_actual - 1.0 / temperature_standard
        )
        
        k_eq_actual = k_eq_standard * math.exp(exponent)
        
        return k_eq_actual
    
    def correct_ionic_strength(
        self,
        delta_g_standard: float,
        charge_reactants: int,
        charge_products: int,
        ionic_strength_actual: float,
        ionic_strength_standard: float = STANDARD_IONIC_STRENGTH
    ) -> float:
        """Correct ΔG° for ionic strength change using Debye-Hückel theory.
        
        The Debye-Hückel equation accounts for electrostatic interactions
        in ionic solutions. Higher ionic strength screens charges and
        affects reaction thermodynamics.
        
        Extended Debye-Hückel equation:
            log γ = -A · z² · √I / (1 + B · a · √I)
        
        Where:
            γ = activity coefficient
            z = ion charge
            I = ionic strength
            A = 0.509 (mol/L)^(-1/2) at 25°C in water
            B = 0.33 Å^(-1)(mol/L)^(-1/2)
            a = ion size parameter (≈4 Å for biochemical ions)
        
        Args:
            delta_g_standard: ΔG° at standard ionic strength (kJ/mol)
            charge_reactants: Sum of squared charges of reactants
            charge_products: Sum of squared charges of products
            ionic_strength_actual: Actual ionic strength (M)
            ionic_strength_standard: Standard ionic strength (M, default 0.1)
            
        Returns:
            Corrected ΔG° at actual ionic strength (kJ/mol)
            
        Note:
            Valid for ionic strengths up to ~0.5 M. Beyond this,
            more sophisticated models (Pitzer equations) are needed.
        """
        if ionic_strength_actual == ionic_strength_standard:
            # No correction needed
            return delta_g_standard
        
        # Calculate activity coefficient corrections
        gamma_actual = self._activity_coefficient(
            charge_products - charge_reactants,
            ionic_strength_actual
        )
        gamma_standard = self._activity_coefficient(
            charge_products - charge_reactants,
            ionic_strength_standard
        )
        
        # ΔG(I) = ΔG°(I_std) + RT ln(γ_actual/γ_standard)
        # For Debye-Hückel: RT ln(γ) ≈ 2.303 RT log(γ)
        rt = self.R * self.STANDARD_TEMPERATURE
        correction = 2.303 * rt * (gamma_actual - gamma_standard)
        
        return delta_g_standard + correction
    
    def _activity_coefficient(
        self,
        delta_charge_squared: int,
        ionic_strength: float
    ) -> float:
        """Calculate log(γ) using extended Debye-Hückel equation.
        
        Args:
            delta_charge_squared: (z_products² - z_reactants²)
            ionic_strength: Ionic strength (M)
            
        Returns:
            log₁₀(γ) activity coefficient logarithm
        """
        if ionic_strength <= 0:
            return 0.0
        
        sqrt_I = math.sqrt(ionic_strength)
        
        # Extended Debye-Hückel: log γ = -A·z²·√I / (1 + B·a·√I)
        denominator = 1.0 + self.DEBYE_HUCKEL_B * self.ION_SIZE_PARAMETER * sqrt_I
        
        log_gamma = -self.DEBYE_HUCKEL_A * delta_charge_squared * sqrt_I / denominator
        
        return log_gamma
    
    def apply_all_corrections(
        self,
        delta_g_standard: float,
        n_protons: int = 0,
        delta_h_standard: Optional[float] = None,
        charge_reactants: int = 0,
        charge_products: int = 0,
        ph_actual: float = STANDARD_PH,
        temperature_actual: float = STANDARD_TEMPERATURE,
        ionic_strength_actual: float = STANDARD_IONIC_STRENGTH,
        ph_standard: float = STANDARD_PH,
        temperature_standard: float = STANDARD_TEMPERATURE,
        ionic_strength_standard: float = STANDARD_IONIC_STRENGTH
    ) -> float:
        """Apply all corrections sequentially.
        
        Order of corrections:
        1. pH correction (most significant for biochemical reactions)
        2. Temperature correction (requires ΔH°)
        3. Ionic strength correction (usually smallest effect)
        
        Args:
            delta_g_standard: ΔG° at standard conditions (kJ/mol)
            n_protons: Net protons consumed (default 0)
            delta_h_standard: ΔH° for temperature correction (kJ/mol, optional)
            charge_reactants: Sum of squared charges of reactants (default 0)
            charge_products: Sum of squared charges of products (default 0)
            ph_actual: Actual pH (default 7.0)
            temperature_actual: Actual temperature K (default 298.15)
            ionic_strength_actual: Actual ionic strength M (default 0.1)
            ph_standard: Standard pH (default 7.0)
            temperature_standard: Standard temperature K (default 298.15)
            ionic_strength_standard: Standard ionic strength M (default 0.1)
            
        Returns:
            Fully corrected ΔG° at actual conditions (kJ/mol)
        """
        # Start with standard ΔG°
        delta_g = delta_g_standard
        
        # Apply pH correction
        if n_protons != 0 and ph_actual != ph_standard:
            delta_g = self.correct_ph(
                delta_g, n_protons, ph_actual, ph_standard, temperature_actual
            )
        
        # Apply temperature correction
        if delta_h_standard is not None and temperature_actual != temperature_standard:
            delta_g = self.correct_temperature(
                delta_g, delta_h_standard, temperature_actual, temperature_standard
            )
        
        # Apply ionic strength correction
        if ionic_strength_actual != ionic_strength_standard:
            delta_g = self.correct_ionic_strength(
                delta_g,
                charge_reactants,
                charge_products,
                ionic_strength_actual,
                ionic_strength_standard
            )
        
        return delta_g
