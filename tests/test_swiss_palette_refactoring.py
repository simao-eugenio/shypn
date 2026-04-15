#!/usr/bin/env python3
"""Integration test for Swiss Palette batch save refactoring.

Verifies that the refactored _save_batch_results method produces
the same output structure as the original implementation.

Author: Simão Eugénio
Date: February 15, 2026
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import json
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.helpers.batch_results_saver import save_swiss_palette_batch


class TestSwissPaletteRefactoring(unittest.TestCase):
    """Test Swiss Palette batch save refactoring produces expected output."""
    
    def setUp(self):
        """Create temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)
    
    def test_refactored_output_structure(self):
        """Test that refactored save produces expected folder structure."""
        # Mock model
        class MockModel:
            filepath = None
            
            def to_dict(self):
                return {
                    'places': [{'id': 'P1', 'initial_marking': 10}],
                    'transitions': [{'id': 'T1', 'rate': 1.0}],
                    'arcs': [],
                    'formalism': 'Signal_Hierarchical_Petri_Net',
                    'metadata': {}
                }
        
        # Mock settings
        class MockSettings:
            duration = 1000.0
            time_units = 'SECONDS'
            dt_auto = True
            use_tau_leaping = True
            tau_epsilon = 0.03
        
        # Mock batch results
        results = []
        for i in range(3):
            results.append({
                'replicate_id': i,
                'time_points': [0.0, 1.0, 2.0],
                'place_data': {
                    'P1': [(0.0, 10 + i), (1.0, 15 + i), (2.0, 20 + i)]
                },
                'transition_data': {}
            })
        
        model = MockModel()
        settings = MockSettings()
        
        # Call refactored save function
        batch_folder = save_swiss_palette_batch(
            results=results,
            recorded_objects={'P1'},
            n_replicates=3,
            simulation_settings=settings,
            model=model,
            project_folder=self.test_dir
        )
        
        batch_path = Path(batch_folder)
        
        # Verify expected output structure
        self.assertTrue(batch_path.exists(), "Batch folder should exist")
        self.assertTrue(batch_path.is_dir(), "Batch folder should be a directory")
        
        # Verify required files exist
        self.assertTrue((batch_path / 'config.json').exists(), "config.json should exist")
        self.assertTrue((batch_path / 'summary.json').exists(), "summary.json should exist")
        
        # Verify replicate CSVs exist
        for i in range(3):
            csv_file = batch_path / f'run_{i+1:03d}.csv'
            self.assertTrue(csv_file.exists(), f"run_{i+1:03d}.csv should exist")
        
        # Verify config.json structure
        with open(batch_path / 'config.json', 'r') as f:
            config = json.load(f)
        
        self.assertIn('timestamp', config)
        self.assertEqual(config['n_replicates'], 3)
        self.assertEqual(config['recorded_objects'], ['P1'])
        self.assertIn('settings', config)
        self.assertEqual(config['settings']['duration'], 1000.0)
        self.assertTrue(config['settings']['use_tau_leaping'])
        
        # Verify summary.json structure
        with open(batch_path / 'summary.json', 'r') as f:
            summary = json.load(f)
        
        self.assertEqual(summary['successful_replicates'], 3)
        self.assertEqual(summary['total_replicates'], 3)
        self.assertIn('statistics', summary)
        self.assertIn('P1', summary['statistics'])
        
        # Verify P1 statistics
        p1_stats = summary['statistics']['P1']
        self.assertIn('mean', p1_stats)
        self.assertIn('std', p1_stats)
        self.assertIn('min', p1_stats)
        self.assertIn('max', p1_stats)
        self.assertIn('final_mean', p1_stats)
        self.assertIn('final_std', p1_stats)
        
        # Each trajectory should be length 3 (3 time points)
        self.assertEqual(len(p1_stats['mean']), 3)
    
    def test_csv_format_compatibility(self):
        """Test that CSV format is compatible with existing analysis tools."""
        # Mock model
        class MockModel:
            filepath = None
            
            def to_dict(self):
                return {
                    'places': [{'id': 'P1', 'initial_marking': 50}],
                    'transitions': [],
                    'arcs': [],
                    'formalism': 'Signal_Hierarchical_Petri_Net',
                    'metadata': {}
                }
        
        class MockSettings:
            duration = 100.0
            time_units = 'SECONDS'
            dt_auto = True
            use_tau_leaping = True
            tau_epsilon = 0.03
        
        results = [{
            'replicate_id': 0,
            'time_points': [0.0, 10.0, 20.0],
            'place_data': {
                'P1': [(0.0, 50), (10.0, 45), (20.0, 40)]
            },
            'transition_data': {}
        }]
        
        batch_folder = save_swiss_palette_batch(
            results=results,
            recorded_objects={'P1'},
            n_replicates=1,
            simulation_settings=MockSettings(),
            model=MockModel(),
            project_folder=self.test_dir
        )
        
        csv_file = Path(batch_folder) / 'run_001.csv'
        
        # Read CSV and verify format
        with open(csv_file, 'r') as f:
            lines = f.readlines()
        
        # Should have metadata header (starts with #)
        has_metadata = any(line.startswith('#') for line in lines)
        self.assertTrue(has_metadata, "CSV should have metadata header")
        
        # Find data section (first non-comment line)
        data_start = next(i for i, line in enumerate(lines) if not line.startswith('#'))
        
        # Header row should contain 'time' and 'P1'
        header_line = lines[data_start].strip()
        self.assertIn('time', header_line)
        self.assertIn('P1', header_line)
        
        # Should have 3 data rows (excluding header)
        data_lines = [line for line in lines[data_start + 1:] if line.strip()]
        self.assertEqual(len(data_lines), 3)
        
        # First data row should be "0.0,50"
        first_data = data_lines[0].strip().split(',')
        self.assertEqual(float(first_data[0]), 0.0)
        self.assertEqual(float(first_data[1]), 50)
    
    def test_backward_compatibility_with_existing_batches(self):
        """Test that new batches are compatible with existing analysis scripts."""
        # This test verifies the structure matches what existing scripts expect
        
        class MockModel:
            filepath = None
            def to_dict(self):
                return {'places': [], 'transitions': [], 'arcs': [], 'formalism': 'Signal_Hierarchical_Petri_Net', 'metadata': {}}
        
        class MockSettings:
            duration = 1000.0
            time_units = 'SECONDS'
            dt_auto = True
            use_tau_leaping = True
            tau_epsilon = 0.03
        
        results = [{
            'replicate_id': 0,
            'time_points': [0.0, 1.0],
            'place_data': {'P1': [(0.0, 10), (1.0, 20)]},
            'transition_data': {}
        }]
        
        batch_folder = save_swiss_palette_batch(
            results=results,
            recorded_objects={'P1'},
            n_replicates=1,
            simulation_settings=MockSettings(),
            model=MockModel(),
            project_folder=self.test_dir
        )
        
        # Verify the saved batch can be loaded by a hypothetical analysis script
        batch_path = Path(batch_folder)
        
        # Load config (as analysis script would)
        with open(batch_path / 'config.json', 'r') as f:
            config = json.load(f)
        
        self.assertIn('n_replicates', config)
        self.assertIn('recorded_objects', config)
        self.assertIn('settings', config)
        
        # Load summary (as analysis script would)
        with open(batch_path / 'summary.json', 'r') as f:
            summary = json.load(f)
        
        self.assertIn('statistics', summary)
        
        # Load CSV (as analysis script would)
        csv_file = batch_path / 'run_001.csv'
        self.assertTrue(csv_file.exists())


if __name__ == '__main__':
    unittest.main()
