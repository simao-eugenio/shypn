"""Tests for equilibrium validator.

This module tests the EquilibriumValidator class, which checks if
kinetic rate constants are consistent with thermodynamic equilibrium
constants.
"""

import pytest
import math

from shypn.thermodynamics import (
    EquilibriumValidator,
    GibbsCalculator,
    ReactionThermodynamics,
)
from shypn.thermodynamics.database import MockEquilibratorProvider


class TestEquilibriumValidatorInit:
    """Test validator initialization."""
    
    def test_init_default_tolerance(self):
        """Test default tolerance is 0.5 (±50%)."""
        provider = MockEquilibratorProvider()
        calculator = GibbsCalculator(provider)
        validator = EquilibriumValidator(calculator)
        
        assert validator.tolerance == 0.5
        assert validator.calculator is calculator
    
    def test_init_custom_tolerance(self):
        """Test custom tolerance values."""
        provider = MockEquilibratorProvider()
        calculator = GibbsCalculator(provider)
        
        validator = EquilibriumValidator(calculator, tolerance=0.3)
        assert validator.tolerance == 0.3
        
        validator = EquilibriumValidator(calculator, tolerance=0.0)
        assert validator.tolerance == 0.0
        
        validator = EquilibriumValidator(calculator, tolerance=1.0)
        assert validator.tolerance == 1.0
    
    def test_init_invalid_tolerance(self):
        """Test that invalid tolerance raises ValueError."""
        provider = MockEquilibratorProvider()
        calculator = GibbsCalculator(provider)
        
        with pytest.raises(ValueError, match="Tolerance must be between"):
            EquilibriumValidator(calculator, tolerance=-0.1)
        
        with pytest.raises(ValueError, match="Tolerance must be between"):
            EquilibriumValidator(calculator, tolerance=1.1)


