#!/usr/bin/env python3
"""
Unit tests for WaylandParentManager.

Tests parent window tracking, state monitoring, and Wayland safety validation.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.helpers.wayland_parent_manager import WaylandParentManager


class TestWaylandParentManager(unittest.TestCase):
    """Test cases for WaylandParentManager."""
    
    def setUp(self):
        """Reset singleton before each test."""
        WaylandParentManager.reset_instance()
        self.manager = WaylandParentManager.get_instance()
    
    def tearDown(self):
        """Clean up after each test."""
        WaylandParentManager.reset_instance()
    
    def test_singleton_pattern(self):
        """Test that get_instance() returns same instance."""
        mgr1 = WaylandParentManager.get_instance()
        mgr2 = WaylandParentManager.get_instance()
        self.assertIs(mgr1, mgr2, "Should return same instance")
    
    def test_reset_instance(self):
        """Test that reset_instance() creates new instance."""
        mgr1 = WaylandParentManager.get_instance()
        WaylandParentManager.reset_instance()
        mgr2 = WaylandParentManager.get_instance()
        self.assertIsNot(mgr1, mgr2, "Should create new instance after reset")
    
    def test_register_parent_basic(self):
        """Test basic parent registration."""
        parent = Mock(spec=Gtk.Window)
        parent.get_mapped.return_value = True
        parent.get_realized.return_value = True
        parent.connect.return_value = 123  # Signal handler ID
        
        document_id = 42
        self.manager.register_parent(document_id, parent)
        
        # Verify signal connections
        self.assertEqual(parent.connect.call_count, 4, "Should connect 4 signals")
        
        # Verify parent is tracked
        self.assertIn(document_id, self.manager.get_all_document_ids())
    
    def test_register_parent_overwrites_existing(self):
        """Test that re-registering a document overwrites old parent."""
        parent1 = Mock(spec=Gtk.Window)
        parent1.get_mapped.return_value = True
        parent1.get_realized.return_value = True
        parent1.connect.return_value = 1
        parent1.disconnect = Mock()
        
        parent2 = Mock(spec=Gtk.Window)
        parent2.get_mapped.return_value = True
        parent2.get_realized.return_value = True
        parent2.connect.return_value = 2
        
        document_id = 42
        
        # Register first parent
        self.manager.register_parent(document_id, parent1)
        
        # Register second parent (should disconnect first)
        self.manager.register_parent(document_id, parent2)
        
        # Verify first parent was disconnected
        self.assertEqual(parent1.disconnect.call_count, 4, "Should disconnect 4 signals from old parent")
        
        # Verify only one document tracked
        self.assertEqual(len(self.manager.get_all_document_ids()), 1)
    
    def test_unregister_parent(self):
        """Test parent unregistration."""
        parent = Mock(spec=Gtk.Window)
        parent.get_mapped.return_value = True
        parent.get_realized.return_value = True
        parent.connect.return_value = 123
        parent.disconnect = Mock()
        
        document_id = 42
        self.manager.register_parent(document_id, parent)
        self.manager.unregister_parent(document_id)
        
        # Verify signals disconnected
        self.assertEqual(parent.disconnect.call_count, 4, "Should disconnect 4 signals")
        
        # Verify parent no longer tracked
        self.assertNotIn(document_id, self.manager.get_all_document_ids())
    
    def test_unregister_nonexistent_parent(self):
        """Test unregistering a document that doesn't exist (should not crash)."""
        self.manager.unregister_parent(999)  # Should not raise exception
    
    def test_get_active_parent_ready(self):
        """Test get_active_parent returns parent when ready."""
        parent = Mock(spec=Gtk.Window)
        parent.get_mapped.return_value = True
        parent.get_realized.return_value = True
        parent.connect.return_value = 123
        
        document_id = 42
        self.manager.register_parent(document_id, parent)
        
        result = self.manager.get_active_parent(document_id)
        self.assertIs(result, parent, "Should return parent when ready")
    
    def test_get_active_parent_not_mapped(self):
        """Test get_active_parent returns None when parent not mapped."""
        parent = Mock(spec=Gtk.Window)
        parent.get_mapped.return_value = False  # Not mapped
        parent.get_realized.return_value = True
        parent.connect.return_value = 123
        
        document_id = 42
        self.manager.register_parent(document_id, parent)
        
        result = self.manager.get_active_parent(document_id)
        self.assertIsNone(result, "Should return None when parent not mapped")
    
    def test_get_active_parent_not_realized(self):
        """Test get_active_parent returns None when parent not realized."""
        parent = Mock(spec=Gtk.Window)
        parent.get_mapped.return_value = True
        parent.get_realized.return_value = False  # Not realized
        parent.connect.return_value = 123
        
        document_id = 42
        self.manager.register_parent(document_id, parent)
        
        result = self.manager.get_active_parent(document_id)
        self.assertIsNone(result, "Should return None when parent not realized")
    
    def test_get_active_parent_nonexistent_document(self):
        """Test get_active_parent returns None for unregistered document."""
        result = self.manager.get_active_parent(999)
        self.assertIsNone(result, "Should return None for nonexistent document")
    
    def test_get_parent_unsafe(self):
        """Test get_parent_unsafe returns parent regardless of state."""
        parent = Mock(spec=Gtk.Window)
        parent.get_mapped.return_value = False
        parent.get_realized.return_value = False
        parent.connect.return_value = 123
        
        document_id = 42
        self.manager.register_parent(document_id, parent)
        
        # get_active_parent should return None
        self.assertIsNone(self.manager.get_active_parent(document_id))
        
        # get_parent_unsafe should return parent anyway
        result = self.manager.get_parent_unsafe(document_id)
        self.assertIs(result, parent, "get_parent_unsafe should return parent even when not ready")
    
    def test_is_parent_ready_true(self):
        """Test is_parent_ready returns True when ready."""
        parent = Mock(spec=Gtk.Window)
        parent.get_mapped.return_value = True
        parent.get_realized.return_value = True
        parent.connect.return_value = 123
        
        document_id = 42
        self.manager.register_parent(document_id, parent)
        
        self.assertTrue(self.manager.is_parent_ready(document_id))
    
    def test_is_parent_ready_false(self):
        """Test is_parent_ready returns False when not ready."""
        parent = Mock(spec=Gtk.Window)
        parent.get_mapped.return_value = False
        parent.get_realized.return_value = True
        parent.connect.return_value = 123
        
        document_id = 42
        self.manager.register_parent(document_id, parent)
        
        self.assertFalse(self.manager.is_parent_ready(document_id))
    
    def test_is_parent_ready_nonexistent(self):
        """Test is_parent_ready returns False for nonexistent document."""
        self.assertFalse(self.manager.is_parent_ready(999))
    
    def test_get_all_document_ids(self):
        """Test get_all_document_ids returns all registered IDs."""
        parent1 = Mock(spec=Gtk.Window)
        parent1.get_mapped.return_value = True
        parent1.get_realized.return_value = True
        parent1.connect.return_value = 1
        
        parent2 = Mock(spec=Gtk.Window)
        parent2.get_mapped.return_value = True
        parent2.get_realized.return_value = True
        parent2.connect.return_value = 2
        
        self.manager.register_parent(1, parent1)
        self.manager.register_parent(2, parent2)
        
        doc_ids = self.manager.get_all_document_ids()
        self.assertEqual(set(doc_ids), {1, 2}, "Should return all document IDs")
    
    def test_state_tracking_map_signal(self):
        """Test that map signal updates state correctly."""
        parent = Mock(spec=Gtk.Window)
        parent.get_mapped.return_value = False  # Initially not mapped
        parent.get_realized.return_value = True
        
        map_callback = None
        def connect_side_effect(signal_name, callback, *args):
            nonlocal map_callback
            if signal_name == 'map':
                map_callback = callback
            return 123
        
        parent.connect.side_effect = connect_side_effect
        
        document_id = 42
        self.manager.register_parent(document_id, parent)
        
        # Initially not ready
        self.assertFalse(self.manager.is_parent_ready(document_id))
        
        # Simulate map signal
        self.assertIsNotNone(map_callback, "Should have captured map callback")
        map_callback(parent, id(parent))
        
        # Now should be ready (mapped + realized)
        self.assertTrue(self.manager.is_parent_ready(document_id))
    
    def test_get_debug_info(self):
        """Test get_debug_info returns tracking state."""
        parent = Mock(spec=Gtk.Window)
        parent.get_mapped.return_value = True
        parent.get_realized.return_value = True
        parent.connect.return_value = 123
        
        document_id = 42
        self.manager.register_parent(document_id, parent)
        
        debug_info = self.manager.get_debug_info()
        
        self.assertEqual(debug_info['active_parents'], 1)
        self.assertIn(document_id, debug_info['documents'])
        
        doc_info = debug_info['documents'][document_id]
        self.assertTrue(doc_info['mapped'])
        self.assertTrue(doc_info['realized'])
        self.assertTrue(doc_info['ready'])


if __name__ == '__main__':
    unittest.main()
