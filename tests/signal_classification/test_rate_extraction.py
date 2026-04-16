#!/usr/bin/env python3
"""Tests for rate function extraction (numeric, expression, catalog).

Author: Simão Eugénio
Date: December 31, 2025
"""

import unittest
from unittest.mock import Mock

import sys
sys.path.insert(0, 'src')

from shypn.analysis.signal_classification.base_classifier import BaseSignalClassifier
from shypn.analysis.signal_classification.energy_classifier import EnergySignalClassifier


class ConcreteClassifier(BaseSignalClassifier):
    """Concrete implementation for testing."""
    
    def get_signal_type(self) -> str:
        return 'TEST'
    
    def get_lexical_patterns(self):
        return []
    
    def get_biochemical_indicators(self):
        return set()
    
    def analyze_topology(self, place) -> float:
        return 0.0
    
    def analyze_dynamics(self, place, rate_functions) -> float:
        return 0.0


class TestRateFunctionExtraction(unittest.TestCase):
    """Test extraction of rate functions in all three formats."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.model = Mock()
        self.model.places = []
        self.model.transitions = []
        self.model.arcs = []
        
        self.classifier = ConcreteClassifier(self.model)
    
    def test_numeric_rate(self):
        """Test numeric rate (no place references)."""
        atp = Mock()
        atp.name = "ATP"
        
        transition = Mock()
        transition.rate = 2.5  # Numeric
        transition.kinetic_metadata = None  # Explicitly set to None
        transition.properties = {}  # No GUI rate_function
        
        self.model.transitions = [transition]
        
        expressions = self.classifier._extract_rate_expressions(transition)
        
        # Numeric rates don't produce expressions
        self.assertEqual(len(expressions), 0)
    
    def test_expression_rate_simple(self):
        """Test expression rate as string."""
        atp = Mock()
        atp.name = "ATP"
        
        transition = Mock()
        transition.rate = "2.0 * ATP * Glucose"  # Expression
        transition.kinetic_metadata = None  # Explicitly set to None
        transition.properties = {}  # No GUI rate_function
        
        self.model.transitions = [transition]
        
        expressions = self.classifier._extract_rate_expressions(transition)
        
        self.assertEqual(len(expressions), 1)
        self.assertIn("ATP", expressions[0])
        self.assertIn("Glucose", expressions[0])
    
    def test_gui_rate_function_field(self):
        """Test rate function from GUI property dialog field."""
        atp = Mock()
        atp.name = "ATP"
        
        transition = Mock()
        transition.rate = 2.5  # Numeric in Rate field
        transition.kinetic_metadata = None
        transition.properties = {
            'rate_function': "Vmax * ATP / (Km + ATP)"  # Complex expression in Rate function field
        }
        
        self.model.transitions = [transition]
        
        expressions = self.classifier._extract_rate_expressions(transition)
        
        # Should extract from properties['rate_function'], not numeric rate
        self.assertEqual(len(expressions), 1)
        self.assertIn("ATP", expressions[0])
        self.assertIn("Vmax", expressions[0])
        self.assertIn("Km", expressions[0])
    
    def test_bidirectional_rates(self):
        """Test forward and reverse rate expressions."""
        transition = Mock()
        transition.rate = None
        transition.rate_forward = "kf * ATP * Substrate"
        transition.rate_reverse = "kr * Product"
        transition.kinetic_metadata = None  # Explicitly set to None
        transition.properties = {}  # No GUI rate_function
        
        self.model.transitions = [transition]
        
        expressions = self.classifier._extract_rate_expressions(transition)
        
        self.assertEqual(len(expressions), 2)
        self.assertIn("kf * ATP * Substrate", expressions)
        self.assertIn("kr * Product", expressions)
    
    def test_catalog_michaelis_menten(self):
        """Test catalog function: Michaelis-Menten."""
        metadata = Mock()
        metadata.rate_type = "michaelis_menten"
        metadata.parameters = {'substrate': 'ATP'}
        metadata.formula = None
        
        transition = Mock()
        transition.rate = None
        transition.kinetic_metadata = metadata
        
        self.model.transitions = [transition]
        
        expressions = self.classifier._extract_rate_expressions(transition)
        
        # Should construct Michaelis-Menten pattern
        self.assertEqual(len(expressions), 1)
        self.assertIn("Vmax", expressions[0])
        self.assertIn("ATP", expressions[0])
        self.assertIn("Km", expressions[0])
    
    def test_catalog_hill(self):
        """Test catalog function: Hill equation."""
        metadata = Mock()
        metadata.rate_type = "hill"
        metadata.parameters = {'substrate': 'LuxR', 'n': 3}
        metadata.formula = None
        
        transition = Mock()
        transition.rate = None
        transition.kinetic_metadata = metadata
        
        expressions = self.classifier._extract_rate_expressions(transition)
        
        # Should construct Hill pattern with n=3
        self.assertEqual(len(expressions), 1)
        self.assertIn("LuxR^3", expressions[0])
        self.assertIn("K^3", expressions[0])
    
    def test_catalog_mass_action(self):
        """Test catalog function: Mass action."""
        metadata = Mock()
        metadata.rate_type = "mass_action"
        metadata.parameters = {'reactant1': 'ATP', 'reactant2': 'Glucose'}
        metadata.formula = None
        
        transition = Mock()
        transition.rate = None
        transition.kinetic_metadata = metadata
        
        expressions = self.classifier._extract_rate_expressions(transition)
        
        # Should construct mass action pattern
        self.assertEqual(len(expressions), 1)
        self.assertIn("ATP", expressions[0])
        self.assertIn("Glucose", expressions[0])
    
    def test_catalog_with_explicit_formula(self):
        """Test catalog function with explicit formula."""
        metadata = Mock()
        metadata.rate_type = "custom"
        metadata.parameters = {}
        metadata.formula = "Vmax * ATP / (Km + ATP) * Glucose"
        
        transition = Mock()
        transition.rate = None
        transition.kinetic_metadata = metadata
        
        expressions = self.classifier._extract_rate_expressions(transition)
        
        # Should use explicit formula
        self.assertIn("Vmax * ATP / (Km + ATP) * Glucose", expressions)
    
    def test_expression_references_place(self):
        """Test place reference detection in expressions."""
        atp = Mock()
        atp.name = "ATP"
        
        # Positive cases
        self.assertTrue(
            self.classifier._expression_references_place("2.0 * ATP", atp)
        )
        self.assertTrue(
            self.classifier._expression_references_place("ATP / (Km + ATP)", atp)
        )
        
        # Negative case: partial match should not trigger
        self.assertFalse(
            self.classifier._expression_references_place("ATPASE * Glucose", atp)
        )
    
    def test_get_rate_functions_referencing(self):
        """Test full pipeline: extract and filter by place."""
        atp = Mock()
        atp.name = "ATP"
        glucose = Mock()
        glucose.name = "Glucose"
        
        self.model.places = [atp, glucose]
        
        # Create transitions with different rate types
        t1 = Mock()
        t1.rate = "2.0 * ATP * Glucose"
        t1.kinetic_metadata = None
        
        t2 = Mock()
        t2.rate = "3.0 * Glucose"  # No ATP
        t2.kinetic_metadata = None
        
        t3_metadata = Mock()
        t3_metadata.rate_type = "michaelis_menten"
        t3_metadata.parameters = {'substrate': 'ATP'}
        t3_metadata.formula = None
        
        t3 = Mock()
        t3.rate = None
        t3.kinetic_metadata = t3_metadata
        
        self.model.transitions = [t1, t2, t3]
        
        # Get rate functions referencing ATP
        atp_funcs = self.classifier._get_rate_functions_referencing(atp)
        
        # Should find t1 and t3 (both reference ATP)
        self.assertEqual(len(atp_funcs), 2)
        self.assertTrue(any("2.0 * ATP * Glucose" in f for f in atp_funcs))
        self.assertTrue(any("ATP" in f and "Vmax" in f for f in atp_funcs))
        
        # Get rate functions referencing Glucose
        glucose_funcs = self.classifier._get_rate_functions_referencing(glucose)
        
        # Should find t1 and t2
        self.assertEqual(len(glucose_funcs), 2)


class TestEnergyClassifierWithCatalog(unittest.TestCase):
    """Test energy classifier with catalog functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.model = Mock()
        self.model.places = []
        self.model.transitions = []
        self.model.arcs = []
        
        self.classifier = EnergySignalClassifier(self.model)
    
    def test_michaelis_menten_energy_signal(self):
        """Test M-M pattern indicates energy signal."""
        atp = Mock()
        atp.name = "ATP"
        
        rate_functions = [
            "Vmax * ATP / (Km + ATP)"  # M-M pattern
        ]
        
        score = self.classifier.analyze_dynamics(atp, rate_functions)
        
        # M-M with energy compound = strong evidence
        self.assertEqual(score, 1.0)
    
    def test_multiple_multiplicative_with_catalog(self):
        """Test multiple multiplicative appearances."""
        nadh = Mock()
        nadh.name = "NADH"
        
        rate_functions = [
            "k * NADH * Substrate1",  # Multiplicative
            "k2 * NADH * Substrate2",  # Multiplicative
        ]
        
        score = self.classifier.analyze_dynamics(nadh, rate_functions)
        
        # Multiple multiplicative = strong evidence
        self.assertEqual(score, 1.0)


if __name__ == '__main__':
    unittest.main()
