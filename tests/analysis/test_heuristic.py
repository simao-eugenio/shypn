"""
Unit tests for kinetic parameter heuristics.

Tests all three estimators:
- MichaelisMentenEstimator
- StochasticEstimator
- MassActionEstimator
"""

import pytest
from unittest.mock import Mock
from src.shypn.heuristic import (
    EstimatorFactory,
    MichaelisMentenEstimator,
    StochasticEstimator,
    MassActionEstimator
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_reaction_simple():
    """Single substrate, single product reaction."""
    reaction = Mock()
    reaction.id = "R1"
    reaction.name = "R1"
    reaction.reactants = [("S1", 1)]  # (id, stoichiometry)
    reaction.products = [("P1", 1)]
    reaction.reversible = False
    return reaction


@pytest.fixture
def mock_reaction_multi():
    """Multiple substrates, multiple products."""
    reaction = Mock()
    reaction.id = "R2"
    reaction.name = "R2"
    reaction.reactants = [("S1", 1), ("S2", 1)]
    reaction.products = [("P1", 2), ("P2", 1)]
    reaction.reversible = False
    return reaction


@pytest.fixture
def mock_reaction_reversible():
    """Reversible reaction."""
    reaction = Mock()
    reaction.id = "R3"
    reaction.name = "R3"
    reaction.reactants = [("S1", 1)]
    reaction.products = [("P1", 1)]
    reaction.reversible = True
    return reaction


@pytest.fixture
def mock_place():
    """Create a mock place with tokens."""
    def _create(name, tokens=10):
        place = Mock()
        place.name = name
        place.tokens = tokens
        return place
    return _create


# ============================================================================
# Factory Tests
# ============================================================================

class TestEstimatorFactory:
    """Test factory pattern."""
    
    def test_create_michaelis_menten(self):
        """Factory creates MichaelisMentenEstimator."""
        estimator = EstimatorFactory.create('michaelis_menten')
        assert isinstance(estimator, MichaelisMentenEstimator)
    
    def test_create_stochastic(self):
        """Factory creates StochasticEstimator."""
        estimator = EstimatorFactory.create('stochastic')
        assert isinstance(estimator, StochasticEstimator)
    
    def test_create_mass_action(self):
        """Factory creates MassActionEstimator."""
        estimator = EstimatorFactory.create('mass_action')
        assert isinstance(estimator, MassActionEstimator)
    
    def test_create_invalid(self):
        """Factory returns None for invalid type."""
        estimator = EstimatorFactory.create('invalid_type')
        assert estimator is None
    
    def test_available_types(self):
        """Factory lists available types."""
        types = EstimatorFactory.available_types()
        assert 'michaelis_menten' in types
        assert 'stochastic' in types
        assert 'mass_action' in types


# ============================================================================
# Michaelis-Menten Tests
# ============================================================================

class TestMichaelisMentenEstimator:
    """Test Michaelis-Menten parameter estimation."""
    
    def test_estimate_simple_reaction(self, mock_reaction_simple, mock_place):
        """Estimate parameters for simple reaction."""
        estimator = MichaelisMentenEstimator()
        
        substrates = [mock_place("S1", tokens=10)]
        products = [mock_place("P1", tokens=0)]
        
        params = estimator.estimate_parameters(
            mock_reaction_simple, substrates, products
        )
        
        assert 'vmax' in params
        assert 'km' in params
        assert params['vmax'] == 10.0  # 10.0 * 1 (stoich)
        assert params['km'] == 5.0  # 10 / 2
    
    def test_vmax_scales_with_stoichiometry(self, mock_reaction_multi, mock_place):
        """Vmax scales with product stoichiometry."""
        estimator = MichaelisMentenEstimator()
        
        substrates = [mock_place("S1"), mock_place("S2")]
        products = [mock_place("P1"), mock_place("P2")]
        
        params = estimator.estimate_parameters(
            mock_reaction_multi, substrates, products
        )
        
        # Max product stoich is 2
        assert params['vmax'] == 20.0  # 10.0 * 2
    
    def test_reversible_reduces_vmax(self, mock_reaction_reversible, mock_place):
        """Reversible reactions have lower Vmax."""
        estimator = MichaelisMentenEstimator()
        
        substrates = [mock_place("S1")]
        products = [mock_place("P1")]
        
        params = estimator.estimate_parameters(
            mock_reaction_reversible, substrates, products
        )
        
        assert params['vmax'] == 8.0  # 10.0 * 0.8
    
    def test_km_from_multiple_substrates(self, mock_reaction_multi, mock_place):
        """Km estimated from mean concentration."""
        estimator = MichaelisMentenEstimator()
        
        substrates = [mock_place("S1", tokens=20), mock_place("S2", tokens=10)]
        products = []
        
        params = estimator.estimate_parameters(
            mock_reaction_multi, substrates, products
        )
        
        # Mean: (20 + 10) / 2 = 15, Km = 15 / 2 = 7.5
        assert params['km'] == 7.5
    
    def test_build_single_substrate(self, mock_reaction_simple, mock_place):
        """Build rate function for single substrate."""
        estimator = MichaelisMentenEstimator()
        
        substrates = [mock_place("Glucose")]
        products = []
        params = {'vmax': 10.0, 'km': 5.0}
        
        rate_func = estimator.build_rate_function(
            mock_reaction_simple, substrates, products, params
        )
        
        assert rate_func == "michaelis_menten(Glucose, 10.0, 5.0)"
    
    def test_build_multiple_substrates(self, mock_reaction_multi, mock_place):
        """Build sequential MM for multiple substrates."""
        estimator = MichaelisMentenEstimator()
        
        substrates = [mock_place("S1"), mock_place("S2")]
        products = []
        params = {'vmax': 10.0, 'km': 5.0}
        
        rate_func = estimator.build_rate_function(
            mock_reaction_multi, substrates, products, params
        )
        
        expected = "michaelis_menten(S1, 10.0, 5.0) * (S2 / (5.0 + S2))"
        assert rate_func == expected
    
    def test_estimate_and_build(self, mock_reaction_simple, mock_place):
        """Convenience method works."""
        estimator = MichaelisMentenEstimator()
        
        substrates = [mock_place("S1")]
        products = [mock_place("P1")]
        
        params, rate_func = estimator.estimate_and_build(
            mock_reaction_simple, substrates, products
        )
        
        assert 'vmax' in params
        assert 'km' in params
        assert "michaelis_menten" in rate_func
    
    def test_caching(self, mock_reaction_simple, mock_place):
        """Parameters are cached."""
        estimator = MichaelisMentenEstimator()
        
        substrates = [mock_place("S1")]
        products = [mock_place("P1")]
        
        # First call
        params1 = estimator.estimate_parameters(
            mock_reaction_simple, substrates, products
        )
        
        # Second call (should use cache)
        params2 = estimator.estimate_parameters(
            mock_reaction_simple, substrates, products
        )
        
        assert params1 == params2


# ============================================================================
# Stochastic Tests
# ============================================================================

class TestStochasticEstimator:
    """Test stochastic (exponential) parameter estimation."""
    
    def test_estimate_simple_reaction(self, mock_reaction_simple, mock_place):
        """Estimate lambda for simple reaction."""
        estimator = StochasticEstimator()
        
        substrates = [mock_place("S1", tokens=10)]
        products = []
        
        params = estimator.estimate_parameters(
            mock_reaction_simple, substrates, products
        )
        
        assert 'lambda' in params
        assert 'distribution' in params
        assert params['distribution'] == 'exponential'
        assert params['lambda'] == 1.0  # 1.0 * 1 (stoich)
    
    def test_lambda_scales_with_stoichiometry(self, mock_reaction_multi, mock_place):
        """Lambda scales with reactant stoichiometry."""
        estimator = StochasticEstimator()
        
        substrates = [mock_place("S1"), mock_place("S2")]
        products = []
        
        params = estimator.estimate_parameters(
            mock_reaction_multi, substrates, products
        )
        
        # Total reactant stoich: 1 + 1 = 2
        assert params['lambda'] == 2.0
    
    def test_low_concentration_reduces_lambda(self, mock_reaction_simple, mock_place):
        """Low substrate concentration reduces lambda."""
        estimator = StochasticEstimator()
        
        # Low concentration (< 10)
        substrates = [mock_place("S1", tokens=5)]
        products = []
        
        params = estimator.estimate_parameters(
            mock_reaction_simple, substrates, products
        )
        
        # Lambda reduced by 0.5
        assert params['lambda'] == 0.5  # 1.0 * 0.5
    
    def test_build_rate_function(self, mock_reaction_simple, mock_place):
        """Build exponential rate function."""
        estimator = StochasticEstimator()
        
        params = {'lambda': 2.5, 'distribution': 'exponential'}
        
        rate_func = estimator.build_rate_function(
            mock_reaction_simple, [], [], params
        )
        
        assert rate_func == "exponential(2.5)"
    
    def test_estimate_and_build(self, mock_reaction_simple, mock_place):
        """Convenience method works."""
        estimator = StochasticEstimator()
        
        substrates = [mock_place("S1")]
        products = []
        
        params, rate_func = estimator.estimate_and_build(
            mock_reaction_simple, substrates, products
        )
        
        assert params['distribution'] == 'exponential'
        assert "exponential" in rate_func


# ============================================================================
# Mass Action Tests
# ============================================================================

class TestMassActionEstimator:
    """Test mass action kinetics parameter estimation."""
    
    def test_estimate_unimolecular(self, mock_reaction_simple, mock_place):
        """Unimolecular reaction has k=1.0."""
        estimator = MassActionEstimator()
        
        substrates = [mock_place("S1")]
        products = []
        
        params = estimator.estimate_parameters(
            mock_reaction_simple, substrates, products
        )
        
        assert params['k'] == 1.0
    
    def test_estimate_bimolecular(self, mock_reaction_multi, mock_place):
        """Bimolecular reaction has k=0.1."""
        estimator = MassActionEstimator()
        
        substrates = [mock_place("S1"), mock_place("S2")]
        products = []
        
        params = estimator.estimate_parameters(
            mock_reaction_multi, substrates, products
        )
        
        assert params['k'] == 0.1
    
    def test_estimate_trimolecular(self, mock_place):
        """Trimolecular reaction has k=0.01."""
        estimator = MassActionEstimator()
        
        reaction = Mock()
        reaction.id = "R_tri"
        reaction.name = "R_tri"
        reaction.reactants = [("S1", 1), ("S2", 1), ("S3", 1)]
        reaction.products = [("P1", 1)]
        
        substrates = [mock_place("S1"), mock_place("S2"), mock_place("S3")]
        products = []
        
        params = estimator.estimate_parameters(reaction, substrates, products)
        
        assert params['k'] == 0.01
    
    def test_build_bimolecular(self, mock_reaction_multi, mock_place):
        """Build mass action for bimolecular."""
        estimator = MassActionEstimator()
        
        substrates = [mock_place("A"), mock_place("B")]
        products = []
        params = {'k': 0.1}
        
        rate_func = estimator.build_rate_function(
            mock_reaction_multi, substrates, products, params
        )
        
        assert rate_func == "mass_action(A, B, 0.1)"
    
    def test_build_unimolecular(self, mock_reaction_simple, mock_place):
        """Build mass action for unimolecular."""
        estimator = MassActionEstimator()
        
        substrates = [mock_place("A")]
        products = []
        params = {'k': 1.0}
        
        rate_func = estimator.build_rate_function(
            mock_reaction_simple, substrates, products, params
        )
        
        assert rate_func == "mass_action(A, 1.0, 1.0)"
    
    def test_estimate_and_build(self, mock_reaction_multi, mock_place):
        """Convenience method works."""
        estimator = MassActionEstimator()
        
        substrates = [mock_place("S1"), mock_place("S2")]
        products = []
        
        params, rate_func = estimator.estimate_and_build(
            mock_reaction_multi, substrates, products
        )
        
        assert params['k'] == 0.1
        assert "mass_action" in rate_func


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Test integration scenarios."""
    
    def test_factory_with_mm_workflow(self, mock_reaction_simple, mock_place):
        """Complete workflow with factory."""
        estimator = EstimatorFactory.create('michaelis_menten')
        
        substrates = [mock_place("Glucose", tokens=10)]
        products = [mock_place("G6P", tokens=0)]
        
        params, rate_func = estimator.estimate_and_build(
            mock_reaction_simple, substrates, products
        )
        
        assert params['vmax'] == 10.0
        assert params['km'] == 5.0
        assert rate_func == "michaelis_menten(Glucose, 10.0, 5.0)"
    
    def test_all_estimators_return_results(self, mock_reaction_simple, mock_place):
        """All estimators produce valid output."""
        substrates = [mock_place("S1")]
        products = [mock_place("P1")]
        
        for kinetic_type in EstimatorFactory.available_types():
            estimator = EstimatorFactory.create(kinetic_type)
            params, rate_func = estimator.estimate_and_build(
                mock_reaction_simple, substrates, products
            )
            
            assert params is not None
            assert rate_func is not None
            assert len(rate_func) > 0
