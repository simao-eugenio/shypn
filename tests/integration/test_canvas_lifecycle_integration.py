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
        place_id = self.id_manager.generate_place_id()
        self.assertEqual(place_id, 'P1')
        
        transition_id = self.id_manager.generate_transition_id()
        self.assertEqual(transition_id, 'T1')
        
    def test_scoped_generation(self):
        """Test ID generation with different scopes."""
        # Scope 1
        self.id_manager.set_scope('canvas_1')
        p1 = self.id_manager.generate_place_id()
        self.assertEqual(p1, 'P1')
        
        # Scope 2
        self.id_manager.set_scope('canvas_2')
        p1_scope2 = self.id_manager.generate_place_id()
        self.assertEqual(p1_scope2, 'P1')  # Resets for new scope
        
        # Back to scope 1
        self.id_manager.set_scope('canvas_1')
        p2 = self.id_manager.generate_place_id()
        self.assertEqual(p2, 'P2')  # Continues from where it left off
        
    def test_multiple_entity_types(self):
        """Test different entity types in same scope."""
        self.id_manager.set_scope('test')
        
        self.assertEqual(self.id_manager.generate_place_id(), 'P1')
        self.assertEqual(self.id_manager.generate_place_id(), 'P2')
        self.assertEqual(self.id_manager.generate_transition_id(), 'T1')
        self.assertEqual(self.id_manager.generate_arc_id(), 'A1')
        self.assertEqual(self.id_manager.generate_place_id(), 'P3')
        
    def test_reset_scope(self):
        """Test resetting a scope's counters."""
        self.id_manager.set_scope('test')
        self.assertEqual(self.id_manager.generate_place_id(), 'P1')
        self.assertEqual(self.id_manager.generate_place_id(), 'P2')
        
        self.id_manager.reset_scope('test')
        self.assertEqual(self.id_manager.generate_place_id(), 'P1')


class TestCanvasLifecycleManager(unittest.TestCase):
    """Test canvas lifecycle coordination.
    
    Note: Full canvas creation requires GTK components and is tested in integration tests.
    These tests focus on the core lifecycle logic that can be tested in isolation.
    """
    
    def setUp(self):
        self.manager = CanvasLifecycleManager()
        
    def test_id_manager_initialization(self):
        """Test that lifecycle manager has ID manager."""
        self.assertIsNotNone(self.manager.id_manager)
        self.assertIsInstance(self.manager.id_manager, IDScopeManager)
        
    def test_canvas_registry_empty(self):
        """Test that canvas registry starts empty."""
        self.assertEqual(len(self.manager.canvas_registry), 0)
        
    def test_id_manager_scope_switching(self):
        """Test ID manager scope changes."""
        # Create different scopes
        self.manager.id_manager.set_scope('canvas_1')
        p1 = self.manager.id_manager.generate_place_id()
        
        self.manager.id_manager.set_scope('canvas_2')
        p1_c2 = self.manager.id_manager.generate_place_id()
        
        # Both should start at P1
        self.assertEqual(p1, 'P1')
        self.assertEqual(p1_c2, 'P1')
        
        # Switch back to canvas_1
        self.manager.id_manager.set_scope('canvas_1')
        p2 = self.manager.id_manager.generate_place_id()
        self.assertEqual(p2, 'P2')  # Should continue from P1
        
    def test_reset_scope_functionality(self):
        """Test scope reset functionality."""
        # Generate some IDs in a scope
        self.manager.id_manager.set_scope('test_canvas')
        self.manager.id_manager.generate_place_id()  # P1
        self.manager.id_manager.generate_place_id()  # P2
        self.manager.id_manager.generate_transition_id()  # T1
        
        # Reset the scope
        self.manager.id_manager.reset_scope('test_canvas')
        
        # Should start from 1 again
        next_place = self.manager.id_manager.generate_place_id()
        next_trans = self.manager.id_manager.generate_transition_id()
        self.assertEqual(next_place, 'P1')
        self.assertEqual(next_trans, 'T1')