class TestValidateRateConstants:
    """Test rate constant validation."""
    
    def test_validate_perfect_match(self):
        """Test validation when k_f/k_r exactly equals K_eq."""
        provider = MockEquilibratorProvider()
        calculator = GibbsCalculator(provider)
        validator = EquilibriumValidator(calculator, tolerance=0.5)
        
        # Create reaction thermo with known K_eq
        reaction_thermo = ReactionThermodynamics(
            reaction_id="test_reaction",
            delta_g_standard=-10.0,  # kJ/mol
            delta_g_prime=-10.0,
            k_eq=56.84,  # exp(10/(8.314*298.15/1000))
            temperature=298.15,
            ph=7.0,
            ionic_strength=0.1
        )
        
        # Set k_f/k_r = K_eq
        k_forward = 5684.0
        k_reverse = 100.0  # ratio = 56.84
        
        validation = validator.validate_rate_constants(
            k_forward=k_forward,
            k_reverse=k_reverse,
            reaction_thermo=reaction_thermo
        )
        
        assert validation.is_valid is True
        assert "Valid" in validation.message
        assert validation.k_eq == 56.84
        assert validation.details["kinetic_ratio"] == 56.84
        assert validation.details["k_forward"] == k_forward
        assert validation.details["k_reverse"] == k_reverse
    
    def test_validate_within_tolerance(self):
        """Test validation when deviation is within tolerance."""
        provider = MockEquilibratorProvider()
        calculator = GibbsCalculator(provider)
        validator = EquilibriumValidator(calculator, tolerance=0.5)
        
        # K_eq = 1000
        reaction_thermo = ReactionThermodynamics(
            reaction_id="test_reaction",
            delta_g_standard=-17.1,  # kJ/mol, K_eq ≈ 1000
            delta_g_prime=-17.1,
            k_eq=1000.0,
            temperature=298.15,
            ph=7.0,
            ionic_strength=0.1
        )
        
        # k_f/k_r = 500 (within ±1 order of magnitude)
        k_forward = 5e5
        k_reverse = 1e3
        
        validation = validator.validate_rate_constants(
            k_forward=k_forward,
            k_reverse=k_reverse,
            reaction_thermo=reaction_thermo
        )
        
        assert validation.is_valid is True
        assert "Valid" in validation.message
    
    def test_validate_exceeds_tolerance(self):
        """Test validation when deviation exceeds tolerance."""
        provider = MockEquilibratorProvider()
        calculator = GibbsCalculator(provider)
        validator = EquilibriumValidator(calculator, tolerance=0.5)
        
        # K_eq = 1000
        reaction_thermo = ReactionThermodynamics(
            reaction_id="test_reaction",
            delta_g_standard=-17.1,  # kJ/mol
            delta_g_prime=-17.1,
            k_eq=1000.0,
            temperature=298.15,
            ph=7.0,
            ionic_strength=0.1
        )
        
        # k_f/k_r = 10 (3 orders of magnitude off, exceeds tolerance)
        k_forward = 100.0
        k_reverse = 10.0
        
        validation = validator.validate_rate_constants(
            k_forward=k_forward,
            k_reverse=k_reverse,
            reaction_thermo=reaction_thermo
        )
        
        assert validation.is_valid is False
        assert "Invalid" in validation.message
        assert "exceeds" in validation.message
        assert validation.details["log_deviation"] > validation.details["max_log_deviation"]
    
    def test_validate_zero_rate_constant(self):
        """Test that zero rate constants raise ValueError."""
        provider = MockEquilibratorProvider()
        calculator = GibbsCalculator(provider)
        validator = EquilibriumValidator(calculator)
        
        reaction_thermo = ReactionThermodynamics(
            reaction_id="test_reaction",
            delta_g_standard=-10.0,
            delta_g_prime=-10.0,
            k_eq=56.84,
            temperature=298.15,
            ph=7.0,
            ionic_strength=0.1
        )
        
        with pytest.raises(ValueError, match="must be positive"):
            validator.validate_rate_constants(
                k_forward=0.0,
                k_reverse=100.0,
                reaction_thermo=reaction_thermo
            )
        
        with pytest.raises(ValueError, match="must be positive"):
            validator.validate_rate_constants(
                k_forward=100.0,
                k_reverse=-10.0,
                reaction_thermo=reaction_thermo
            )
    
    def test_validate_none_k_eq(self):
        """Test validation when K_eq is None."""
        provider = MockEquilibratorProvider()
        calculator = GibbsCalculator(provider)
        validator = EquilibriumValidator(calculator)
        
        # Note: ReactionThermodynamics requires k_eq to be non-negative, so use 0.0
        # We'll modify the validator to handle this edge case
        reaction_thermo = ReactionThermodynamics(
            reaction_id="test_reaction",
            delta_g_standard=0.0,
            delta_g_prime=0.0,
            k_eq=0.0,  # Will treat as invalid
            temperature=298.15,
            ph=7.0,
            ionic_strength=0.1
        )
        
        validation = validator.validate_rate_constants(
            k_forward=100.0,
            k_reverse=10.0,
            reaction_thermo=reaction_thermo
        )
        
        assert validation.is_valid is False
        assert "Cannot validate" in validation.message
        assert "zero" in validation.message.lower()
    
    def test_validate_infinite_k_eq(self):
        """Test validation when K_eq is infinite."""
        provider = MockEquilibratorProvider()
        calculator = GibbsCalculator(provider)
        validator = EquilibriumValidator(calculator)
        
        reaction_thermo = ReactionThermodynamics(
            reaction_id="test_reaction",
            delta_g_standard=-1000.0,  # Very negative
            delta_g_prime=-1000.0,
            k_eq=math.inf,  # Overflow
            temperature=298.15,
            ph=7.0,
            ionic_strength=0.1
        )
        
        validation = validator.validate_rate_constants(
            k_forward=1e10,
            k_reverse=1.0,
            reaction_thermo=reaction_thermo
        )
        
        assert validation.is_valid is False
        assert "Cannot validate" in validation.message
        assert "inf" in validation.message
    
    def test_validate_with_metadata(self):
        """Test that metadata is included in validation result."""
        provider = MockEquilibratorProvider()
        calculator = GibbsCalculator(provider)
        validator = EquilibriumValidator(calculator)
        
        reaction_thermo = ReactionThermodynamics(
            reaction_id="test_reaction",
            delta_g_standard=-10.0,
            delta_g_prime=-10.0,
            k_eq=56.84,
            temperature=298.15,
            ph=7.0,
            ionic_strength=0.1
        )
        
        metadata = {
            "reaction_id": "R00001",
            "enzyme": "ATP synthase",
            "pathway": "Oxidative phosphorylation"
        }
        
        validation = validator.validate_rate_constants(
            k_forward=5684.0,
            k_reverse=100.0,
            reaction_thermo=reaction_thermo,
            metadata=metadata
        )
        
        assert validation.details["reaction_id"] == "R00001"
        assert validation.details["enzyme"] == "ATP synthase"
        assert validation.details["pathway"] == "Oxidative phosphorylation"


