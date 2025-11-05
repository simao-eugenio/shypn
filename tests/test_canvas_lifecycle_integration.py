#!/usr/bin/env python3
"""
Integration tests for canvas lifecycle management system.

Tests the coordination between:
- IDScopeManager (scoped ID generation)
- CanvasLifecycleManager (component lifecycle)
- LifecycleAdapter (backward compatibility)
- ModelCanvasLoader integration points

Author: Canvas Lifecycle Team
Date: 2025-01-05
"""

import sys
import unittest
from unittest.mock import Mock, MagicMock, patch
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# Add project root to path
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.canvas.lifecycle import (
    CanvasContext,
    IDScopeManager,
    CanvasLifecycleManager,
    LifecycleAdapter,
    IntegrationHelper
)


class TestIDScopeManager(unittest.TestCase):
    """Test scoped ID generation."""
    
    def setUp(self):
        self.id_manager = IDScopeManager()
        
    def test_default_scope(self):
        """Test ID generation with default scope."""
        place_id = self.id_manager.get_next_id('place')
        self.assertEqual(place_id, 'P1')
        
        transition_id = self.id_manager.get_next_id('transition')
        self.assertEqual(transition_id, 'T1')
        
    def test_scoped_generation(self):
        """Test ID generation with different scopes."""
        # Scope 1
        self.id_manager.set_scope('canvas_1')
        p1 = self.id_manager.get_next_id('place')
        self.assertEqual(p1, 'P1')
        
        # Scope 2
        self.id_manager.set_scope('canvas_2')
        p1_scope2 = self.id_manager.get_next_id('place')
        self.assertEqual(p1_scope2, 'P1')  # Resets for new scope
        
        # Back to scope 1
        self.id_manager.set_scope('canvas_1')
        p2 = self.id_manager.get_next_id('place')
        self.assertEqual(p2, 'P2')  # Continues from where it left off
        
    def test_multiple_entity_types(self):
        """Test different entity types in same scope."""
        self.id_manager.set_scope('test')
        
        self.assertEqual(self.id_manager.get_next_id('place'), 'P1')
        self.assertEqual(self.id_manager.get_next_id('place'), 'P2')
        self.assertEqual(self.id_manager.get_next_id('transition'), 'T1')
        self.assertEqual(self.id_manager.get_next_id('arc'), 'A1')
        self.assertEqual(self.id_manager.get_next_id('place'), 'P3')
        
    def test_reset_scope(self):
        """Test resetting a scope's counters."""
        self.id_manager.set_scope('test')
        self.assertEqual(self.id_manager.get_next_id('place'), 'P1')
        self.assertEqual(self.id_manager.get_next_id('place'), 'P2')
        
        self.id_manager.reset_scope('test')
        self.assertEqual(self.id_manager.get_next_id('place'), 'P1')


class TestCanvasLifecycleManager(unittest.TestCase):
    """Test canvas lifecycle coordination."""
    
    def setUp(self):
        self.manager = CanvasLifecycleManager()
        
    def test_create_canvas(self):
        """Test canvas creation."""
        drawing_area = Mock()
        document_model = Mock()
        
        context = self.manager.create_canvas(
            drawing_area=drawing_area,
            document_model=document_model
        )
        
        self.assertIsNotNone(context)
        self.assertEqual(context.drawing_area, drawing_area)
        self.assertEqual(context.document_model, document_model)
        self.assertIn(drawing_area, self.manager.active_contexts)
        
    def test_switch_canvas(self):
        """Test switching between canvases."""
        da1 = Mock(spec=['id'])
        da2 = Mock(spec=['id'])
        
        ctx1 = self.manager.create_canvas(da1, Mock())
        ctx2 = self.manager.create_canvas(da2, Mock())
        
        # Switch to canvas 2
        result = self.manager.switch_canvas(da2)
        self.assertEqual(result, ctx2)
        
        # Verify ID scope changed
        self.assertEqual(self.manager.id_manager.current_scope, ctx2.id_scope)
        
    def test_destroy_canvas(self):
        """Test canvas destruction."""
        drawing_area = Mock()
        self.manager.create_canvas(drawing_area, Mock())
        
        success = self.manager.destroy_canvas(drawing_area)
        self.assertTrue(success)
        self.assertNotIn(drawing_area, self.manager.active_contexts)
        
    def test_reset_canvas(self):
        """Test canvas reset."""
        drawing_area = Mock()
        context = self.manager.create_canvas(drawing_area, Mock())
        
        # Generate some IDs
        self.manager.id_manager.get_next_id('place')
        self.manager.id_manager.get_next_id('place')
        
        # Reset
        self.manager.reset_canvas(drawing_area)
        
        # Should start from 1 again
        next_id = self.manager.id_manager.get_next_id('place')
        self.assertEqual(next_id, 'P1')


