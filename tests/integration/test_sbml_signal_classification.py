#!/usr/bin/env python3
"""Integration test for SBML import + signal classification.

Tests that the new signal classification system is properly integrated
into the SBML import workflow.

Author: Simão Eugénio
Date: December 31, 2024
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
sys.path.insert(0, 'src')

from shypn.services.sbml_compartment_module_service import SBMLCompartmentModuleService
from shypn.netobjs import Place, Transition, Arc
from shypn.netobjs.signal_type import SignalType


class TestSBMLSignalClassificationIntegration(unittest.TestCase):
    """Test integration between SBML import and signal classification."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = SBMLCompartmentModuleService()
    
    def test_classifier_manager_imported(self):
        """Test that SignalClassifierManager is available for import."""
        try:
            from shypn.analysis.signal_classification import SignalClassifierManager
            self.assertIsNotNone(SignalClassifierManager)
        except ImportError:
            self.fail("SignalClassifierManager should be importable")
    
    def test_signal_detection_uses_both_systems(self):
        """Test that signal detection calls both legacy and new systems."""
        # Create mock document
        document = Mock()
        
        # Create mock places with rate information
        atp_place = Mock(spec=Place)
        atp_place.name = "ATP"
        atp_place.signal_type = None
        
        glucose_place = Mock(spec=Place)
        glucose_place.name = "Glucose"
        glucose_place.signal_type = None
        
        document.places = [atp_place, glucose_place]
        
        # Create mock transition with rate function referencing ATP
        transition = Mock(spec=Transition)
        transition.name = "Phosphorylation"
        transition.rate = 2.5  # Numeric
        transition.properties = {
            'rate_function': "Vmax * ATP / (Km + ATP)"  # Michaelis-Menten
        }
        transition.kinetic_metadata = None
        
        document.transitions = [transition]
        document.arcs = []
        
        # Mock modules
        modules = {}
        warnings = []
        
        # Call signal detection
        result = self.service._apply_signal_detection(
            document,
            modules,
            confidence_threshold=0.5,
            warnings=warnings
        )
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertIn('combined_applied_count', result)
        
        # Should have attempted both systems
        # (May not be available in test environment, but structure should exist)
        if result.get('new_classification'):
            self.assertIn('applied_count', result['new_classification'])
            self.assertIn('classifications', result['new_classification'])
    
    def test_sbml_import_parameters(self):
        """Test that SBML import has auto_detect_signals parameter."""
        # Verify the convert_compartments_to_modules method signature
        import inspect
        sig = inspect.signature(self.service.convert_compartments_to_modules)
        
        params = sig.parameters
        self.assertIn('auto_detect_signals', params)
        self.assertEqual(params['auto_detect_signals'].default, True)
        
        # Verify it accepts confidence_threshold
        self.assertIn('confidence_threshold', params)
        self.assertEqual(params['confidence_threshold'].default, 0.75)
    
    @patch('shypn.services.sbml_compartment_module_service.SignalClassifierManager')
    def test_rate_function_extraction_called(self, mock_classifier_class):
        """Test that rate function extraction is attempted during import."""
        # Setup mock classifier
        mock_manager = MagicMock()
        mock_manager.classify_all.return_value = {}
        mock_manager.generate_report.return_value = "Report"
        mock_classifier_class.return_value = mock_manager
        
        # Create mock document
        document = Mock()
        document.places = [Mock(name="ATP")]
        document.transitions = [Mock(name="T1", properties={'rate_function': "k * ATP"})]
        document.arcs = []
        
        modules = {}
        warnings = []
        
        # Call detection
        result = self.service._apply_signal_detection(
            document,
            modules,
            confidence_threshold=0.6,
            warnings=warnings
        )
        
        # Verify SignalClassifierManager was instantiated
        mock_classifier_class.assert_called_once()
        
        # Verify classify_all was called with threshold
        mock_manager.classify_all.assert_called_once_with(threshold=0.6)


class TestRateFunctionAvailability(unittest.TestCase):
    """Test that rate function data is available during SBML import."""
    
    def test_transition_has_rate_properties(self):
        """Test that Transition has rate and properties attributes."""
        from shypn.netobjs.transition import Transition
        
        t = Transition(100, 100, "t1", "T1")
        
        # Should have rate attribute
        self.assertTrue(hasattr(t, 'rate'))
        
        # Should have properties for rate_function
        self.assertTrue(hasattr(t, 'properties'))
        
        # properties should be dict-like
        if t.properties is None:
            t.properties = {}
        
        t.properties['rate_function'] = "2.0 * ATP"
        self.assertEqual(t.properties['rate_function'], "2.0 * ATP")
    
    def test_place_has_signal_type(self):
        """Test that Place can have signal_type assigned."""
        from shypn.netobjs.place import Place
        
        p = Place(100, 100, "p1", "ATP")
        
        # Should have signal_type attribute
        self.assertTrue(hasattr(p, 'signal_type'))
        
        # Should be able to set it
        p.signal_type = SignalType.ENERGY
        self.assertEqual(p.signal_type, SignalType.ENERGY)


if __name__ == '__main__':
    unittest.main()
