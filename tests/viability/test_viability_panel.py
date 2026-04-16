#!/usr/bin/env python3
"""Test Viability Panel - Phase 1 tests.

Tests basic panel creation, display, and topology integration.

Author: Simão Eugénio
Date: November 9, 2025
"""

import sys
import unittest

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# Add src to path
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.ui.panels.viability import ViabilityPanel
from shypn.ui.panels.viability.diagnosis_view import DiagnosisView
from shypn.helpers.viability_panel_loader import ViabilityPanelLoader


class TestViabilityPanel(unittest.TestCase):
    """Test ViabilityPanel class."""
    
    def test_panel_creation(self):
        """Test that panel can be created."""
        panel = ViabilityPanel()
        self.assertIsNotNone(panel)
        self.assertIsInstance(panel, Gtk.Box)
    
    def test_panel_has_required_widgets(self):
        """Test panel has all required widgets."""
        panel = ViabilityPanel()
        
        # Should have float button
        self.assertTrue(hasattr(panel, 'float_button'))
        self.assertIsInstance(panel.float_button, Gtk.ToggleButton)
        
        # Should have diagnosis view
        self.assertTrue(hasattr(panel, 'diagnosis_view'))
        self.assertIsInstance(panel.diagnosis_view, DiagnosisView)
        
        # Should have scan button
        self.assertTrue(hasattr(panel, 'scan_button'))
        self.assertIsInstance(panel.scan_button, Gtk.Button)
    
    def test_set_topology_panel(self):
        """Test setting topology panel reference."""
        panel = ViabilityPanel()
        
        # Mock topology panel
        mock_topology = type('MockTopology', (), {
            'generate_summary_for_report_panel': lambda: {
                'status': 'complete',
                'statistics': {},
                'warnings': []
            }
        })()
        
        panel.set_topology_panel(mock_topology)
        self.assertIsNotNone(panel.topology_panel)


class TestDiagnosisView(unittest.TestCase):
    """Test DiagnosisView widget."""
    
    def test_view_creation(self):
        """Test that view can be created."""
        view = DiagnosisView()
        self.assertIsNotNone(view)
        self.assertIsInstance(view, Gtk.ScrolledWindow)
    
    def test_display_empty_issues(self):
        """Test displaying empty issue list."""
        view = DiagnosisView()
        view.display_issues([])
        
        # Should show "no issues" message
        count = view.get_issue_count()
        self.assertEqual(count, 1)  # One entry: "No issues detected"
    
    def test_display_issues(self):
        """Test displaying issue list."""
        view = DiagnosisView()
        
        issues = [
            {
                'severity': 'critical',
                'type': 'deadlock',
                'description': 'Model can deadlock',
                'id': 'deadlock_1'
            },
            {
                'severity': 'warning',
                'type': 'unbounded',
                'description': 'Place P9 is unbounded',
                'id': 'unbounded_1'
            }
        ]
        
        view.display_issues(issues)
        
        # Should show 2 issues (plus 2 category headers)
        # Actually get_issue_count only counts leaf nodes
        count = view.get_issue_count()
        self.assertEqual(count, 2)
    
    def test_clear(self):
        """Test clearing issues."""
        view = DiagnosisView()
        
        issues = [{'severity': 'info', 'type': 'test', 'description': 'Test', 'id': '1'}]
        view.display_issues(issues)
        
        view.clear()
        count = view.get_issue_count()
        self.assertEqual(count, 0)


class TestViabilityPanelLoader(unittest.TestCase):
    """Test ViabilityPanelLoader class."""
    
    def test_loader_creation(self):
        """Test that loader can be created."""
        loader = ViabilityPanelLoader(model=None)
        self.assertIsNotNone(loader)
    
    def test_loader_has_panel(self):
        """Test loader creates panel."""
        loader = ViabilityPanelLoader(model=None)
        self.assertIsNotNone(loader.panel)
        self.assertIsInstance(loader.panel, ViabilityPanel)
    
    def test_loader_has_window(self):
        """Test loader creates floating window."""
        loader = ViabilityPanelLoader(model=None)
        self.assertIsNotNone(loader.window)
        self.assertIsInstance(loader.window, Gtk.Window)
    
    def test_loader_compatibility_attributes(self):
        """Test loader has compatibility attributes."""
        loader = ViabilityPanelLoader(model=None)
        
        # Should have controller
        self.assertTrue(hasattr(loader, 'controller'))
        self.assertEqual(loader.controller, loader)
        
        # Should have widget/content references
        self.assertTrue(hasattr(loader, 'widget'))
        self.assertTrue(hasattr(loader, 'content'))
        self.assertEqual(loader.widget, loader.panel)
        self.assertEqual(loader.content, loader.panel)


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("VIABILITY PANEL - PHASE 1 TESTS")
    print("=" * 60 + "\n")
    
    # Run tests
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    main()