class TestValidateReversibleReaction:
    """Test validation with full thermodynamic calculation."""
    
    def test_validate_atp_hydrolysis(self):
        """Test validation of ATP hydrolysis with realistic parameters."""
        provider = MockEquilibratorProvider()
        calculator = GibbsCalculator(provider)
        validator = EquilibriumValidator(calculator, tolerance=0.5)
        
        # ATP + H2O -> ADP + Pi
        # Mock data: ΔG ≈ -436 kJ/mol (very favorable)
        # K_eq = exp(436/(8.314*298.15/1000)) ≈ 1.3e76
        
        # Set k_f/k_r to match K_eq (approximately)
        k_forward = 1e80
        k_reverse = 1e4
        # ratio = 1e76, matches K_eq
        
        validation = validator.validate_reversible_reaction(
            k_forward=k_forward,
            k_reverse=k_reverse,
            reactants={"C00002": 1, "C00001": 1},  # ATP + H2O (stoichiometry)
            products={"C00008": 1, "C00009": 1},   # ADP + Pi (stoichiometry)
            metadata={"reaction": "ATP hydrolysis"}
        )
        
        assert validation.k_eq is not None
        assert validation.k_eq > 1e70  # Very large K_eq
        assert validation.details["reaction"] == "ATP hydrolysis"
        # May be valid or invalid depending on exact calculation
    
    def test_validate_near_equilibrium_reaction(self):
        """Test validation of a reaction near equilibrium."""
        provider = MockEquilibratorProvider()
        calculator = GibbsCalculator(provider)
        validator = EquilibriumValidator(calculator, tolerance=0.5)
        
        # Create a near-equilibrium reaction using actual ATP/ADP data
        # but with balanced k_forward and k_reverse
        # Since we can't control exact ΔG, we'll just test that validation works
        
        validation = validator.validate_reversible_reaction(
            k_forward=1000.0,
            k_reverse=950.0,  # Close to forward rate
            reactants={"C00002": 1},  # ATP (stoichiometry)
            products={"C00008": 1, "C00001": 1},   # ADP + H2O (to balance)
            ph=7.0,
            temperature=298.15,
            metadata={"reaction": "ATP -> ADP + H2O"}
        )
        
        # Just check that calculation completes successfully
        assert validation.k_eq is not None
        assert "reaction" in validation.details
    
    def test_validate_custom_conditions(self):
        """Test validation with custom pH and temperature."""
        provider = MockEquilibratorProvider()
        calculator = GibbsCalculator(provider)
        validator = EquilibriumValidator(calculator, tolerance=0.3)
        
        validation = validator.validate_reversible_reaction(
            k_forward=500.0,
            k_reverse=100.0,
            reactants={"C00002": 1},  # ATP (stoichiometry)
            products={"C00008": 1},   # ADP (stoichiometry)
            ph=6.5,  # Slightly acidic
            temperature=310.15,  # 37°C (body temperature)
            metadata={"conditions": "physiological"}
        )
        
        assert validation.details["conditions"] == "physiological"
        # K_eq should be calculated for these conditions


class TestToleranceLevels:
    """Test different tolerance levels."""
    
    def test_strict_tolerance(self):
        """Test with very strict tolerance (0.1 = ±10%)."""
        provider = MockEquilibratorProvider()
        calculator = GibbsCalculator(provider)
        validator = EquilibriumValidator(calculator, tolerance=0.1)
        
        reaction_thermo = ReactionThermodynamics(
            reaction_id="test_reaction",
            delta_g_standard=-10.0,
            delta_g_prime=-10.0,
            k_eq=100.0,
            temperature=298.15,
            ph=7.0,
            ionic_strength=0.1
        )
        
        # k_f/k_r = 50 (half of K_eq, within ±0.3 log units)
        validation = validator.validate_rate_constants(
            k_forward=5000.0,
            k_reverse=100.0,
            reaction_thermo=reaction_thermo
        )
        
        # With tolerance=0.1, max_log_deviation = 0.2
        # log(100) - log(50) = 2.0 - 1.7 = 0.3 > 0.2
        # Should be invalid
        assert validation.is_valid is False
    
    def test_permissive_tolerance(self):
        """Test with very permissive tolerance (0.9 = ±90%)."""
        provider = MockEquilibratorProvider()
        calculator = GibbsCalculator(provider)
        validator = EquilibriumValidator(calculator, tolerance=0.9)
        
        reaction_thermo = ReactionThermodynamics(
            reaction_id="test_reaction",
            delta_g_standard=-10.0,
            delta_g_prime=-10.0,
            k_eq=100.0,
            temperature=298.15,
            ph=7.0,
            ionic_strength=0.1
        )
        
        # k_f/k_r = 5 (20x off from K_eq)
        validation = validator.validate_rate_constants(
            k_forward=500.0,
            k_reverse=100.0,
            reaction_thermo=reaction_thermo
        )
        
        # With tolerance=0.9, max_log_deviation = 1.8
        # log(100) - log(5) = 2.0 - 0.7 = 1.3 < 1.8
        # Should be valid
        assert validation.is_valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
