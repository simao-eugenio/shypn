#!/usr/bin/env python3
"""Tests for Viability Panel Experiment Automation.

Tests the complete workflow from parameter sweep configuration
to batch execution and results export.

Author: Simão Eugénio
Date: December 7, 2025
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.ui.panels.viability.experiment_manager import ExperimentManager, ExperimentSnapshot
from shypn.ui.panels.viability.automation.batch_executor import BatchExecutor


class TestExperimentManager(unittest.TestCase):
    """Test ExperimentManager snapshot management."""
    
    def setUp(self):
        self.manager = ExperimentManager()
    
    def test_add_snapshot(self):
        """Test adding experiment snapshots."""
        snapshot = self.manager.add_snapshot("Test Experiment")
        
        self.assertEqual(len(self.manager.snapshots), 1)
        self.assertEqual(snapshot.name, "Test Experiment")
        self.assertEqual(self.manager.active_index, 0)
    
    def test_switch_snapshot(self):
        """Test switching between snapshots."""
        self.manager.add_snapshot("Exp1")
        self.manager.add_snapshot("Exp2")
        
        self.assertEqual(self.manager.active_index, 1)
        
        snapshot = self.manager.switch_to(0)
        self.assertEqual(snapshot.name, "Exp1")
        self.assertEqual(self.manager.active_index, 0)
    
    def test_generate_sweep_snapshots(self):
        """Test parameter sweep generation."""
        # Create base snapshot
        base = self.manager.add_snapshot("Baseline")
        base.transition_rates['T1'] = 1.0
        base.place_markings['P1'] = 10
        
        # Generate sweep
        values = [0.5, 1.0, 2.0]
        count = self.manager.generate_sweep_snapshots(
            parameter_type='transitions',
            parameter_name='T1',
            values=values,
            base_snapshot=base
        )
        
        self.assertEqual(count, 3)
        self.assertEqual(len(self.manager.snapshots), 4)  # Base + 3 sweep
        
        # Verify sweep values
        self.assertEqual(self.manager.snapshots[1].transition_rates['T1'], 0.5)
        self.assertEqual(self.manager.snapshots[2].transition_rates['T1'], 1.0)
        self.assertEqual(self.manager.snapshots[3].transition_rates['T1'], 2.0)
        
        # Verify base values preserved
        self.assertEqual(self.manager.snapshots[1].place_markings['P1'], 10)
    
    def test_copy_snapshot(self):
        """Test snapshot copying."""
        original = self.manager.add_snapshot("Original")
        original.place_markings['P1'] = 5
        
        copy = self.manager.copy_snapshot(0)
        
        self.assertEqual(len(self.manager.snapshots), 2)
        self.assertEqual(copy.name, "Original (Copy)")
        self.assertEqual(copy.place_markings['P1'], 5)
        
        # Verify independence
        copy.place_markings['P1'] = 10
        self.assertEqual(original.place_markings['P1'], 5)
    
    def test_remove_snapshot(self):
        """Test snapshot removal."""
        self.manager.add_snapshot("Exp1")
        self.manager.add_snapshot("Exp2")
        
        removed = self.manager.remove_snapshot(0)
        
        self.assertTrue(removed)
        self.assertEqual(len(self.manager.snapshots), 1)
        self.assertEqual(self.manager.snapshots[0].name, "Exp2")


class TestBatchExecutor(unittest.TestCase):
    """Test BatchExecutor simulation execution."""
    
    def setUp(self):
        self.manager = ExperimentManager()
        self.model_canvas = Mock()
        self.parent_panel = Mock()
        self.parent_panel.selected_localities = {}
        self.executor = BatchExecutor(self.manager, self.model_canvas, self.parent_panel)
    
    def test_executor_initialization(self):
        """Test executor initializes correctly."""
        self.assertFalse(self.executor.is_running)
        self.assertFalse(self.executor.is_cancelled)
        self.assertEqual(len(self.executor.results), 0)
    
    def test_get_model(self):
        """Test model retrieval from parent panel."""
        # Mock the parent panel's _get_current_model method
        mock_model = Mock()
        mock_model.places = [Mock(id='P1')]
        mock_model.transitions = [Mock(id='T1')]
        mock_model.arcs = []
        
        self.executor.parent_panel._get_current_model = Mock(return_value=mock_model)
        
        model = self.executor._get_model()
        
        self.assertEqual(model, mock_model)
        self.executor.parent_panel._get_current_model.assert_called_once()
    
    def test_apply_snapshot_to_model(self):
        """Test applying snapshot parameters to model."""
        # Create snapshot
        snapshot = ExperimentSnapshot("Test")
        snapshot.place_markings['P1'] = 5
        snapshot.transition_rates['T1'] = 2.0
        snapshot.arc_weights['A1'] = 3
        
        # Create mock model
        mock_place = Mock()
        mock_place.id = 'P1'
        
        mock_transition = Mock()
        mock_transition.id = 'T1'
        
        mock_arc = Mock()
        mock_arc.id = 'A1'
        
        mock_model = Mock()
        mock_model.places = [mock_place]
        mock_model.transitions = [mock_transition]
        mock_model.arcs = [mock_arc]
        
        # Create subnet containing these elements
        subnet = {
            'places': [mock_place],
            'transitions': [mock_transition],
            'arcs': [mock_arc]
        }
        
        # Apply snapshot with subnet
        self.executor._apply_snapshot_to_model(snapshot, mock_model, subnet)
        
        # Verify parameters applied
        self.assertEqual(mock_place.tokens, 5)
        self.assertEqual(mock_place.marking, 5)
        self.assertEqual(mock_transition.rate, 2.0)
        self.assertEqual(mock_arc.weight, 3)
    
    @patch('shypn.engine.simulation.replicate_runner.ReplicateRunner')
    def test_run_single_experiment_success(self, mock_runner_class):
        """Test successful single experiment execution."""
        # Setup mocks
        snapshot = self.manager.add_snapshot("Test")
        snapshot.place_markings['P1'] = 10
        
        mock_place = Mock(id='P1')
        mock_transition = Mock(id='T1')
        
        # Mock DocumentModel (what to_document_model returns)
        mock_document_model = Mock()
        mock_document_model.places = [mock_place]
        mock_document_model.transitions = [mock_transition]
        mock_document_model.arcs = []
        
        # Mock ModelCanvasManager (what _get_model returns)
        mock_canvas_manager = Mock()
        mock_canvas_manager.places = [mock_place]
        mock_canvas_manager.transitions = [mock_transition]
        mock_canvas_manager.arcs = []
        mock_canvas_manager.to_document_model = Mock(return_value=mock_document_model)
        
        self.executor._get_model = Mock(return_value=mock_canvas_manager)
        
        # Mock ReplicateRunner
        mock_runner = Mock()
        mock_runner.run_replicates.return_value = [
            {
                'replicate_id': 0,
                'seed': 42,
                'time_points': [0.0, 1.0],
                'place_data': {'P1': [10, 12]},
                'final_marking': {'P1': 12}
            }
        ]
        mock_runner.compute_statistics.return_value = {
            'n_replicates': 1,
            'time_points': [0.0, 1.0],
            'species_statistics': {}
        }
        mock_runner_class.return_value = mock_runner
        
        # Run experiment
        result = self.executor._run_single_experiment(
            name="Test",
            snapshot_index=0,
            replicates=1,
            duration=10.0
        )
        
        # Verify result
        self.assertEqual(result['name'], "Test")
        self.assertEqual(result['n_replicates'], 1)  # Check replicate count instead
        self.assertIn('statistics', result)
        self.assertGreater(result['duration'], 0)
    
    def test_clear_results(self):
        """Test clearing results."""
        self.executor.results['test1'] = {'data': 'value1'}
        self.executor.results['test2'] = {'data': 'value2'}
        
        self.assertEqual(len(self.executor.results), 2)
        
        self.executor.clear_results()
        
        self.assertEqual(len(self.executor.results), 0)
    
    def test_extract_subnet_with_selected_localities(self):
        """Test subnet extraction from selected localities."""
        # Create mock model
        mock_place1 = Mock()
        mock_place1.id = 'P1'
        
        mock_transition1 = Mock()
        mock_transition1.id = 'T1'
        
        mock_arc1 = Mock()
        mock_arc1.id = 'A1'
        
        mock_model = Mock()
        mock_model.places = [mock_place1]
        mock_model.transitions = [mock_transition1]
        mock_model.arcs = [mock_arc1]
        
        # Create mock locality
        mock_locality = Mock()
        mock_locality.transition_id = 'T1'
        mock_locality.transition = mock_transition1
        mock_locality.input_places = [mock_place1]
        mock_locality.output_places = []
        mock_locality.input_arcs = [mock_arc1]
        mock_locality.output_arcs = []
        
        # Set parent panel with selected localities
        self.executor.parent_panel.selected_localities = {
            'T1': {
                'locality': mock_locality
            }
        }
        
        # Extract subnet
        subnet = self.executor._extract_subnet(mock_model)
        
        # Verify subnet contains expected elements
        self.assertIsNotNone(subnet)
        self.assertEqual(len(subnet['places']), 1)
        self.assertEqual(len(subnet['transitions']), 1)
        self.assertEqual(len(subnet['arcs']), 1)
        self.assertEqual(subnet['places'][0].id, 'P1')
        self.assertEqual(subnet['transitions'][0].id, 'T1')
        self.assertEqual(subnet['arcs'][0].id, 'A1')
    
    def test_extract_subnet_no_selected_localities(self):
        """Test subnet extraction when no localities selected returns None."""
        mock_model = Mock()
        mock_model.places = [Mock(id='P1')]
        mock_model.transitions = [Mock(id='T1')]
        mock_model.arcs = [Mock(id='A1')]
        
        # Clear selected localities
        self.executor.parent_panel.selected_localities = {}
        
        # Extract subnet - should return full model when no selection
        subnet = self.executor._extract_subnet(mock_model)
        
        # Should return full model as subnet
        self.assertIsNotNone(subnet)
        self.assertEqual(len(subnet['places']), 1)
        self.assertEqual(len(subnet['transitions']), 1)


class TestExperimentSnapshot(unittest.TestCase):
    """Test ExperimentSnapshot data capture."""
    
    def test_snapshot_creation(self):
        """Test creating snapshot with name."""
        snapshot = ExperimentSnapshot("My Experiment")
        
        self.assertEqual(snapshot.name, "My Experiment")
        self.assertEqual(len(snapshot.place_markings), 0)
        self.assertEqual(len(snapshot.transition_rates), 0)
        self.assertEqual(len(snapshot.arc_weights), 0)
    
    def test_to_dict_from_dict(self):
        """Test serialization round-trip."""
        snapshot = ExperimentSnapshot("Test")
        snapshot.place_markings['P1'] = 10
        snapshot.transition_rates['T1'] = 2.0
        snapshot.notes = "Test experiment"
        
        # Convert to dict
        data = snapshot.to_dict()
        
        self.assertEqual(data['name'], "Test")
        self.assertEqual(data['place_markings']['P1'], 10)
        self.assertEqual(data['transition_rates']['T1'], 2.0)
        
        # Reconstruct from dict
        restored = ExperimentSnapshot.from_dict(data)
        
        self.assertEqual(restored.name, "Test")
        self.assertEqual(restored.place_markings['P1'], 10)
        self.assertEqual(restored.transition_rates['T1'], 2.0)
        self.assertEqual(restored.notes, "Test experiment")


if __name__ == '__main__':
    unittest.main()
