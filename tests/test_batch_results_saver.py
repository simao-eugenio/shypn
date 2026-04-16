#!/usr/bin/env python3
"""Tests for BatchResultsSaver - Unified batch results persistence.

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

from shypn.helpers.batch_results_saver import BatchResultsSaver, save_swiss_palette_batch


class TestBatchResultsSaver(unittest.TestCase):
    """Test suite for BatchResultsSaver class."""
    
    def setUp(self):
        """Create temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()
        self.saver = BatchResultsSaver(self.test_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)
    
    def test_create_batch_folder(self):
        """Test batch folder creation with timestamp."""
        batch_path = self.saver.create_batch_folder()
        
        self.assertTrue(batch_path.exists())
        self.assertTrue(batch_path.is_dir())
        self.assertIsNotNone(self.saver.timestamp)
        self.assertTrue(str(batch_path).endswith(self.saver.timestamp))
    
    def test_create_batch_folder_with_suffix(self):
        """Test batch folder creation with custom suffix."""
        batch_path = self.saver.create_batch_folder(name_suffix='EPO_dose')
        
        self.assertTrue(batch_path.exists())
        self.assertTrue('EPO_dose' in str(batch_path))
        self.assertTrue(self.saver.timestamp in str(batch_path))
    
    def test_save_config(self):
        """Test configuration file saving."""
        self.saver.create_batch_folder()
        
        config_path = self.saver.save_config(
            n_replicates=100,
            recorded_objects=['P1', 'P2', 'T1'],
            settings={'duration': 1000, 'tau_leaping': True}
        )
        
        self.assertTrue(config_path.exists())
        
        # Verify contents
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.assertEqual(config['n_replicates'], 100)
        self.assertEqual(config['recorded_objects'], ['P1', 'P2', 'T1'])
        self.assertEqual(config['settings']['duration'], 1000)
    
    def test_save_replicate_csv(self):
        """Test individual replicate CSV saving."""
        self.saver.create_batch_folder()
        
        # Mock trajectory data
        time_points = [0.0, 0.1, 0.2, 0.3]
        place_data = {
            'P1': [(0.0, 10), (0.1, 12), (0.2, 15), (0.3, 18)],
            'P2': [(0.0, 5), (0.1, 6), (0.2, 7), (0.3, 8)]
        }
        transition_data = {
            'T1': [(0.0, 0), (0.1, 2), (0.2, 4), (0.3, 6)]
        }
        
        csv_path = self.saver.save_replicate_csv(
            replicate_id=0,
            time_points=time_points,
            place_data=place_data,
            transition_data=transition_data,
            metadata_context=None,
            use_metadata_header=False
        )
        
        self.assertTrue(csv_path.exists())
        self.assertEqual(csv_path.name, 'run_001.csv')
        
        # Verify CSV contents
        with open(csv_path, 'r') as f:
            lines = f.readlines()
        
        # Check header
        self.assertIn('time', lines[0])
        self.assertIn('P1', lines[0])
        self.assertIn('P2', lines[0])
        self.assertIn('T1', lines[0])
        
        # Check data rows
        self.assertEqual(len(lines), 5)  # Header + 4 data rows
    
    def test_save_summary(self):
        """Test summary statistics saving."""
        self.saver.create_batch_folder()
        
        # Mock results from multiple replicates
        results = [
            {
                'replicate_id': 0,
                'place_data': {
                    'P1': [(0.0, 10), (1.0, 20)],
                    'P2': [(0.0, 5), (1.0, 10)]
                }
            },
            {
                'replicate_id': 1,
                'place_data': {
                    'P1': [(0.0, 12), (1.0, 22)],
                    'P2': [(0.0, 6), (1.0, 11)]
                }
            },
            {
                'replicate_id': 2,
                'place_data': {
                    'P1': [(0.0, 11), (1.0, 21)],
                    'P2': [(0.0, 5), (1.0, 10)]
                }
            }
        ]
        
        summary_path = self.saver.save_summary(
            results=results,
            recorded_objects={'P1', 'P2'},
            n_replicates=3
        )
        
        self.assertTrue(summary_path.exists())
        
        # Verify summary contents
        with open(summary_path, 'r') as f:
            summary = json.load(f)
        
        self.assertEqual(summary['successful_replicates'], 3)
        self.assertEqual(summary['total_replicates'], 3)
        self.assertIn('P1', summary['statistics'])
        self.assertIn('P2', summary['statistics'])
        
        # Check statistics structure
        p1_stats = summary['statistics']['P1']
        self.assertIn('mean', p1_stats)
        self.assertIn('std', p1_stats)
        self.assertIn('min', p1_stats)
        self.assertIn('max', p1_stats)
        self.assertIn('final_mean', p1_stats)
        self.assertIn('final_std', p1_stats)
    
    def test_save_batch_complete(self):
        """Test complete batch save operation."""
        # Mock complete batch data
        results = []
        for i in range(5):
            results.append({
                'replicate_id': i,
                'time_points': [0.0, 1.0, 2.0],
                'place_data': {
                    'P1': [(0.0, 10 + i), (1.0, 20 + i), (2.0, 30 + i)]
                },
                'transition_data': {
                    'T1': [(0.0, 0), (1.0, i), (2.0, 2*i)]
                }
            })
        
        batch_path = self.saver.save_batch(
            results=results,
            recorded_objects={'P1', 'T1'},
            n_replicates=5,
            settings={'duration': 2.0, 'tau_leaping': True},
            model=None,
            name_suffix='test_batch'
        )
        
        self.assertTrue(batch_path.exists())
        
        # Verify all expected files exist
        self.assertTrue((batch_path / 'config.json').exists())
        self.assertTrue((batch_path / 'summary.json').exists())
        
        # Verify all replicate CSVs exist
        for i in range(5):
            csv_path = batch_path / f'run_{i+1:03d}.csv'
            self.assertTrue(csv_path.exists())
    
    def test_minimal_header_generation(self):
        """Test minimal header fallback when SweepHeaderGenerator fails."""
        self.saver.create_batch_folder()
        
        header = self.saver._generate_minimal_header(
            context={'test': 'data'},
            replicate_id=0
        )
        
        self.assertIn('SHYPN BATCH EXPERIMENT DATA', header)
        self.assertIn('Replicate ID: 1', header)
        self.assertIn(self.saver.timestamp, header)
        self.assertTrue(header.startswith('# '))
    
    def test_custom_subfolder(self):
        """Test using custom subfolder for results."""
        saver = BatchResultsSaver(
            self.test_dir,
            subfolder='experiments/results',
            batch_prefix='experiment'
        )
        
        batch_path = saver.create_batch_folder('test')
        
        self.assertTrue('experiments/results' in str(batch_path))
        self.assertTrue('experiment_test' in str(batch_path))
    
    def test_skip_failed_replicates(self):
        """Test that failed replicates are skipped in save_batch."""
        results = [
            {
                'replicate_id': 0,
                'time_points': [0.0, 1.0],
                'place_data': {'P1': [(0.0, 10), (1.0, 20)]}
            },
            {
                'replicate_id': 1,
                'error': 'Simulation failed'
            },
            {
                'replicate_id': 2,
                'time_points': [0.0, 1.0],
                'place_data': {'P1': [(0.0, 12), (1.0, 22)]}
            }
        ]
        
        batch_path = self.saver.save_batch(
            results=results,
            recorded_objects={'P1'},
            n_replicates=3,
            settings={'duration': 1.0}
        )
        
        # Only 2 CSVs should exist (failed replicate skipped)
        csv_files = list(batch_path.glob('run_*.csv'))
        self.assertEqual(len(csv_files), 2)
        
        # Summary should show 2 successful out of 3 total
        with open(batch_path / 'summary.json', 'r') as f:
            summary = json.load(f)
        
        self.assertEqual(summary['successful_replicates'], 2)
        self.assertEqual(summary['total_replicates'], 3)


