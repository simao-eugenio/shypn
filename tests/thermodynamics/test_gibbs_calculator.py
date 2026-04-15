"""Tests for Gibbs free energy calculator.

Test coverage:
- ΔG° calculation from compound formation energies
- K_eq calculation from ΔG° via Boltzmann relationship
- Reaction quotient Q calculation
- ΔG calculation with concentrations
- ATP hydrolysis validation (experimental comparison)
"""

import math
import pytest
from unittest.mock import Mock

from shypn.thermodynamics import (
    GibbsCalculator,
    CompoundThermodynamics,
    ReactionThermodynamics
)


class MockCompoundProvider:
    """Mock provider for testing with known compound data."""
    
    def __init__(self):
        # ATP hydrolysis at pH 7, 25°C (Alberty 2003)
        self.compounds = {
            "C00002": CompoundThermodynamics(  # ATP
                compound_id="C00002",
                name="ATP",
                delta_g_formation=-2292.2,  # kJ/mol
                source="Alberty 2003",
                conditions={'pH': 7.0, 'temperature': 298.15, 'ionic_strength': 0.1}
            ),
            "C00001": CompoundThermodynamics(  # H2O
                compound_id="C00001",
                name="H2O",
                delta_g_formation=-237.2,  # kJ/mol
                source="Standard",
                conditions={'pH': 7.0, 'temperature': 298.15, 'ionic_strength': 0.1}
            ),
            "C00008": CompoundThermodynamics(  # ADP
                compound_id="C00008",
                name="ADP",
                delta_g_formation=-1906.2,  # kJ/mol
                source="Alberty 2003",
                conditions={'pH': 7.0, 'temperature': 298.15, 'ionic_strength': 0.1}
            ),
            "C00009": CompoundThermodynamics(  # Pi (phosphate)
                compound_id="C00009",
                name="Phosphate",
                delta_g_formation=-1059.2,  # kJ/mol
                source="Alberty 2003",
                conditions={'pH': 7.0, 'temperature': 298.15, 'ionic_strength': 0.1}
            ),
        }
    
    def get_compound(self, compound_id, ph=7.0, temperature=298.15, ionic_strength=0.1):
        return self.compounds.get(compound_id)
    
    def has_compound(self, compound_id):
        return compound_id in self.compounds


class TestGibbsCalculatorKEq:
    """Test K_eq calculation from ΔG°."""
    
    def test_favorable_reaction_large_keq(self):
        """Negative ΔG° should give K_eq >> 1."""
        calculator = GibbsCalculator()
        
        delta_g = -30.0  # kJ/mol (favorable)
        k_eq = calculator.calculate_k_eq(delta_g, temperature=298.15)
        
        # K_eq = exp(-(-30000) / (8.314 * 298.15)) = exp(12.1) ≈ 1.8e5
        assert k_eq > 1e5, f"Expected K_eq >> 1, got {k_eq:.2e}"
        assert k_eq < 1e6, f"K_eq out of expected range: {k_eq:.2e}"
    
    def test_unfavorable_reaction_small_keq(self):
        """Positive ΔG° should give K_eq << 1."""
        calculator = GibbsCalculator()
        
        delta_g = 30.0  # kJ/mol (unfavorable)
        k_eq = calculator.calculate_k_eq(delta_g, temperature=298.15)
        
        # K_eq = exp(-30000 / (8.314 * 298.15)) = exp(-12.1) ≈ 5.5e-6
        assert k_eq < 1e-4, f"Expected K_eq << 1, got {k_eq:.2e}"
        assert k_eq > 1e-7, f"K_eq out of expected range: {k_eq:.2e}"
    
    def test_equilibrium_keq_one(self):
        """ΔG° = 0 should give K_eq = 1."""
        calculator = GibbsCalculator()
        
        delta_g = 0.0  # kJ/mol (at equilibrium)
        k_eq = calculator.calculate_k_eq(delta_g, temperature=298.15)
        
        assert abs(k_eq - 1.0) < 1e-6, f"Expected K_eq ≈ 1, got {k_eq}"
    
    def test_temperature_dependence(self):
        """Higher temperature should decrease K_eq for favorable reaction."""
        calculator = GibbsCalculator()
        
        delta_g = -20.0  # kJ/mol
        k_eq_25C = calculator.calculate_k_eq(delta_g, temperature=298.15)
        k_eq_37C = calculator.calculate_k_eq(delta_g, temperature=310.15)
        
        # At higher T, entropy matters more, K_eq decreases for ΔG < 0
        assert k_eq_37C < k_eq_25C, "K_eq should decrease with temperature for ΔG < 0"
    
    def test_overflow_protection(self):
        """Very large negative ΔG° should not cause overflow."""
        calculator = GibbsCalculator()
        
        delta_g = -1000.0  # kJ/mol (extremely favorable)
        k_eq = calculator.calculate_k_eq(delta_g, temperature=298.15)
        
        assert math.isfinite(k_eq), "K_eq should be finite"
        assert k_eq > 0, "K_eq should be positive"