class TestLifecycleAdapter(unittest.TestCase):
    """Test backward compatibility adapter."""
    
    def setUp(self):
        self.lifecycle_manager = CanvasLifecycleManager()
        self.adapter = LifecycleAdapter(self.lifecycle_manager)
        
    def test_register_canvas(self):
        """Test registering existing canvas with lifecycle system."""
        drawing_area = Mock()
        document_model = Mock()
        controller = Mock()
        palette = Mock()
        
        self.adapter.register_canvas(
            drawing_area,
            document_model,
            controller,
            palette
        )
        
        # Verify registration
        context = self.adapter.get_canvas_context(drawing_area)
        self.assertIsNotNone(context)
        self.assertEqual(context.document_model, document_model)
        self.assertEqual(context.controller, controller)
        self.assertEqual(context.palette, palette)
        
    def test_switch_to_canvas(self):
        """Test adapter canvas switching."""
        da1 = Mock()
        da2 = Mock()
        
        self.adapter.register_canvas(da1, Mock(), Mock(), Mock())
        self.adapter.register_canvas(da2, Mock(), Mock(), Mock())
        
        result = self.adapter.switch_to_canvas(da2)
        self.assertIsNotNone(result)
        
    def test_destroy_canvas(self):
        """Test adapter canvas destruction."""
        drawing_area = Mock()
        self.adapter.register_canvas(drawing_area, Mock(), Mock(), Mock())
        
        success = self.adapter.destroy_canvas(drawing_area)
        self.assertTrue(success)
        
        context = self.adapter.get_canvas_context(drawing_area)
        self.assertIsNone(context)


class TestIntegrationHelper(unittest.TestCase):
    """Test integration helper utilities."""
    
    def setUp(self):
        self.helper = IntegrationHelper()
        
    def test_validate_canvas_components(self):
        """Test component validation."""
        drawing_area = Mock()
        document_model = Mock()
        
        # Valid components
        is_valid = self.helper.validate_canvas_components(
            drawing_area,
            document_model
        )
        self.assertTrue(is_valid)
        
        # Invalid (None) components
        is_valid = self.helper.validate_canvas_components(
            None,
            document_model
        )
        self.assertFalse(is_valid)
        
    def test_safe_canvas_creation(self):
        """Test safe canvas creation with validation."""
        manager = CanvasLifecycleManager()
        drawing_area = Mock()
        document_model = Mock()
        
        context = self.helper.create_canvas_safely(
            manager,
            drawing_area,
            document_model
        )
        
        self.assertIsNotNone(context)
        self.assertEqual(context.drawing_area, drawing_area)


class TestMultiCanvasScenarios(unittest.TestCase):
    """Test realistic multi-canvas scenarios."""
    
    def setUp(self):
        self.manager = CanvasLifecycleManager()
        self.adapter = LifecycleAdapter(self.manager)
        
    def test_three_canvases_independent_ids(self):
        """Test that three canvases have independent ID sequences."""
        da1 = Mock(spec=['id'])
        da2 = Mock(spec=['id'])
        da3 = Mock(spec=['id'])
        
        # Create three canvases
        ctx1 = self.manager.create_canvas(da1, Mock())
        ctx2 = self.manager.create_canvas(da2, Mock())
        ctx3 = self.manager.create_canvas(da3, Mock())
        
        # Generate IDs in canvas 1
        self.manager.switch_canvas(da1)
        p1_c1 = self.manager.id_manager.get_next_id('place')
        p2_c1 = self.manager.id_manager.get_next_id('place')
        
        # Generate IDs in canvas 2
        self.manager.switch_canvas(da2)
        p1_c2 = self.manager.id_manager.get_next_id('place')
        
        # Generate IDs in canvas 3
        self.manager.switch_canvas(da3)
        p1_c3 = self.manager.id_manager.get_next_id('place')
        p2_c3 = self.manager.id_manager.get_next_id('place')
        p3_c3 = self.manager.id_manager.get_next_id('place')
        
        # Back to canvas 1
        self.manager.switch_canvas(da1)
        p3_c1 = self.manager.id_manager.get_next_id('place')
        
        # Verify independence
        self.assertEqual(p1_c1, 'P1')
        self.assertEqual(p2_c1, 'P2')
        self.assertEqual(p3_c1, 'P3')  # Should continue from P2
        
        self.assertEqual(p1_c2, 'P1')
        
        self.assertEqual(p1_c3, 'P1')
        self.assertEqual(p2_c3, 'P2')
        self.assertEqual(p3_c3, 'P3')
        
    def test_canvas_destruction_preserves_others(self):
        """Test that destroying one canvas doesn't affect others."""
        da1 = Mock(spec=['id'])
        da2 = Mock(spec=['id'])
        
        ctx1 = self.manager.create_canvas(da1, Mock())
        ctx2 = self.manager.create_canvas(da2, Mock())
        
        # Generate IDs in both
        self.manager.switch_canvas(da1)
        self.manager.id_manager.get_next_id('place')
        
        self.manager.switch_canvas(da2)
        self.manager.id_manager.get_next_id('place')
        self.manager.id_manager.get_next_id('place')
        
        # Destroy canvas 1
        self.manager.destroy_canvas(da1)
        
        # Canvas 2 should still work
        self.manager.switch_canvas(da2)
        p3 = self.manager.id_manager.get_next_id('place')
        self.assertEqual(p3, 'P3')
        
        # Canvas 1 should be gone
        self.assertNotIn(da1, self.manager.active_contexts)
        self.assertIn(da2, self.manager.active_contexts)


def run_tests():
    """Run all tests with detailed output."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestIDScopeManager))
    suite.addTests(loader.loadTestsFromTestCase(TestCanvasLifecycleManager))
    suite.addTests(loader.loadTestsFromTestCase(TestLifecycleAdapter))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationHelper))
    suite.addTests(loader.loadTestsFromTestCase(TestMultiCanvasScenarios))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
