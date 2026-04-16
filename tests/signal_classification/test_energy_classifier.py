#!/usr/bin/env python3
"""Tests for Energy Signal Classifier.

Author: Simão Eugénio
Date: December 31, 2025
"""

import unittest
from unittest.mock import Mock

import sys
sys.path.insert(0, 'src')

from shypn.analysis.signal_classification.energy_classifier import EnergySignalClassifier


class TestEnergySignalClassifier(unittest.TestCase):
    """Test cases for EnergySignalClassifier."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.model = Mock()
        self.model.places = []
        self.model.transitions = []
        self.model.arcs = []
        
        self.classifier = EnergySignalClassifier(self.model, confidence_threshold=0.5)
    
    def test_signal_type(self):
        """Test signal type identifier."""
        self.assertEqual(self.classifier.get_signal_type(), 'ENERGY')
    
    def test_atp_detection(self):
        """Test detection of ATP as energy signal."""
        place = Mock()
        place.name = "ATP"
        
        is_match, confidence, _ = self.classifier.classify(place)
        
        self.assertTrue(is_match)
        self.assertGreater(confidence, 0.5)
    
    def test_nadh_detection(self):
        """Test detection of NADH as energy signal."""
        place = Mock()
        place.name = "NADH"
        
        is_match, confidence, _ = self.classifier.classify(place)
        
        self.assertTrue(is_match)
        self.assertGreater(confidence, 0.5)
    
    def test_topology_hub_detection(self):
        """Test detection of highly connected energy hubs."""
        atp = Mock()
        atp.name = "ATP"
        
        # Create 6 consuming transitions
        for i in range(6):
            arc = Mock()
            arc.source = atp
            arc.target = Mock(name=f"T{i}")
            self.model.arcs.append(arc)
        
        # Create 2 producing transitions
        for i in range(2):
            arc = Mock()
            arc.source = Mock(name=f"P{i}")
            arc.target = atp
            self.model.arcs.append(arc)
        
        score = self.classifier.analyze_topology(atp)
        
        self.assertGreater(score, 0.5)
    
    def test_multiplicative_dynamics(self):
        """Test detection of multiplicative energy factors."""
        atp = Mock()
        atp.name = "ATP"
        
        rate_functions = [
            "2.0 * ATP * Glucose",
            "k * ATP * substrate",
        ]
        
        score = self.classifier.analyze_dynamics(atp, rate_functions)
        
        self.assertGreater(score, 0.7)
    
    def test_saturation_kinetics(self):
        """Test detection of saturation kinetics."""
        nadh = Mock()
        nadh.name = "NADH"
        
        rate_functions = [
            "Vmax * NADH / (Km + NADH)",
        ]
        
        score = self.classifier.analyze_dynamics(nadh, rate_functions)
        
        self.assertGreater(score, 0.5)
    
    def test_non_energy_metabolite(self):
        """Test that non-energy metabolites are not classified."""
        glucose = Mock()
        glucose.name = "Glucose"
        
        is_match, confidence, _ = self.classifier.classify(glucose)
        
        self.assertLess(confidence, 0.5)


if __name__ == '__main__':
    unittest.main()
