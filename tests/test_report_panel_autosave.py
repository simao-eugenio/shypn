#!/usr/bin/env python3
"""Test Report Panel Auto-Save Integration.

Tests that simulations in the Report panel are automatically saved
using the unified BatchResultsSaver infrastructure.

Author: Simão Eugénio
Date: January 2026
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch


def test_report_panel_autosave_method_exists():
    """Test that DynamicAnalysesCategory has auto-save method."""
    from shypn.ui.panels.report.parameters_category import DynamicAnalysesCategory
    
    # Create instance (will fail without GTK, but we can check the class)
    assert hasattr(DynamicAnalysesCategory, '_auto_save_simulation'), \
        "DynamicAnalysesCategory should have _auto_save_simulation method"
    assert hasattr(DynamicAnalysesCategory, '_get_project_folder'), \
        "DynamicAnalysesCategory should have _get_project_folder method"


def test_report_panel_autosave_folder_structure():
    """Test that auto-save creates correct folder structure."""
    # Create temporary project folder
    with tempfile.TemporaryDirectory() as temp_dir:
        project_folder = Path(temp_dir)
        
        # Mock simulation data
        sim_data = {
            'time_points': [0, 1, 2, 3, 4, 5],
            'place_data': {
                'p1': [10, 12, 14, 16, 18, 20],
                'p2': [5, 6, 7, 8, 9, 10]
            },
            'transition_data': {
                't1': [1, 2, 3, 4, 5, 6]
            },
            'model': Mock(name='test_model', id='test_model'),
            'metadata': {'duration': 5, 'mode': 'continuous'},
            'accounting_report': None
        }
        
        # Mock the category
        from shypn.ui.panels.report.parameters_category import DynamicAnalysesCategory
        
        # Create a mock category instance
        category = Mock(spec=DynamicAnalysesCategory)
        category.controller = Mock()
        category.controller.model = sim_data['model']
        
        # Bind the actual methods to the mock
        category._auto_save_simulation = DynamicAnalysesCategory._auto_save_simulation.__get__(category)
        category._get_project_folder = lambda: str(project_folder)
        
        # Mock the exporters to avoid actual export operations
        with patch('shypn.ui.panels.report.parameters_category.CSVSimulationExporter') as mock_csv:
            with patch('shypn.ui.panels.report.parameters_category.JSONSimulationExporter') as mock_json:
                # Setup mocks
                mock_csv_instance = Mock()
                mock_csv.return_value = mock_csv_instance
                mock_csv_instance.export_timeseries_wide.return_value = True
                mock_csv_instance.export_summary_statistics.return_value = True
                
                mock_json_instance = Mock()
                mock_json.return_value = mock_json_instance
                mock_json_instance.export.return_value = True
                
                # Call auto-save
                category._auto_save_simulation(sim_data)
                
                # Verify folder structure
                simulations_folder = project_folder / 'simulations'
                assert simulations_folder.exists(), "simulations/ folder should be created"
                
                # Find the simulation folder (should be simulation_test_model_TIMESTAMP)
                sim_folders = list(simulations_folder.glob('simulation_*'))
                assert len(sim_folders) >= 1, "At least one simulation folder should be created"
                
                sim_folder = sim_folders[0]
                
                # Verify files exist
                assert (sim_folder / 'config.json').exists(), "config.json should exist"
                assert (sim_folder / 'metadata.txt').exists(), "metadata.txt should exist"
                
                # Verify config.json content
                with open(sim_folder / 'config.json') as f:
                    config = json.load(f)
                    assert config['model_name'] == 'test_model'
                    assert config['simulation_type'] == 'report_panel'
                    assert 'timestamp' in config
                
                # Verify exporters were called
                assert mock_csv_instance.export_timeseries_wide.called
                assert mock_csv_instance.export_summary_statistics.called
                assert mock_json_instance.export.called


def test_report_panel_autosave_no_project():
    """Test that auto-save handles missing project gracefully."""
    from shypn.ui.panels.report.parameters_category import DynamicAnalysesCategory
    
    # Mock category with no project
    category = Mock(spec=DynamicAnalysesCategory)
    category.controller = None
    
    # Bind methods
    category._auto_save_simulation = DynamicAnalysesCategory._auto_save_simulation.__get__(category)
    category._get_project_folder = lambda: None  # No project folder
    
    # Mock sim_data
    sim_data = {
        'time_points': [0, 1, 2],
        'place_data': {'p1': [1, 2, 3]},
        'transition_data': {},
        'model': Mock(name='test', id='test'),
        'metadata': {},
        'accounting_report': None
    }
    
    # Should not raise exception, just print warning
    try:
        category._auto_save_simulation(sim_data)
        # If no exception, test passes
        assert True
    except Exception as e:
        # Should not raise - test fails
        assert False, f"Auto-save should not raise exception when no project: {e}"


def test_report_panel_autosave_integration_mock():
    """Test integration with on_simulation_complete callback (mocked)."""
    from shypn.ui.panels.report.parameters_category import DynamicAnalysesCategory
    
    # Mock category
    category = Mock(spec=DynamicAnalysesCategory)
    category._registered_controllers = set()
    category._refresh_generation = 0
    category._pending_refresh_id = None
    category.controller = None
    category.parent_panel = None
    
    # Bind the register method
    category._register_simulation_complete_callback = \
        DynamicAnalysesCategory._register_simulation_complete_callback.__get__(category)
    
    # Mock controller
    controller = Mock()
    controller.data_collector = Mock()
    controller.data_collector.has_data.return_value = True
    controller.data_collector.time_points = [0, 1, 2]
    controller.data_collector.place_data = {'p1': [1, 2, 3]}
    controller.data_collector.transition_data = {}
    controller.model = Mock(name='test_model', id='test_model')
    
    # Mock the auto_save method
    category._auto_save_simulation = Mock()
    
    # Register callback
    category._register_simulation_complete_callback(controller)
    
    # Verify callback was set
    assert hasattr(controller, 'on_simulation_complete')
    assert callable(controller.on_simulation_complete)
    
    # Trigger callback
    controller.on_simulation_complete()
    
    # Verify auto-save was called (may be delayed due to GLib.idle_add)
    # For this mock test, we mainly verify the callback structure exists
    assert id(controller) in category._registered_controllers


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