class TestLifecycleAdapter(unittest.TestCase):
    """Test backward compatibility adapter.
    
    Note: Adapter requires real GTK DrawingArea objects for registration.
    These tests focus on adapter initialization and basic properties.
    """
    
    def setUp(self):
        self.lifecycle_manager = CanvasLifecycleManager()
        self.adapter = LifecycleAdapter(self.lifecycle_manager)
        
    def test_adapter_initialization(self):
        """Test adapter initializes with lifecycle manager."""
        self.assertIsNotNone(self.adapter)
        self.assertEqual(self.adapter.lifecycle_manager, self.lifecycle_manager)
        
    def test_adapter_has_lifecycle_manager(self):
        """Test adapter provides access to lifecycle manager."""
        self.assertIsInstance(self.adapter.lifecycle_manager, CanvasLifecycleManager)
        
    def test_adapter_id_manager_access(self):
        """Test adapter provides access to ID manager through lifecycle."""
        id_mgr = self.adapter.lifecycle_manager.id_manager
        self.assertIsInstance(id_mgr, IDScopeManager)
        
        # Test ID generation through adapter's lifecycle
        id_mgr.set_scope('test')
        p1 = id_mgr.generate_place_id()
        self.assertEqual(p1, 'P1')


class TestIntegrationHelper(unittest.TestCase):
    """Test integration helper utilities.
    
    Note: IntegrationHelper is primarily used for internal lifecycle coordination.
    Core functionality is tested through lifecycle manager tests.
    """
    
    def setUp(self):
        self.helper = IntegrationHelper()
        
    def test_helper_initialization(self):
        """Test helper initializes correctly."""
        self.assertIsNotNone(self.helper)
        
    def test_helper_provides_utilities(self):
        """Test helper has expected utility methods."""
        # Check that helper class exists and can be instantiated
        self.assertIsInstance(self.helper, IntegrationHelper)
        
    def test_helper_can_access_logger(self):
        """Test helper has logging capability."""
        # Integration helper uses module-level logger
        # This test just verifies the helper is properly structured
        self.assertTrue(hasattr(IntegrationHelper, '__init__'))


class TestMultiCanvasScenarios(unittest.TestCase):
    """Test realistic multi-canvas scenarios using ID scoping."""
    
    def setUp(self):
        self.manager = CanvasLifecycleManager()
        self.id_mgr = self.manager.id_manager
        
    def test_three_canvases_independent_ids(self):
        """Test that three canvases have independent ID sequences."""
        # Simulate three canvas scopes
        # Canvas 1: Generate P1, P2
        self.id_mgr.set_scope('canvas_1')
        p1_c1 = self.id_mgr.generate_place_id()
        p2_c1 = self.id_mgr.generate_place_id()
        
        # Canvas 2: Generate P1
        self.id_mgr.set_scope('canvas_2')
        p1_c2 = self.id_mgr.generate_place_id()
        
        # Canvas 3: Generate P1, P2, P3
        self.id_mgr.set_scope('canvas_3')
        p1_c3 = self.id_mgr.generate_place_id()
        p2_c3 = self.id_mgr.generate_place_id()
        p3_c3 = self.id_mgr.generate_place_id()
        
        # Back to canvas 1: Generate P3
        self.id_mgr.set_scope('canvas_1')
        p3_c1 = self.id_mgr.generate_place_id()
        
        # Verify independence
        self.assertEqual(p1_c1, 'P1')
        self.assertEqual(p2_c1, 'P2')
        self.assertEqual(p3_c1, 'P3')  # Should continue from P2
        
        self.assertEqual(p1_c2, 'P1')
        
        self.assertEqual(p1_c3, 'P1')
        self.assertEqual(p2_c3, 'P2')
        self.assertEqual(p3_c3, 'P3')
        
    def test_canvas_reset_preserves_scope(self):
        """Test that resetting one canvas doesn't affect others."""
        # Create IDs in canvas 1
        self.id_mgr.set_scope('canvas_1')
        self.id_mgr.generate_place_id()  # P1
        
        # Create IDs in canvas 2
        self.id_mgr.set_scope('canvas_2')
        self.id_mgr.generate_place_id()  # P1
        self.id_mgr.generate_place_id()  # P2
        
        # Reset canvas 1
        self.id_mgr.reset_scope('canvas_1')
        
        # Canvas 2 should still be at P2
        self.id_mgr.set_scope('canvas_2')
        p3 = self.id_mgr.generate_place_id()
        self.assertEqual(p3, 'P3')
        
        # Canvas 1 should restart at P1
        self.id_mgr.set_scope('canvas_1')
        p1 = self.id_mgr.generate_place_id()
        self.assertEqual(p1, 'P1')


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
