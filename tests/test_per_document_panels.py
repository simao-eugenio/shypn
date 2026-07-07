#!/usr/bin/env python3
"""Unit tests for per-document panel architecture.

Tests the OOP base class and concrete panel loader implementations to ensure:
- Panel instance isolation per document
- State preservation on tab switching
- Proper cleanup on document close
- Factory pattern correctness

Author: SHYPN Development Team
Date: 2026-01-06
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.helpers.base_panel_loader import PerDocumentPanelLoader, PanelLoaderFactory


class MockPanel:
    """Mock panel widget for testing."""
    def __init__(self):
        self.set_no_show_all_called = False
        self.show_all_called = False
        self.hide_called = False
        self.parent = None
        
    def set_no_show_all(self, value):
        self.set_no_show_all_called = True
        
    def show_all(self):
        self.show_all_called = True
        
    def hide(self):
        self.hide_called = True
        
    def get_parent(self):
        return self.parent
    
    def destroy(self):
        pass


class ConcretePanelLoader(PerDocumentPanelLoader):
    """Concrete implementation for testing."""
    
    def _create_panel(self):
        return MockPanel()
    
    def get_panel_name(self):
        return "Test Panel"


class TestPerDocumentPanelLoader(unittest.TestCase):
    """Test PerDocumentPanelLoader base class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_model = Mock()
        self.mock_parent_window = Mock()
    
    def test_initialization(self):
        """Test panel loader initialization."""
        loader = ConcretePanelLoader(
            model=self.mock_model,
            parent_window=self.mock_parent_window
        )
        
        # Verify attributes set
        self.assertEqual(loader.model, self.mock_model)
        self.assertEqual(loader.parent_window, self.mock_parent_window)
        self.assertIsNotNone(loader.panel)
        self.assertIsNotNone(loader.widget)
        
        # Verify panel created (set_no_show_all is called during attach/detach,
        # not during __init__ — intentional: avoids breaking matplotlib canvas)
        self.assertFalse(loader.panel.show_all_called)  # no premature show_all
    
    def test_panel_name(self):
        """Test get_panel_name() returns correct name."""
        loader = ConcretePanelLoader(model=self.mock_model)
        self.assertEqual(loader.get_panel_name(), "Test Panel")
    
    def test_is_attached_property(self):
        """Test is_attached property getter/setter."""
        loader = ConcretePanelLoader(model=self.mock_model)
        
        # Default is attached
        self.assertTrue(loader.is_attached)
        
        # Set to not attached
        loader.is_attached = False
        self.assertFalse(loader.is_attached)
    
    def test_is_visible_property(self):
        """Test is_visible property shows/hides widget."""
        loader = ConcretePanelLoader(model=self.mock_model)
        
        # Default is not visible
        self.assertFalse(loader.is_visible)
        
        # Set visible
        loader.is_visible = True
        self.assertTrue(loader.is_visible)
        self.assertTrue(loader.panel.show_all_called)
        
        # Set hidden
        loader.is_visible = False
        self.assertFalse(loader.is_visible)
        self.assertTrue(loader.panel.hide_called)
    
    def test_show_hide_methods(self):
        """Test show() and hide() convenience methods."""
        loader = ConcretePanelLoader(model=self.mock_model)
        
        # Show
        loader.show()
        self.assertTrue(loader.is_visible)
        self.assertTrue(loader.panel.show_all_called)
        
        # Hide
        loader.hide()
        self.assertFalse(loader.is_visible)
        self.assertTrue(loader.panel.hide_called)
    
    def test_get_widget(self):
        """Test get_widget() returns panel widget."""
        loader = ConcretePanelLoader(model=self.mock_model)
        widget = loader.get_widget()
        self.assertEqual(widget, loader.panel)
    
    def test_set_model(self):
        """Test set_model() updates model reference."""
        loader = ConcretePanelLoader(model=self.mock_model)
        
        new_model = Mock()
        loader.set_model(new_model)
        
        self.assertEqual(loader.model, new_model)
    
    def test_cleanup(self):
        """Test cleanup() destroys widgets properly."""
        loader = ConcretePanelLoader(model=self.mock_model)
        
        # Verify panel exists
        self.assertIsNotNone(loader.panel)
        self.assertIsNotNone(loader.widget)
        
        # Cleanup
        loader.cleanup()
        
        # Verify widgets destroyed
        self.assertIsNone(loader.panel)
        self.assertIsNone(loader.widget)
    
    def test_repr(self):
        """Test string representation."""
        loader = ConcretePanelLoader(model=self.mock_model)
        repr_str = repr(loader)
        
        self.assertIn("ConcretePanelLoader", repr_str)
        self.assertIn("Test Panel", repr_str)
        self.assertIn("attached=True", repr_str)
        self.assertIn("visible=False", repr_str)


