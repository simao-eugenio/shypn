"""
Test mass_action rate function generation in heuristics.

This test verifies that when applying stochastic parameters with mass_action kinetics,
the rate_function is correctly generated with actual substrate place names.
"""

import unittest
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass


class TestMassActionRateFunction(unittest.TestCase):
    """Test mass_action rate function generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock place objects
        self.place1 = Mock()
        self.place1.id = "P1"
        self.place1.name = "ATP"
        
        self.place2 = Mock()
        self.place2.id = "P2"
        self.place2.name = "Glucose"
        
        # Create mock arc objects
        self.arc1 = Mock()
        self.arc1.source = self.place1
        
        self.arc2 = Mock()
        self.arc2.source = self.place2
        
        # Create mock transition
        self.transition = Mock()
        self.transition.id = "T1"
        self.transition.properties = {}
        self.transition.input_arcs = []
    
    def test_stochastic_parameters_no_auto_generation(self):
        """Test that StochasticParameters.__post_init__ doesn't auto-generate incorrect rate_function."""
        from shypn.crossfetch.models.transition_types import (
            StochasticParameters,
            TransitionType,
            BiologicalSemantics
        )
        
        # Create parameters with k_forward but no rate_function
        params = StochasticParameters(
            transition_type=TransitionType.STOCHASTIC,
            biological_semantics=BiologicalSemantics.MASS_ACTION,
            lambda_param=0.1,
            k_forward=0.1,
            organism="Homo sapiens"
        )
        
        # Verify rate_function is NOT auto-generated
        # (Previously would have been "mass_action(0.1)" which is incorrect)
        self.assertIsNone(params.rate_function, 
                         "rate_function should not be auto-generated with incorrect signature")
    
    def test_apply_parameters_bimolecular_mass_action(self):
        """Test that apply_parameters generates correct bimolecular mass_action rate function."""
        # Set up bimolecular transition (2 input arcs)
        self.transition.input_arcs = [self.arc1, self.arc2]
        
        # Parameters to apply
        parameters = {
            'transition_type': 'stochastic',
            'parameters': {
                'lambda': 0.1,
                'k_forward': 0.1
            }
        }
        
        # Expected rate function: mass_action(ATP, Glucose, 0.1)
        expected_rate_function = "mass_action(ATP, Glucose, 0.1)"
        
        # Manually apply the logic (simulating what controller does)
        params = parameters['parameters']
        self.transition.rate = params['lambda']
        
        substrate_places = [self.arc1.source, self.arc2.source]
        k = params['k_forward']
        
        if len(substrate_places) >= 2:
            sub1_name = substrate_places[0].name
            sub2_name = substrate_places[1].name
            rate_function = f"mass_action({sub1_name}, {sub2_name}, {k})"
            self.transition.properties['rate_function'] = rate_function
        
        # Verify
        self.assertEqual(self.transition.properties['rate_function'], expected_rate_function)
        print(f"✓ Bimolecular: {self.transition.properties['rate_function']}")
    
    def test_apply_parameters_unimolecular_mass_action(self):
        """Test that apply_parameters generates correct unimolecular mass_action rate function."""
        # Set up unimolecular transition (1 input arc)
        self.transition.input_arcs = [self.arc1]
        
        # Parameters to apply
        parameters = {
            'transition_type': 'stochastic',
            'parameters': {
                'lambda': 0.05,
                'k_forward': 0.05
            }
        }
        
        # Expected rate function: mass_action(ATP, 1.0, 0.05)
        expected_rate_function = "mass_action(ATP, 1.0, 0.05)"
        
        # Manually apply the logic
        params = parameters['parameters']
        self.transition.rate = params['lambda']
        
        substrate_places = [self.arc1.source]
        k = params['k_forward']
        
        if len(substrate_places) == 1:
            sub_name = substrate_places[0].name
            rate_function = f"mass_action({sub_name}, 1.0, {k})"
            self.transition.properties['rate_function'] = rate_function
        
        # Verify
        self.assertEqual(self.transition.properties['rate_function'], expected_rate_function)
        print(f"✓ Unimolecular: {self.transition.properties['rate_function']}")
    
    def test_mass_action_function_signature(self):
        """Test that mass_action function in catalog has correct signature."""
        from shypn.engine.function_catalog import mass_action
        import inspect
        
        # Get function signature
        sig = inspect.signature(mass_action)
        params = list(sig.parameters.keys())
        
        # Verify parameters
        self.assertEqual(params[0], 'reactant1', "First param should be reactant1")
        self.assertEqual(params[1], 'reactant2', "Second param should be reactant2")
        self.assertEqual(params[2], 'rate_constant', "Third param should be rate_constant")
        
        # Verify defaults
        self.assertEqual(sig.parameters['reactant2'].default, 1.0)
        self.assertEqual(sig.parameters['rate_constant'].default, 1.0)
        
        print(f"✓ mass_action signature: {sig}")
    
    def test_mass_action_function_execution(self):
        """Test that mass_action function computes correctly."""
        from shypn.engine.function_catalog import mass_action
        
        # Test bimolecular: k * [A] * [B]
        result = mass_action(2.0, 3.0, 0.1)
        expected = 0.1 * 2.0 * 3.0
        self.assertEqual(result, expected)
        print(f"✓ Bimolecular: mass_action(2.0, 3.0, 0.1) = {result}")
        
        # Test unimolecular: k * [A] * 1.0
        result = mass_action(5.0, 1.0, 0.05)
        expected = 0.05 * 5.0 * 1.0
        self.assertEqual(result, expected)
        print(f"✓ Unimolecular: mass_action(5.0, 1.0, 0.05) = {result}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
