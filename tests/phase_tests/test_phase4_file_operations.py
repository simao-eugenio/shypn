#!/usr/bin/env python3
"""
Phase 4 Integration Test: File Operations with Lifecycle System

Tests complete lifecycle integration including:
- File → New: Creates new canvas with independent ID scope
- File → Open: Loads file into new canvas with independent ID scope
- File → Close: Properly destroys canvas and cleans up resources
- Multi-canvas: Verify ID isolation between multiple open canvases
- Global IDManager integration: Verify automatic scoping via global delegation

This test validates the complete Phase 4 implementation:
- Task 1: add_document() integration
- Task 2: close_tab() integration  
- Task 3: Global IDManager scoping
- Task 4: reset_current_canvas() functionality

Author: Phase 4 Team
Date: 2025-01-05
"""

import sys
import unittest
from unittest.mock import Mock, MagicMock, patch, call
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# Add project root to path
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.canvas.lifecycle import (
    CanvasLifecycleManager,
    IDScopeManager,
)
from shypn.data.canvas.id_manager import (
    IDManager,
    set_lifecycle_scope_manager,
    get_lifecycle_scope_manager,
)


class TestGlobalIDManagerIntegration(unittest.TestCase):
    """Test global IDManager integration with lifecycle scoping."""
    
    def setUp(self):
        """Set up test with fresh global state."""
        # Reset global scope manager
        set_lifecycle_scope_manager(None)
        
    def tearDown(self):
        """Clean up global state."""
        set_lifecycle_scope_manager(None)
        
    def test_global_idmanager_without_lifecycle(self):
        """Test that global IDManager works without lifecycle (backward compat)."""
        id_mgr = IDManager()
        
        # Should use local counters
        p1 = id_mgr.generate_place_id()
        p2 = id_mgr.generate_place_id()
        
        self.assertEqual(p1, 'P1')
        self.assertEqual(p2, 'P2')
        
    def test_global_idmanager_with_lifecycle(self):
        """Test that global IDManager delegates to lifecycle when available."""
        # Create lifecycle scope manager
        scope_mgr = IDScopeManager()
        scope_mgr.set_scope('canvas_1')
        set_lifecycle_scope_manager(scope_mgr)
        
        # Create IDManager instances (simulating DocumentModel/DocumentController)
        id_mgr1 = IDManager()
        id_mgr2 = IDManager()
        
        # Both should delegate to lifecycle scope manager
        p1 = id_mgr1.generate_place_id()
        p2 = id_mgr2.generate_place_id()
        
        # Should get sequential IDs from shared scope
        self.assertEqual(p1, 'P1')
        self.assertEqual(p2, 'P2')
        
    def test_global_idmanager_multi_canvas(self):
        """Test that global IDManager respects canvas switching."""
        scope_mgr = IDScopeManager()
        set_lifecycle_scope_manager(scope_mgr)
        
        id_mgr = IDManager()
        
        # Canvas 1
        scope_mgr.set_scope('canvas_1')
        c1_p1 = id_mgr.generate_place_id()
        c1_p2 = id_mgr.generate_place_id()
        
        # Canvas 2  
        scope_mgr.set_scope('canvas_2')
        c2_p1 = id_mgr.generate_place_id()
        
        # Back to Canvas 1
        scope_mgr.set_scope('canvas_1')
        c1_p3 = id_mgr.generate_place_id()
        
        # Verify independence
        self.assertEqual(c1_p1, 'P1')
        self.assertEqual(c1_p2, 'P2')
        self.assertEqual(c1_p3, 'P3')  # Continues from P2
        
        self.assertEqual(c2_p1, 'P1')  # Fresh start in new canvas
        
    def test_global_idmanager_register_methods(self):
        """Test that register methods also delegate to lifecycle."""
        scope_mgr = IDScopeManager()
        scope_mgr.set_scope('test')
        set_lifecycle_scope_manager(scope_mgr)
        
        id_mgr = IDManager()
        
        # Register IDs (used when loading files)
        id_mgr.register_place_id('P5')
        id_mgr.register_transition_id('T3')
        
        # Next IDs should be higher
        p_next = id_mgr.generate_place_id()
        t_next = id_mgr.generate_transition_id()
        
        self.assertEqual(p_next, 'P6')
        self.assertEqual(t_next, 'T4')
        
    def test_global_idmanager_fallback_on_error(self):
        """Test that IDManager falls back to local counter on lifecycle error."""
        # Create broken scope manager that raises exceptions
        broken_scope = Mock()
        broken_scope.generate_place_id.side_effect = RuntimeError("Lifecycle error")
        set_lifecycle_scope_manager(broken_scope)
        
        id_mgr = IDManager()
        
        # Should fall back to local counter without crashing
        p1 = id_mgr.generate_place_id()
        p2 = id_mgr.generate_place_id()
        
        # Should work with local counters
        self.assertEqual(p1, 'P1')
        self.assertEqual(p2, 'P2')


