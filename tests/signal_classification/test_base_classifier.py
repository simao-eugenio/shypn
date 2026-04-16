#!/usr/bin/env python3
"""Tests for Base Signal Classifier.

Author: Simão Eugénio
Date: December 31, 2025
"""

import unittest
from unittest.mock import Mock, MagicMock

import sys
sys.path.insert(0, 'src')

from shypn.analysis.signal_classification.base_classifier import BaseSignalClassifier


class ConcreteClassifier(BaseSignalClassifier):
    """Concrete implementation for testing abstract base class."""
    
    def get_signal_type(self) -> str:
        return 'TEST'
    
    def get_lexical_patterns(self):
        return [r'\btest\b']
    
    def get_biochemical_indicators(self):
        return {'TEST'}
    
    def analyze_topology(self, place) -> float:
        return 0.5
    
    def analyze_dynamics(self, place, rate_functions) -> float:
        return 0.5


class TestBaseSignalClassifier(unittest.TestCase):
    """Test cases for BaseSignalClassifier."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.model = Mock()
        self.model.places = []
        self.model.transitions = []
        self.model.arcs = []
        
        self.classifier = ConcreteClassifier(self.model, confidence_threshold=0.5)
    
    def test_initialization(self):
        """Test classifier initialization."""
        self.assertEqual(self.classifier.model, self.model)
        self.assertEqual(self.classifier.confidence_threshold, 0.5)
    
    def test_lexical_analysis_match(self):
        """Test lexical analysis with matching pattern."""
        place = Mock()
        place.name = "test_place"
        
        score = self.classifier._analyze_lexical(place)
        self.assertEqual(score, 1.0)
    
    def test_lexical_analysis_no_match(self):
        """Test lexical analysis with no match."""
        place = Mock()
        place.name = "other_place"
        
        score = self.classifier._analyze_lexical(place)
        self.assertEqual(score, 0.0)
    
    def test_biochemical_analysis_match(self):
        """Test biochemical analysis with matching compound."""
        place = Mock()
        place.name = "TEST_compound"
        
        score = self.classifier._analyze_biochemical(place)
        self.assertEqual(score, 1.0)
    
    def test_biochemical_analysis_no_match(self):
        """Test biochemical analysis with no match."""
        place = Mock()
        place.name = "other_compound"
        
        score = self.classifier._analyze_biochemical(place)
        self.assertEqual(score, 0.0)
    
    def test_classify_above_threshold(self):
        """Test classification with confidence above threshold."""
        place = Mock()
        place.name = "test_TEST"
        
        is_match, confidence, breakdown = self.classifier.classify(place)
        
        self.assertTrue(is_match)
        self.assertGreater(confidence, 0.5)
        self.assertIn('lexical', breakdown)
        self.assertIn('biochemical', breakdown)
        self.assertIn('topology', breakdown)
        self.assertIn('dynamics', breakdown)
    
    def test_classify_below_threshold(self):
        """Test classification with confidence below threshold."""
        place = Mock()
        place.name = "unrelated"
        
        is_match, confidence, breakdown = self.classifier.classify(place)
        
        self.assertFalse(is_match)
        self.assertLess(confidence, 0.5)
    
    def test_extract_place_references(self):
        """Test extraction of place names from formula."""
        # Create mock places
        atp = Mock()
        atp.name = "ATP"
        glucose = Mock()
        glucose.name = "Glucose"
        
        self.model.places = [atp, glucose]
        
        formula = "2.0 * ATP * Glucose / (10 + ATP)"
        references = self.classifier._extract_place_references(formula)
        
        self.assertEqual(references, {'ATP', 'Glucose'})
    
    def test_extract_place_references_filters_math(self):
        """Test that math keywords are filtered out."""
        atp = Mock()
        atp.name = "ATP"
        
        self.model.places = [atp]
        
        formula = "min(ATP, 10) * exp(-time)"
        references = self.classifier._extract_place_references(formula)
        
        self.assertEqual(references, {'ATP'})
        self.assertNotIn('min', references)
        self.assertNotIn('exp', references)
        self.assertNotIn('time', references)


if __name__ == '__main__':
    unittest.main()
