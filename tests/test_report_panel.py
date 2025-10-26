#!/usr/bin/env python3
"""Test Report Panel - Wayland compatible.

Tests the report panel with mock data.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.ui.panels.report import ReportPanel


class MockProject:
    """Mock project for testing."""
    
    def __init__(self):
        self.name = "Test Project"
        self.base_path = "/home/user/projects/test_project"
        self.created_date = "2025-10-20 10:00:00"
        self.modified_date = "2025-10-25 14:30:00"
        self.models = ['model1', 'model2', 'model3']
        self.pathways = MockPathways()


class MockPathways:
    """Mock pathways for testing."""
    
    def list_pathways(self):
        return [
            MockPathway("Glycolysis", "kegg", "hsa00010", "Homo sapiens", "2025-10-25 14:00:00", "hsa00010.kgml", "model-xyz"),
            MockPathway("TCA Cycle", "sbml", "tca_cycle", "Homo sapiens", "2025-10-24 09:00:00", "tca.sbml", None)
        ]


class MockPathway:
    """Mock pathway for testing."""
    
    def __init__(self, name, source_type, source_id, organism, date, raw_file, model_id):
        self.name = name
        self.source_type = source_type
        self.source_id = source_id
        self.source_organism = organism
        self.imported_date = date
        self.raw_file = raw_file
        self.model_id = model_id
        self.enrichments = []


class MockModelCanvas:
    """Mock model canvas for testing."""
    
    def __init__(self):
        self.model = MockModel()


class MockModel:
    """Mock model for testing."""
    
    def __init__(self):
        self.places = {f'p{i}': MockPlace(f'Place {i}', f'p{i}') for i in range(1, 46)}
        self.transitions = {f't{i}': MockTransition(f'Reaction {i}', f't{i}') for i in range(1, 39)}
        self.arcs = list(range(120))


class MockPlace:
    """Mock place for testing."""
    
    def __init__(self, label, id):
        self.label = label
        self.id = id


class MockTransition:
    """Mock transition for testing."""
    
    def __init__(self, label, id):
        self.label = label
        self.id = id


class TestReportWindow(Gtk.Window):
    """Test window for report panel."""
    
    def __init__(self):
        super().__init__(title="SHYpn Report Panel Test")
        self.set_default_size(800, 600)
        self.connect('destroy', Gtk.main_quit)
        
        # Create mock data
        project = MockProject()
        model_canvas = MockModelCanvas()
        
        # Create report panel
        report_panel = ReportPanel(project=project, model_canvas=model_canvas)
        
        self.add(report_panel)
        self.show_all()


def main():
    """Main test function."""
    print("[TEST] Starting Report Panel test...")
    print("[TEST] Creating window with mock data...")
    
    window = TestReportWindow()
    
    print("[TEST] Window created. Starting GTK main loop...")
    print("[TEST] Close the window to exit.")
    
    Gtk.main()
    
    print("[TEST] Test completed.")


if __name__ == '__main__':
    main()
