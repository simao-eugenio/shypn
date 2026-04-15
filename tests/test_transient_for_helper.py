#!/usr/bin/env python3
"""
Unit tests for TransientForHelper.

Tests safe transient dialog presentation with Wayland compatibility.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib

from shypn.helpers.transient_for_helper import TransientForHelper


class TestTransientForHelper(unittest.TestCase):
    """Test cases for TransientForHelper."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.dialog = Mock(spec=Gtk.Dialog)
        self.parent = Mock(spec=Gtk.Window)
   
    def test_present_dialog_no_parent(self):
        """Test presenting dialog without parent (simple case)."""
        result = TransientForHelper.present_dialog(self.dialog, None)
        
        self.assertTrue(result, "Should return True for immediate presentation")
        self.dialog.present.assert_called_once()
        self.dialog.set_transient_for.assert_not_called()
    
    def test_present_dialog_ready_parent(self):
        """Test presenting dialog with ready parent (mapped + realized)."""
        self.parent.get_mapped.return_value = True
        self.parent.get_realized.return_value = True
        
        result = TransientForHelper.present_dialog(self.dialog, self.parent)
        
        self.assertTrue(result, "Should return True for immediate presentation")
        self.dialog.set_transient_for.assert_called_once_with(self.parent)
        self.dialog.present.assert_called_once()
    
    @patch('shypn.helpers.transient_for_helper.GLib.timeout_add')
    def test_present_dialog_not_mapped(self, mock_timeout):
        """Test presenting dialog when parent not mapped (deferred)."""
        self.parent.get_mapped.return_value = False
        self.parent.get_realized.return_value = True
        
        result = TransientForHelper.present_dialog(self.dialog, self.parent, delay_ms=50)
        
        self.assertFalse(result, "Should return False for deferred presentation")
        mock_timeout.assert_called_once()
        
        # Verify timeout args
        args = mock_timeout.call_args[0]
        self.assertEqual(args[0], 50, "Should use specified delay")
        self.assertEqual(args[1], TransientForHelper._delayed_present)
        self.assertIs(args[2], self.dialog)
        self.assertIs(args[3], self.parent)
    
    @patch('shypn.helpers.transient_for_helper.GLib.timeout_add')
    def test_present_dialog_not_realized(self, mock_timeout):
        """Test presenting dialog when parent not realized (deferred)."""
        self.parent.get_mapped.return_value = True
        self.parent.get_realized.return_value = False
        
        result = TransientForHelper.present_dialog(self.dialog, self.parent)
        
        self.assertFalse(result, "Should return False for deferred presentation")
        mock_timeout.assert_called_once()
    
    def test_present_dialog_safe_no_parent(self):
        """Test present_dialog_safe without parent."""
        result = TransientForHelper.present_dialog_safe(self.dialog, None)
        
        self.assertTrue(result)
        self.dialog.present.assert_called_once()
    
    @patch.object(TransientForHelper, '_handle_window_state_transitions')
    @patch.object(TransientForHelper, '_sync_compositor')
    def test_present_dialog_safe_with_parent(self, mock_sync, mock_handle_state):
        """Test present_dialog_safe with parent and safety checks."""
        self.parent.get_mapped.return_value = True
        self.parent.get_realized.return_value = True
        
        result = TransientForHelper.present_dialog_safe(
            self.dialog, self.parent, sync_compositor=True
        )
        
        self.assertTrue(result)
        mock_handle_state.assert_called_once_with(self.parent)
        mock_sync.assert_called_once()
        self.dialog.set_transient_for.assert_called_once_with(self.parent)
        self.dialog.present.assert_called_once()
    
    @patch.object(TransientForHelper, '_sync_compositor')
    @patch.object(TransientForHelper, '_handle_window_state_transitions')
    def test_present_dialog_safe_no_sync(self, mock_handle_state, mock_sync):
        """Test present_dialog_safe without compositor sync."""
        self.parent.get_mapped.return_value = True
        self.parent.get_realized.return_value = True
        
        TransientForHelper.present_dialog_safe(
            self.dialog, self.parent, sync_compositor=False
        )
        
        mock_handle_state.assert_called_once_with(self.parent)
        mock_sync.assert_not_called()
    
    def test_present_immediate_success(self):
        """Test successful immediate presentation."""
        result = TransientForHelper._present_immediate(self.dialog, self.parent)
        
        self.assertTrue(result)
        self.dialog.set_transient_for.assert_called_once_with(self.parent)
        self.dialog.present.assert_called_once()
    
    def test_present_immediate_exception_fallback(self):
        """Test fallback when set_transient_for raises exception."""
        self.dialog.set_transient_for.side_effect = Exception("Wayland error")
        
        result = TransientForHelper._present_immediate(self.dialog, self.parent)
        
        # Should still present (without transient)
        self.assertTrue(result)
        self.dialog.present.assert_called_once()
    
    def test_delayed_present_ready(self):
        """Test delayed present when parent becomes ready."""
        self.parent.get_mapped.return_value = True
        self.parent.get_realized.return_value = True
        
        result = TransientForHelper._delayed_present(
            self.dialog, self.parent, delay_ms=50, retries_left=3
        )
        
        self.assertFalse(result, "Should return False to stop timeout repeat")
        self.dialog.set_transient_for.assert_called_once_with(self.parent)
        self.dialog.present.assert_called_once()
    
    @patch('shypn.helpers.transient_for_helper.GLib.timeout_add')
    def test_delayed_present_retry(self, mock_timeout):
        """Test delayed present retries when parent still not ready."""
        self.parent.get_mapped.return_value = False
        self.parent.get_realized.return_value = True
        
        result = TransientForHelper._delayed_present(
            self.dialog, self.parent, delay_ms=50, retries_left=2
        )
        
        self.assertFalse(result, "Should return False to stop timeout repeat")
        mock_timeout.assert_called_once()
        
        # Verify retry scheduled with decremented count
        # GLib.timeout_add(delay, callback, dialog, parent, delay, retries_left-1)
        call_args = mock_timeout.call_args
        self.assertEqual(call_args[0][0], 50, "Should use same delay")
        self.assertEqual(call_args[0][1], TransientForHelper._delayed_present)
        self.assertIs(call_args[0][2], self.dialog)
        self.assertIs(call_args[0][3], self.parent)
        self.assertEqual(call_args[0][4], 50, "Should pass delay_ms")
        self.assertEqual(call_args[0][5], 1, "Should decrement retries_left")
    
    def test_delayed_present_give_up(self):
        """Test delayed present gives up after max retries."""
        self.parent.get_mapped.return_value = False
        self.parent.get_realized.return_value = True
        
        result = TransientForHelper._delayed_present(
            self.dialog, self.parent, delay_ms=50, retries_left=0
        )
        
        self.assertFalse(result, "Should return False to stop timeout repeat")
        # Should present without transient parent
        self.dialog.present.assert_called_once()
        self.dialog.set_transient_for.assert_not_called()
    
    @patch('time.sleep')
    def test_handle_window_state_transitions_maximized(self, mock_sleep):
        """Test delay added for maximized window."""
        gdk_window = Mock()
        gdk_window.get_state.return_value = Gdk.WindowState.MAXIMIZED
        self.parent.get_window.return_value = gdk_window
        
        TransientForHelper._handle_window_state_transitions(self.parent)
        
        mock_sleep.assert_called_once_with(0.1)
    
    @patch('time.sleep')
    def test_handle_window_state_transitions_fullscreen(self, mock_sleep):
        """Test delay added for fullscreen window."""
        gdk_window = Mock()
        gdk_window.get_state.return_value = Gdk.WindowState.FULLSCREEN
        self.parent.get_window.return_value = gdk_window
        
        TransientForHelper._handle_window_state_transitions(self.parent)
        
        mock_sleep.assert_called_once_with(0.1)
    
    @patch('time.sleep')
    def test_handle_window_state_transitions_normal(self, mock_sleep):
        """Test no delay for normal window state."""
        gdk_window = Mock()
        gdk_window.get_state.return_value = 0  # No special state
        self.parent.get_window.return_value = gdk_window
        
        TransientForHelper._handle_window_state_transitions(self.parent)
        
        mock_sleep.assert_not_called()
    
    def test_handle_window_state_transitions_no_window(self):
        """Test handling when get_window() returns None."""
        self.parent.get_window.return_value = None
        
        # Should not crash
        TransientForHelper._handle_window_state_transitions(self.parent)
    
    @patch('shypn.helpers.transient_for_helper.Gdk.Display.get_default')
    def test_sync_compositor(self, mock_get_display):
        """Test compositor sync."""
        mock_display = Mock()
        mock_get_display.return_value = mock_display
        
        TransientForHelper._sync_compositor()
        
        mock_display.sync.assert_called_once()
    
    @patch('shypn.helpers.transient_for_helper.Gdk.Display.get_default')
    def test_sync_compositor_no_display(self, mock_get_display):
        """Test compositor sync when no display available."""
        mock_get_display.return_value = None
        
        # Should not crash
        TransientForHelper._sync_compositor()
    
    def test_set_transient_safe_no_parent(self):
        """Test set_transient_safe with no parent."""
        result = TransientForHelper.set_transient_safe(self.dialog, None)
        
        self.assertFalse(result)
        self.dialog.set_transient_for.assert_not_called()
    
    def test_set_transient_safe_ready_parent(self):
        """Test set_transient_safe with ready parent."""
        self.parent.get_mapped.return_value = True
        self.parent.get_realized.return_value = True
        
        result = TransientForHelper.set_transient_safe(self.dialog, self.parent)
        
        self.assertTrue(result)
        self.dialog.set_transient_for.assert_called_once_with(self.parent)
    
    def test_set_transient_safe_not_ready(self):
        """Test set_transient_safe with not ready parent."""
        self.parent.get_mapped.return_value = False
        self.parent.get_realized.return_value = True
        
        result = TransientForHelper.set_transient_safe(self.dialog, self.parent)
        
        self.assertFalse(result)
        self.dialog.set_transient_for.assert_not_called()
    
    def test_set_transient_safe_exception(self):
        """Test set_transient_safe handles exceptions."""
        self.parent.get_mapped.return_value = True
        self.parent.get_realized.return_value = True
        self.dialog.set_transient_for.side_effect = Exception("Error")
        
        result = TransientForHelper.set_transient_safe(self.dialog, self.parent)
        
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
