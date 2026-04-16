#!/usr/bin/env python3
"""Tests for ViabilityAnalyzer.

Phase 2.2 Quality Improvements - Extracted analyzer testing.

Tests the multi-level viability analysis pipeline independent of UI.
"""
import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import from Phase 2.2 extraction
from shypn.ui.panels.viability.analyzers import ViabilityAnalyzer, AnalysisResult


class TestViabilityAnalyzer(unittest.TestCase):
    """Test suite for ViabilityAnalyzer."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock model
        self.mock_model = Mock()
        self.mock_model.transitions = []
        self.mock_model.places = []
        
        # Create mock KB
        self.mock_kb = Mock()
        
        # Create mock simulation
        self.mock_simulation = Mock()
        
        # Create analyzer
        self.analyzer = ViabilityAnalyzer(
            model=self.mock_model,
            kb=self.mock_kb,
            simulation=self.mock_simulation
        )
    
    def test_initialization(self):
        """Test analyzer initializes correctly."""
        self.assertIsNotNone(self.analyzer)
        self.assertEqual(self.analyzer.model, self.mock_model)
        self.assertEqual(self.analyzer.kb, self.mock_kb)
        self.assertEqual(self.analyzer.simulation, self.mock_simulation)
        
        # Check analyzers initialized
        self.assertIsNotNone(self.analyzer.locality_analyzer)
        self.assertIsNotNone(self.analyzer.dependency_analyzer)
        self.assertIsNotNone(self.analyzer.boundary_analyzer)
        self.assertIsNotNone(self.analyzer.conservation_analyzer)
    
    def test_analyze_missing_transition(self):
        """Test analysis with missing transition returns error result."""
        # Create transition that doesn't exist in model
        mock_transition = Mock()
        mock_transition.transition_id = "T1"
        
        result = self.analyzer.analyze(mock_transition)
        
        self.assertIsInstance(result, AnalysisResult)
        self.assertEqual(result.transition, mock_transition)
        self.assertEqual(len(result.issues), 0)
        self.assertTrue(len(result.errors) > 0)
        self.assertIn("not found", result.errors[0])
    
    def test_analyze_quick_mode(self):
        """Test quick analysis mode (locality only)."""
        # Create mock transition
        mock_transition = Mock()
        mock_transition.transition_id = "T1"
        
        mock_transition_obj = Mock()
        mock_transition_obj.id = "T1"
        self.mock_model.transitions = [mock_transition_obj]
        
        # Patch LocalityDetector where it's imported
        with patch('shypn.diagnostic.LocalityDetector') as mock_detector_cls:
            mock_detector = Mock()
            mock_detector.get_locality_for_transition.return_value = Mock()
            mock_detector_cls.return_value = mock_detector
            
            # Mock locality analyzer to return empty issues
            self.analyzer.locality_analyzer.analyze = Mock(return_value=[])
            
            result = self.analyzer.analyze(mock_transition, mode='quick')
            
            self.assertIsInstance(result, AnalysisResult)
            self.assertEqual(len(result.errors), 0)
            # Should only call locality analyzer in quick mode
            self.analyzer.locality_analyzer.analyze.assert_called_once()
    
    def test_analyze_standard_mode(self):
        """Test standard analysis mode (locality + boundary + conservation)."""
        # Create mock transition
        mock_transition = Mock()
        mock_transition.transition_id = "T1"
        
        mock_transition_obj = Mock()
        mock_transition_obj.id = "T1"
        self.mock_model.transitions = [mock_transition_obj]
        
        # Patch LocalityDetector
        with patch('shypn.diagnostic.LocalityDetector') as mock_detector_cls:
            mock_detector = Mock()
            mock_detector.get_locality_for_transition.return_value = Mock()
            mock_detector_cls.return_value = mock_detector
            
            # Mock analyzers
            self.analyzer.locality_analyzer.analyze = Mock(return_value=[])
            self.analyzer.boundary_analyzer.analyze = Mock(return_value=[])
            self.analyzer.conservation_analyzer.analyze = Mock(return_value=[])
            
            result = self.analyzer.analyze(mock_transition, mode='standard')
            
            self.assertIsInstance(result, AnalysisResult)
            # Should call locality, boundary, and conservation analyzers
            self.analyzer.locality_analyzer.analyze.assert_called_once()
            self.analyzer.boundary_analyzer.analyze.assert_called_once()
            self.analyzer.conservation_analyzer.analyze.assert_called_once()
    
    def test_analyze_deep_mode(self):
        """Test deep analysis mode (all analyzers)."""
        # Create mock transition
        mock_transition = Mock()
        mock_transition.transition_id = "T1"
        
        mock_transition_obj = Mock()
        mock_transition_obj.id = "T1"
        self.mock_model.transitions = [mock_transition_obj]
        
        # Patch LocalityDetector
        with patch('shypn.diagnostic.LocalityDetector') as mock_detector_cls:
            mock_detector = Mock()
            mock_detector.get_locality_for_transition.return_value = Mock()
            mock_detector_cls.return_value = mock_detector
            
            # Mock analyzers
            self.analyzer.locality_analyzer.analyze = Mock(return_value=[])
            self.analyzer.dependency_analyzer.analyze = Mock(return_value=[])
            self.analyzer.boundary_analyzer.analyze = Mock(return_value=[])
            self.analyzer.conservation_analyzer.analyze = Mock(return_value=[])
            
            result = self.analyzer.analyze(mock_transition, mode='deep')
            
            self.assertIsInstance(result, AnalysisResult)
            # Should call all analyzers in deep mode
            self.analyzer.locality_analyzer.analyze.assert_called_once()
            self.analyzer.dependency_analyzer.analyze.assert_called_once()
            self.analyzer.boundary_analyzer.analyze.assert_called_once()
            self.analyzer.conservation_analyzer.analyze.assert_called_once()
    
    def test_analyze_with_suggestions(self):
        """Test analysis with suggestion generation."""
        # Create mock transition
        mock_transition = Mock()
        mock_transition.transition_id = "T1"
        
        mock_transition_obj = Mock()
        mock_transition_obj.id = "T1"
        self.mock_model.transitions = [mock_transition_obj]
        
        # Create mock issue
        mock_issue = Mock()
        mock_issue.message = "locality issue"
        mock_issue.category = "structural"
        
        # Patch LocalityDetector
        with patch('shypn.diagnostic.LocalityDetector') as mock_detector_cls:
            mock_detector = Mock()
            mock_detector.get_locality_for_transition.return_value = Mock()
            mock_detector_cls.return_value = mock_detector
            
            # Mock analyzers to return issues
            self.analyzer.locality_analyzer.analyze = Mock(return_value=[mock_issue])
            self.analyzer.locality_analyzer.generate_suggestions = Mock(return_value=[Mock()])
            
            result = self.analyzer.analyze(mock_transition, mode='quick', generate_suggestions=True)
            
            self.assertIsInstance(result, AnalysisResult)
            self.assertEqual(len(result.issues), 1)
            self.assertTrue(len(result.suggestions) > 0)
            self.analyzer.locality_analyzer.generate_suggestions.assert_called_once()
    
    def test_batch_analyze(self):
        """Test batch analysis of multiple transitions."""
        # Create mock transitions
        mock_transitions = []
        for i in range(3):
            mock_t = Mock()
            mock_t.transition_id = f"T{i}"
            mock_transitions.append(mock_t)
            
            mock_t_obj = Mock()
            mock_t_obj.id = f"T{i}"
            self.mock_model.transitions.append(mock_t_obj)
        
        # Patch LocalityDetector
        with patch('shypn.diagnostic.LocalityDetector') as mock_detector_cls:
            mock_detector = Mock()
            mock_detector.get_locality_for_transition.return_value = Mock()
            mock_detector_cls.return_value = mock_detector
            
            # Mock analyzers
            self.analyzer.locality_analyzer.analyze = Mock(return_value=[])
            
            results = self.analyzer.batch_analyze(mock_transitions, mode='quick')
            
            self.assertEqual(len(results), 3)
            for result in results:
                self.assertIsInstance(result, AnalysisResult)
    
    def test_batch_analyze_with_error(self):
        """Test batch analysis handles errors gracefully."""
        # Create mock transitions
        mock_transitions = [Mock()]
        mock_transitions[0].transition_id = "T1"
        
        # Don't add transition to model to force error
        
        results = self.analyzer.batch_analyze(mock_transitions, mode='quick')
        
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], AnalysisResult)
        # Should have error recorded
        self.assertTrue(len(results[0].errors) > 0)


class TestAnalysisResult(unittest.TestCase):
    """Test suite for AnalysisResult dataclass."""
    
    def test_creation(self):
        """Test AnalysisResult creation."""
        mock_transition = Mock()
        mock_issues = [Mock(), Mock()]
        
        result = AnalysisResult(
            transition=mock_transition,
            issues=mock_issues
        )
        
        self.assertEqual(result.transition, mock_transition)
        self.assertEqual(result.issues, mock_issues)
        self.assertIsNotNone(result.suggestions)
        self.assertIsNotNone(result.context)
        self.assertIsNotNone(result.errors)
        self.assertEqual(len(result.suggestions), 0)
        self.assertEqual(len(result.errors), 0)
    
    def test_creation_with_suggestions(self):
        """Test AnalysisResult with suggestions."""
        mock_suggestions = [Mock(), Mock(), Mock()]
        
        result = AnalysisResult(
            transition=Mock(),
            issues=[],
            suggestions=mock_suggestions
        )
        
        self.assertEqual(result.suggestions, mock_suggestions)
        self.assertEqual(len(result.suggestions), 3)


if __name__ == '__main__':
    unittest.main()