class TestModelCanvasLoaderIntegration(unittest.TestCase):
    """Test ModelCanvasLoader integration with lifecycle system."""
    
    @patch('shypn.helpers.model_canvas_loader.Gtk.Builder')
    def setUp(self, mock_builder):
        """Set up with mocked GTK components."""
        from shypn.helpers.model_canvas_loader import ModelCanvasLoader
        
        # Mock GTK components
        mock_builder_instance = Mock()
        mock_builder.return_value = mock_builder_instance
        mock_builder_instance.get_object.return_value = Mock()
        
        # Create loader (will initialize lifecycle system)
        with patch('shypn.canvas.lifecycle.enable_lifecycle_system') as mock_enable:
            mock_lifecycle = Mock(spec=CanvasLifecycleManager)
            mock_lifecycle.id_manager = IDScopeManager()
            mock_adapter = Mock()
            mock_enable.return_value = (mock_lifecycle, mock_adapter)
            
            self.loader = ModelCanvasLoader()
            
        # Verify lifecycle was enabled
        self.assertIsNotNone(self.loader.lifecycle_manager)
        
        # Verify global IDManager was connected
        scope_mgr = get_lifecycle_scope_manager()
        self.assertIsNotNone(scope_mgr)
        
    def tearDown(self):
        """Clean up global state."""
        set_lifecycle_scope_manager(None)
        
    def test_add_document_creates_canvas(self):
        """Test that add_document creates canvas with lifecycle."""
        # Mock lifecycle create_canvas
        mock_context = Mock()
        self.loader.lifecycle_manager.create_canvas.return_value = mock_context
        
        # Create document
        drawing_area = self.loader.add_document(title="Test Document")
        
        # Verify lifecycle was called
        self.loader.lifecycle_manager.create_canvas.assert_called_once()
        
    def test_close_tab_destroys_canvas(self):
        """Test that close_tab destroys canvas with lifecycle."""
        # Mock notebook with one page
        self.loader.notebook = Mock()
        self.loader.notebook.get_n_pages.return_value = 1
        
        # Mock drawing area and page structure
        mock_drawing_area = Mock(spec=Gtk.DrawingArea)
        mock_scrolled = Mock(spec=Gtk.ScrolledWindow)
        mock_scrolled.get_child.return_value = mock_drawing_area
        
        self.loader.notebook.get_nth_page.return_value = mock_scrolled
        
        # Mock the canvas_managers dict
        self.loader.canvas_managers = {mock_drawing_area: Mock()}
        
        # Close tab
        self.loader.close_tab(0)
        
        # Verify lifecycle destroy was called
        self.loader.lifecycle_manager.destroy_canvas.assert_called_once_with(mock_drawing_area)
            
    def test_reset_current_canvas(self):
        """Test that reset_current_canvas calls lifecycle reset."""
        # Mock current document
        mock_drawing_area = Mock(spec=Gtk.DrawingArea)
        with patch.object(self.loader, 'get_current_document', return_value=mock_drawing_area):
            # Reset canvas
            result = self.loader.reset_current_canvas()
            
            # Verify lifecycle reset was called
            self.loader.lifecycle_manager.reset_canvas.assert_called_once_with(mock_drawing_area)
            self.assertTrue(result)
            
    def test_reset_current_canvas_no_document(self):
        """Test reset_current_canvas with no active document."""
        with patch.object(self.loader, 'get_current_document', return_value=None):
            result = self.loader.reset_current_canvas()
            self.assertFalse(result)