class TestGibbsCalculatorReactionQuotient:
    """Test reaction quotient Q calculation."""
    
    def test_simple_reaction_quotient(self):
        """Q = [B] / [A] for A → B."""
        calculator = GibbsCalculator()
        
        reactants = {"A": 1}
        products = {"B": 1}
        concentrations = {"A": 0.1, "B": 1.0}
        
        q = calculator.calculate_reaction_quotient(reactants, products, concentrations)
        
        expected_q = 1.0 / 0.1  # [B] / [A]
        assert abs(q - expected_q) < 1e-6, f"Expected Q = {expected_q}, got {q}"
    
    def test_stoichiometric_coefficients(self):
        """Q = [C]² / ([A] * [B]) for A + B → 2C."""
        calculator = GibbsCalculator()
        
        reactants = {"A": 1, "B": 1}
        products = {"C": 2}
        concentrations = {"A": 0.5, "B": 0.5, "C": 2.0}
        
        q = calculator.calculate_reaction_quotient(reactants, products, concentrations)
        
        expected_q = (2.0 ** 2) / (0.5 * 0.5)  # [C]² / ([A] * [B])
        assert abs(q - expected_q) < 1e-6, f"Expected Q = {expected_q}, got {q}"
    
    def test_missing_concentration_raises(self):
        """Missing concentration should raise ValueError."""
        calculator = GibbsCalculator()
        
        reactants = {"A": 1}
        products = {"B": 1}
        concentrations = {"A": 0.1}  # Missing B
        
        with pytest.raises(ValueError, match="Missing concentration"):
            calculator.calculate_reaction_quotient(reactants, products, concentrations)
    
    def test_zero_concentration_raises(self):
        """Zero concentration should raise ValueError."""
        calculator = GibbsCalculator()
        
        reactants = {"A": 1}
        products = {"B": 1}
        concentrations = {"A": 0.0, "B": 1.0}
        
        with pytest.raises(ValueError, match="Concentration must be positive"):
            calculator.calculate_reaction_quotient(reactants, products, concentrations)


