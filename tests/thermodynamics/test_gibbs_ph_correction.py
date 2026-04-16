"""Tests for pH correction integration in Gibbs calculator.

This module tests the integration of ThermodynamicCorrector into
GibbsCalculator for pH-dependent reactions.
"""

import pytest
import math

from shypn.thermodynamics.gibbs_calculator import GibbsCalculator
from shypn.thermodynamics.database.static_provider import StaticThermodynamicProvider


class TestGibbsCalculatorPHCorrection:
    """Test pH correction integration in Gibbs calculator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use static provider with test data
        self.calculator = GibbsCalculator(
            compound_provider=StaticThermodynamicProvider()
        )
    
    def test_calculator_has_corrector(self):
        """Test that calculator has corrector initialized."""
        assert hasattr(self.calculator, 'corrector')
        assert self.calculator.corrector is not None
    
    def test_calculate_delta_g_reaction_has_n_protons_parameter(self):
        """Test that calculate_delta_g_reaction accepts n_protons parameter."""
        # Try calling with n_protons parameter (even if data unavailable)
        try:
            result = self.calculator.calculate_delta_g_reaction(
                reactants={"C00002": 1.0},
                products={"C00008": 1.0},
                n_protons=0
            )
            # If we got here, parameter is accepted
            assert True
        except ValueError as e:
            # Data might be unavailable, but parameter should be accepted
            if "unavailable" in str(e) or "not found" in str(e):
                pytest.skip("Test data not available in static provider")
            else:
                raise
    
    def test_no_ph_correction_when_n_protons_zero(self):
        """Test that pH correction is skipped when n_protons=0."""
        # Mock a simple reaction with known data
        try:
            result = self.calculator.calculate_delta_g_reaction(
                reactants={"C00002": 1.0},
                products={"C00008": 1.0},
                ph=7.0,
                n_protons=0  # No correction needed
            )
            
            # delta_g_prime should equal delta_g_standard (no correction)
            assert result.delta_g_prime == result.delta_g_standard, \
                "Expected no pH correction when n_protons=0"
        
        except ValueError as e:
            if "unavailable" in str(e) or "not found" in str(e):
                pytest.skip("Test data not available in static provider")
            else:
                raise
    
    def test_ph_correction_applied_when_n_protons_nonzero(self):
        """Test that pH correction is applied when n_protons != 0."""
        try:
            # Reaction producing 1 proton (n_protons = -1)
            result = self.calculator.calculate_delta_g_reaction(
                reactants={"C00002": 1.0},
                products={"C00008": 1.0},
                ph=7.0,
                n_protons=-1
            )
            
            # delta_g_prime should differ from delta_g_standard
            assert result.delta_g_prime != result.delta_g_standard, \
                "Expected pH correction when n_protons != 0"
        
        except ValueError as e:
            if "unavailable" in str(e) or "not found" in str(e):
                pytest.skip("Test data not available in static provider")
            else:
                raise
    
    def test_ph_correction_direction_proton_production(self):
        """Test pH correction for reaction producing protons."""
        try:
            # Reaction producing 1 proton (n_protons = -1)
            # At pH 7.0 (standard)
            result_ph7 = self.calculator.calculate_delta_g_reaction(
                reactants={"C00002": 1.0},
                products={"C00008": 1.0},
                ph=7.0,
                n_protons=-1
            )
            
            # At pH 6.0 (more acidic)
            result_ph6 = self.calculator.calculate_delta_g_reaction(
                reactants={"C00002": 1.0},
                products={"C00008": 1.0},
                ph=6.0,
                n_protons=-1
            )
            
            # At lower pH (more acidic), reaction producing H+ is less favorable
            # ΔG'° should be less negative (less favorable)
            assert result_ph6.delta_g_prime > result_ph7.delta_g_prime, \
                "Expected less favorable ΔG at lower pH for proton-producing reaction"
            
            # K_eq should also be smaller at lower pH
            assert result_ph6.k_eq < result_ph7.k_eq, \
                "Expected smaller K_eq at lower pH for proton-producing reaction"
        
        except ValueError as e:
            if "unavailable" in str(e) or "not found" in str(e):
                pytest.skip("Test data not available in static provider")
            else:
                raise
    
    def test_ph_correction_direction_proton_consumption(self):
        """Test pH correction for reaction consuming protons."""
        try:
            # Reaction consuming 1 proton (n_protons = 1)
            # At pH 7.0 (standard)
            result_ph7 = self.calculator.calculate_delta_g_reaction(
                reactants={"C00002": 1.0},
                products={"C00008": 1.0},
                ph=7.0,
                n_protons=1
            )
            
            # At pH 6.0 (more acidic, more H+ available)
            result_ph6 = self.calculator.calculate_delta_g_reaction(
                reactants={"C00002": 1.0},
                products={"C00008": 1.0},
                ph=6.0,
                n_protons=1
            )
            
            # At lower pH (more H+ available), reaction consuming H+ is more favorable
            # ΔG'° should be more negative (more favorable)
            assert result_ph6.delta_g_prime < result_ph7.delta_g_prime, \
                "Expected more favorable ΔG at lower pH for proton-consuming reaction"
            
            # K_eq should also be larger at lower pH
            assert result_ph6.k_eq > result_ph7.k_eq, \
                "Expected larger K_eq at lower pH for proton-consuming reaction"
        
        except ValueError as e:
            if "unavailable" in str(e) or "not found" in str(e):
                pytest.skip("Test data not available in static provider")
            else:
                raise
    
    def test_k_eq_uses_corrected_delta_g(self):
        """Test that K_eq is calculated from corrected ΔG'°."""
        try:
            result = self.calculator.calculate_delta_g_reaction(
                reactants={"C00002": 1.0},
                products={"C00008": 1.0},
                ph=7.0,
                temperature=298.15,
                n_protons=-1
            )
            
            # Calculate expected K_eq from delta_g_prime
            R = 8.314  # J/(mol·K)
            T = 298.15
            delta_g_joules = result.delta_g_prime * 1000
            expected_k_eq = math.exp(-delta_g_joules / (R * T))
            
            # K_eq should match expected value (within floating point tolerance)
            assert abs(result.k_eq - expected_k_eq) / expected_k_eq < 1e-6, \
                "K_eq should be calculated from corrected ΔG'°"
        
        except ValueError as e:
            if "unavailable" in str(e) or "not found" in str(e):
                pytest.skip("Test data not available in static provider")
            else:
                raise
    
    def test_delta_g_actual_uses_corrected_value(self):
        """Test that ΔG_actual is calculated from corrected ΔG'°."""
        try:
            concentrations = {
                "C00002": 0.001,  # 1 mM ATP
                "C00008": 0.001   # 1 mM ADP
            }
            
            result = self.calculator.calculate_delta_g_reaction(
                reactants={"C00002": 1.0},
                products={"C00008": 1.0},
                concentrations=concentrations,
                ph=7.0,
                temperature=298.15,
                n_protons=-1
            )
            
            # Calculate expected ΔG_actual from delta_g_prime
            R = 8.314  # J/(mol·K)
            T = 298.15
            Q = result.reaction_quotient
            expected_delta_g_actual = result.delta_g_prime + (R * T / 1000) * math.log(Q)
            
            # ΔG_actual should match expected value (within tolerance)
            assert abs(result.delta_g_actual - expected_delta_g_actual) < 0.01, \
                "ΔG_actual should be calculated from corrected ΔG'°"
        
        except ValueError as e:
            if "unavailable" in str(e) or "not found" in str(e):
                pytest.skip("Test data not available in static provider")
            else:
                raise


class TestPHCorrectionIntegration:
    """Integration tests for pH correction."""
    
    def test_multiple_proton_stoichiometry(self):
        """Test pH correction with multiple protons."""
        calculator = GibbsCalculator(
            compound_provider=StaticThermodynamicProvider()
        )
        
        try:
            # Reaction producing 2 protons
            result_2h = calculator.calculate_delta_g_reaction(
                reactants={"C00002": 1.0},
                products={"C00008": 1.0},
                ph=7.0,
                n_protons=-2
            )
            
            # Reaction producing 1 proton
            result_1h = calculator.calculate_delta_g_reaction(
                reactants={"C00002": 1.0},
                products={"C00008": 1.0},
                ph=7.0,
                n_protons=-1
            )
            
            # More protons produced → larger correction
            correction_2h = abs(result_2h.delta_g_prime - result_2h.delta_g_standard)
            correction_1h = abs(result_1h.delta_g_prime - result_1h.delta_g_standard)
            
            assert correction_2h > correction_1h, \
                "Expected larger correction for more protons"
        
        except ValueError as e:
            if "unavailable" in str(e) or "not found" in str(e):
                pytest.skip("Test data not available")
            else:
                raise


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