class TestPanelLoaderFactory(unittest.TestCase):
    """Test PanelLoaderFactory."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_workspace_settings = Mock()
        self.mock_parent_window = Mock()
        self.factory = PanelLoaderFactory(
            workspace_settings=self.mock_workspace_settings,
            parent_window=self.mock_parent_window
        )
    
    def test_factory_initialization(self):
        """Test factory initializes with correct settings."""
        self.assertEqual(self.factory.workspace_settings, self.mock_workspace_settings)
        self.assertEqual(self.factory.parent_window, self.mock_parent_window)
    
    @patch('shypn.helpers.pathway_panel_loader.PathwayPanelLoader')
    def test_create_pathway_panel(self, mock_pathway_loader_class):
        """Test create_pathway_panel() creates loader correctly."""
        mock_model = Mock()
        mock_instance = Mock()
        mock_pathway_loader_class.return_value = mock_instance
        
        loader = self.factory.create_pathway_panel(mock_model)
        
        # Verify PathwayPanelLoader was instantiated with correct args
        mock_pathway_loader_class.assert_called_once_with(
            model=mock_model,
            parent_window=self.mock_parent_window,
            workspace_settings=self.mock_workspace_settings
        )
        self.assertEqual(loader, mock_instance)
    
    @patch('shypn.helpers.analyses_panel_loader.AnalysesPanelLoader')
    def test_create_analyses_panel(self, mock_analyses_loader_class):
        """Test create_analyses_panel() creates loader correctly."""
        mock_model = Mock()
        mock_data_collector = Mock()
        mock_instance = Mock()
        mock_analyses_loader_class.return_value = mock_instance
        
        loader = self.factory.create_analyses_panel(mock_model, mock_data_collector)
        
        # Verify AnalysesPanelLoader was instantiated
        mock_analyses_loader_class.assert_called_once_with(
            model=mock_model,
            data_collector=mock_data_collector,
            parent_window=self.mock_parent_window
        )
        self.assertEqual(loader, mock_instance)
    
    @patch('shypn.helpers.topology_panel_loader.TopologyPanelLoader')
    def test_create_topology_panel(self, mock_topology_loader_class):
        """Test create_topology_panel() creates loader correctly."""
        mock_model = Mock()
        mock_instance = Mock()
        mock_topology_loader_class.return_value = mock_instance
        
        loader = self.factory.create_topology_panel(mock_model)
        
        # Verify TopologyPanelLoader was instantiated with correct args
        mock_topology_loader_class.assert_called_once_with(
            model=mock_model,
            parent_window=self.mock_parent_window
        )
        self.assertEqual(loader, mock_instance)


class TestPanelInstanceIsolation(unittest.TestCase):
    """Test that each document has isolated panel instances."""
    
    def test_different_documents_have_different_loaders(self):
        """Each document should get its own panel loader instance."""
        mock_model_a = Mock()
        mock_model_b = Mock()
        
        loader_a = ConcretePanelLoader(model=mock_model_a)
        loader_b = ConcretePanelLoader(model=mock_model_b)
        
        # Verify different instances
        self.assertIsNot(loader_a, loader_b)
        self.assertIsNot(loader_a.panel, loader_b.panel)
        self.assertIsNot(loader_a.widget, loader_b.widget)
        
        # Verify different models
        self.assertEqual(loader_a.model, mock_model_a)
        self.assertEqual(loader_b.model, mock_model_b)
    
    def test_panel_state_isolation(self):
        """Panel state should be isolated between instances."""
        mock_model_a = Mock()
        mock_model_b = Mock()
        
        loader_a = ConcretePanelLoader(model=mock_model_a)
        loader_b = ConcretePanelLoader(model=mock_model_b)
        
        # Modify loader_a state
        loader_a.is_visible = True
        loader_a.is_attached = False
        
        # Verify loader_b state unaffected
        self.assertFalse(loader_b.is_visible)  # Default is False
        self.assertTrue(loader_b.is_attached)  # Default is True
    
    def test_multiple_loaders_from_factory(self):
        """Factory should create independent instances."""
        factory = PanelLoaderFactory()
        mock_model_a = Mock()
        mock_model_b = Mock()
        
        # Create two loaders with same factory
        loader_a = ConcretePanelLoader(model=mock_model_a)
        loader_b = ConcretePanelLoader(model=mock_model_b)
        
        # Verify independent instances
        self.assertIsNot(loader_a, loader_b)
        self.assertIsNot(loader_a.panel, loader_b.panel)


class TestPanelCleanup(unittest.TestCase):
    """Test panel cleanup on document close."""
    
    def test_cleanup_destroys_widgets(self):
        """Cleanup should destroy panel widgets."""
        mock_model = Mock()
        loader = ConcretePanelLoader(model=mock_model)
        
        # Verify panel exists
        panel = loader.panel
        self.assertIsNotNone(panel)
        
        # Cleanup
        loader.cleanup()
        
        # Verify panel destroyed
        self.assertIsNone(loader.panel)
        self.assertIsNone(loader.widget)
    
    def test_cleanup_removes_from_parent(self):
        """Cleanup should remove widget from parent container."""
        mock_model = Mock()
        loader = ConcretePanelLoader(model=mock_model)
        
        # Mock parent container
        mock_parent = Mock()
        loader.panel.parent = mock_parent
        loader.panel.get_parent = Mock(return_value=mock_parent)
        
        # Cleanup
        loader.cleanup()
        
        # Verify remove called
        mock_parent.remove.assert_called_once()


class TestWaylandSafety(unittest.TestCase):
    """Test Wayland-safe implementation."""
    
    def test_no_premature_window_operations(self):
        """Panel should not perform window operations before parenting."""
        mock_model = Mock()
        loader = ConcretePanelLoader(model=mock_model)
        
        # Wayland safety: set_no_show_all is called during attach/detach
        # (not in __init__ — removed to fix matplotlib canvas rendering).
        # Key invariant: no premature show_all before explicit visibility control.
        self.assertFalse(loader.panel.show_all_called)
    
    def test_proper_visibility_control(self):
        """Visibility should be controlled explicitly, not automatic."""
        mock_model = Mock()
        loader = ConcretePanelLoader(model=mock_model)
        
        # Default: not visible
        self.assertFalse(loader.is_visible)
        
        # Must explicitly show
        loader.show()
        self.assertTrue(loader.is_visible)


def suite():
    """Create test suite."""
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TestPerDocumentPanelLoader))
    test_suite.addTest(unittest.makeSuite(TestPanelLoaderFactory))
    test_suite.addTest(unittest.makeSuite(TestPanelInstanceIsolation))
    test_suite.addTest(unittest.makeSuite(TestPanelCleanup))
    test_suite.addTest(unittest.makeSuite(TestWaylandSafety))
    return test_suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())