class TestSwissPaletteBatchSave(unittest.TestCase):
    """Test suite for Swiss Palette convenience function."""
    
    def setUp(self):
        """Create temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)
    
    def test_save_swiss_palette_batch(self):
        """Test Swiss Palette batch save wrapper."""
        # Mock model
        class MockModel:
            filepath = None
        
        # Mock settings
        class MockSettings:
            duration = 1000.0
            time_units = 'SECONDS'
            dt_auto = True
            use_tau_leaping = True
            tau_epsilon = 0.03
        
        model = MockModel()
        settings = MockSettings()
        
        results = [
            {
                'replicate_id': 0,
                'time_points': [0.0, 1.0],
                'place_data': {'P1': [(0.0, 10), (1.0, 20)]},
                'transition_data': {}
            }
        ]
        
        batch_path = save_swiss_palette_batch(
            results=results,
            recorded_objects={'P1'},
            n_replicates=1,
            simulation_settings=settings,
            model=model,
            project_folder=self.test_dir
        )
        
        self.assertTrue(Path(batch_path).exists())
        self.assertTrue((Path(batch_path) / 'config.json').exists())
        self.assertTrue((Path(batch_path) / 'run_001.csv').exists())
        self.assertTrue((Path(batch_path) / 'summary.json').exists())


if __name__ == '__main__':
    unittest.main()