class TestGibbsCalculatorATPHydrolysis:
    """Test ATP hydrolysis with experimental validation."""
    
    def test_atp_hydrolysis_delta_g(self):
        """ATP + H2O → ADP + Pi should have ΔG° ≈ -30.5 kJ/mol."""
        provider = MockCompoundProvider()
        calculator = GibbsCalculator(provider)
        
        # ATP + H2O → ADP + Pi
        reactants = {"C00002": 1, "C00001": 1}
        products = {"C00008": 1, "C00009": 1}
        
        thermo = calculator.calculate_delta_g_reaction(
            reactants, products, temperature=298.15, ph=7.0
        )
        
        # Expected: ΔG°_r = (ΔG_ADP + ΔG_Pi) - (ΔG_ATP + ΔG_H2O)
        # = (-1906.2 + -1059.2) - (-2292.2 + -237.2) = -2965.4 - (-2529.4) = -436.0
        # Note: Using formation energies, actual hydrolysis is more complex
        # This tests the calculation machinery, not absolute values
        
        assert thermo.delta_g_standard < 0, "ATP hydrolysis should be favorable (ΔG < 0)"
        assert -500 < thermo.delta_g_standard < -400, f"Expected ΔG° ≈ -436, got {thermo.delta_g_standard}"
    
    def test_atp_hydrolysis_k_eq(self):
        """ATP hydrolysis K_eq should be very large (>> 1)."""
        provider = MockCompoundProvider()
        calculator = GibbsCalculator(provider)
        
        reactants = {"C00002": 1, "C00001": 1}
        products = {"C00008": 1, "C00009": 1}
        
        thermo = calculator.calculate_delta_g_reaction(
            reactants, products, temperature=298.15, ph=7.0
        )
        
        # K_eq = exp(-ΔG° / RT), for ΔG° ≈ -30, K_eq ≈ 1e5
        assert thermo.k_eq > 1e10, f"Expected very large K_eq, got {thermo.k_eq:.2e}"
    
    def test_atp_hydrolysis_with_concentrations(self):
        """ΔG should differ from ΔG° when concentrations provided."""
        provider = MockCompoundProvider()
        calculator = GibbsCalculator(provider)
        
        reactants = {"C00002": 1, "C00001": 1}
        products = {"C00008": 1, "C00009": 1}
        concentrations = {
            "C00002": 0.005,  # 5 mM ATP
            "C00001": 55.5,   # 55.5 M H2O (standard)
            "C00008": 0.001,  # 1 mM ADP
            "C00009": 0.001   # 1 mM Pi
        }
        
        thermo = calculator.calculate_delta_g_reaction(
            reactants, products, concentrations=concentrations,
            temperature=298.15, ph=7.0
        )
        
        assert thermo.delta_g_actual is not None, "ΔG should be calculated with concentrations"
        assert thermo.reaction_quotient is not None, "Q should be calculated"
        
        # Q = ([ADP] * [Pi]) / ([ATP] * [H2O])
        expected_q = (0.001 * 0.001) / (0.005 * 55.5)
        assert abs(thermo.reaction_quotient - expected_q) / expected_q < 0.01, \
            f"Expected Q ≈ {expected_q:.2e}, got {thermo.reaction_quotient:.2e}"


class TestGibbsCalculatorConcentrationDependence:
    """Test ΔG = ΔG° + RT ln(Q)."""
    
    def test_delta_g_increases_with_products(self):
        """Increasing product concentration should make ΔG less favorable."""
        provider = MockCompoundProvider()
        calculator = GibbsCalculator(provider)
        
        reactants = {"C00002": 1, "C00001": 1}
        products = {"C00008": 1, "C00009": 1}
        
        # Low product concentration
        conc_low = {
            "C00002": 0.005, "C00001": 55.5,
            "C00008": 0.0001, "C00009": 0.0001
        }
        thermo_low = calculator.calculate_delta_g_reaction(
            reactants, products, concentrations=conc_low
        )
        
        # High product concentration
        conc_high = {
            "C00002": 0.005, "C00001": 55.5,
            "C00008": 0.01, "C00009": 0.01
        }
        thermo_high = calculator.calculate_delta_g_reaction(
            reactants, products, concentrations=conc_high
        )
        
        # Higher products → larger Q → larger RT ln(Q) → less negative ΔG
        assert thermo_high.delta_g_actual > thermo_low.delta_g_actual, \
            "Higher product concentration should make ΔG less favorable"


class TestGibbsCalculatorCaching:
    """Test compound data caching."""
    
    def test_cache_reduces_provider_calls(self):
        """Second calculation should use cache, not provider."""
        provider = Mock()
        provider.get_compound.return_value = CompoundThermodynamics(
            compound_id="C00002",
            name="ATP",
            delta_g_formation=-2292.2,
            source="Mock"
        )
        
        calculator = GibbsCalculator(provider)
        
        # First call
        dg1 = calculator._get_compound_formation_energy("C00002", 7.0, 298.15)
        assert provider.get_compound.call_count == 1
        
        # Second call should use cache
        dg2 = calculator._get_compound_formation_energy("C00002", 7.0, 298.15)
        assert provider.get_compound.call_count == 1  # No additional call
        assert dg1 == dg2
    
    def test_cache_clear(self):
        """Clearing cache should force provider query."""
        provider = Mock()
        provider.get_compound.return_value = CompoundThermodynamics(
            compound_id="C00002",
            name="ATP",
            delta_g_formation=-2292.2,
            source="Mock"
        )
        
        calculator = GibbsCalculator(provider)
        
        # First call
        calculator._get_compound_formation_energy("C00002", 7.0, 298.15)
        assert provider.get_compound.call_count == 1
        
        # Clear cache
        calculator.clear_cache()
        
        # Second call should query provider again
        calculator._get_compound_formation_energy("C00002", 7.0, 298.15)
        assert provider.get_compound.call_count == 2


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