class TestMultiCanvasFileOperations(unittest.TestCase):
    """Test realistic multi-canvas file operation scenarios."""
    
    def setUp(self):
        """Set up lifecycle system for testing."""
        # For these tests, we only need the IDScopeManager, not full lifecycle
        self.id_scope_mgr = IDScopeManager()
        set_lifecycle_scope_manager(self.id_scope_mgr)
        
    def tearDown(self):
        """Clean up global state."""
        set_lifecycle_scope_manager(None)
        
    def test_three_canvases_independent_ids(self):
        """Test that three open canvases have independent ID sequences."""
        # Simulate three canvases with different scopes
        id_mgr = IDManager()
        
        # Canvas 1: Create P1, P2
        self.id_scope_mgr.set_scope('canvas_1')
        c1_p1 = id_mgr.generate_place_id()
        c1_p2 = id_mgr.generate_place_id()
        
        # Canvas 2: Create P1
        self.id_scope_mgr.set_scope('canvas_2')
        c2_p1 = id_mgr.generate_place_id()
        
        # Canvas 3: Create P1, P2, P3
        self.id_scope_mgr.set_scope('canvas_3')
        c3_p1 = id_mgr.generate_place_id()
        c3_p2 = id_mgr.generate_place_id()
        c3_p3 = id_mgr.generate_place_id()
        
        # Back to Canvas 1: Create P3
        self.id_scope_mgr.set_scope('canvas_1')
        c1_p3 = id_mgr.generate_place_id()
        
        # Verify each canvas has independent sequence
        self.assertEqual(c1_p1, 'P1')
        self.assertEqual(c1_p2, 'P2')
        self.assertEqual(c1_p3, 'P3')
        
        self.assertEqual(c2_p1, 'P1')
        
        self.assertEqual(c3_p1, 'P1')
        self.assertEqual(c3_p2, 'P2')
        self.assertEqual(c3_p3, 'P3')
        
    def test_close_middle_canvas_preserves_others(self):
        """Test that closing middle canvas doesn't affect others."""
        id_mgr = IDManager()
        
        # Generate IDs in each canvas
        self.id_scope_mgr.set_scope('canvas_1')
        id_mgr.generate_place_id()  # P1
        
        self.id_scope_mgr.set_scope('canvas_2')
        id_mgr.generate_place_id()  # P1
        id_mgr.generate_place_id()  # P2
        
        self.id_scope_mgr.set_scope('canvas_3')
        id_mgr.generate_place_id()  # P1
        
        # Remove middle scope (simulate closing canvas_2)
        self.id_scope_mgr.reset_scope('canvas_2')
        
        # Verify canvas_1 and canvas_3 still work correctly
        self.id_scope_mgr.set_scope('canvas_1')
        p2 = id_mgr.generate_place_id()
        self.assertEqual(p2, 'P2')  # Should continue from P1
        
        self.id_scope_mgr.set_scope('canvas_3')
        p2 = id_mgr.generate_place_id()
        self.assertEqual(p2, 'P2')  # Should continue from P1
        
    def test_reset_canvas_preserves_scope_not_ids(self):
        """Test that reset_canvas resets IDs but preserves canvas."""
        id_mgr = IDManager()
        
        # Generate some IDs
        self.id_scope_mgr.set_scope('test_canvas')
        p1 = id_mgr.generate_place_id()
        p2 = id_mgr.generate_place_id()
        
        self.assertEqual(p1, 'P1')
        self.assertEqual(p2, 'P2')
        
        # Reset scope (simulate File → New on existing tab)
        self.id_scope_mgr.reset_scope('test_canvas')
        
        # IDs should restart from 1
        p1_new = id_mgr.generate_place_id()
        self.assertEqual(p1_new, 'P1')
        
    def test_load_file_with_existing_ids(self):
        """Test loading file that has specific IDs (register_*_id)."""
        id_mgr = IDManager()
        
        self.id_scope_mgr.set_scope('loaded_file')
        
        # Simulate loading file with P1-P5, T1-T3
        id_mgr.register_place_id('P5')
        id_mgr.register_transition_id('T3')
        
        # Next generated IDs should be higher
        p_next = id_mgr.generate_place_id()
        t_next = id_mgr.generate_transition_id()
        
        self.assertEqual(p_next, 'P6')
        self.assertEqual(t_next, 'T4')


class TestPhase4BackwardCompatibility(unittest.TestCase):
    """Test that Phase 4 changes don't break existing code."""
    
    def test_idmanager_works_without_lifecycle(self):
        """Test that IDManager still works when lifecycle not initialized."""
        set_lifecycle_scope_manager(None)
        
        id_mgr = IDManager()
        
        # Should use local counters
        p1 = id_mgr.generate_place_id()
        t1 = id_mgr.generate_transition_id()
        a1 = id_mgr.generate_arc_id()
        
        self.assertEqual(p1, 'P1')
        self.assertEqual(t1, 'T1')
        self.assertEqual(a1, 'A1')
        
    def test_multiple_idmanager_instances_independent(self):
        """Test that multiple IDManager instances work independently without lifecycle."""
        set_lifecycle_scope_manager(None)
        
        id_mgr1 = IDManager()
        id_mgr2 = IDManager()
        
        # Each should have independent counters
        p1_mgr1 = id_mgr1.generate_place_id()
        p1_mgr2 = id_mgr2.generate_place_id()
        
        p2_mgr1 = id_mgr1.generate_place_id()
        p2_mgr2 = id_mgr2.generate_place_id()
        
        self.assertEqual(p1_mgr1, 'P1')
        self.assertEqual(p1_mgr2, 'P1')
        self.assertEqual(p2_mgr1, 'P2')
        self.assertEqual(p2_mgr2, 'P2')


def run_tests():
    """Run all Phase 4 tests with detailed output."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestGlobalIDManagerIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestModelCanvasLoaderIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestMultiCanvasFileOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestPhase4BackwardCompatibility))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*70)
    print("PHASE 4 TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
