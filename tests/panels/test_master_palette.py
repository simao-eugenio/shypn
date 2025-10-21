"""Unit tests for MasterPalette and PaletteButton classes."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.ui.master_palette import MasterPalette
from shypn.ui.palette_button import PaletteButton


class TestPaletteButton:
    """Test PaletteButton class."""

    def test_button_creation(self):
        """Test basic button creation."""
        pb = PaletteButton('test', 'folder-symbolic', 'Test tooltip')
        assert pb.name == 'test'
        assert pb.icon_name == 'folder-symbolic'
        assert pb.tooltip == 'Test tooltip'
        assert isinstance(pb.widget, Gtk.ToggleButton)

    def test_button_active_state(self):
        """Test get/set active."""
        pb = PaletteButton('test', 'folder-symbolic', 'Test')
        assert pb.get_active() == False
        pb.set_active(True)
        assert pb.get_active() == True
        pb.set_active(False)
        assert pb.get_active() == False

    def test_button_sensitive(self):
        """Test enable/disable."""
        pb = PaletteButton('test', 'folder-symbolic', 'Test')
        assert pb.widget.get_sensitive() == True
        pb.set_sensitive(False)
        assert pb.widget.get_sensitive() == False
        pb.set_sensitive(True)
        assert pb.widget.get_sensitive() == True

    def test_button_callback(self):
        """Test toggled callback."""
        pb = PaletteButton('test', 'folder-symbolic', 'Test')
        callback_result = []
        
        def on_toggle(active):
            callback_result.append(active)
        
        pb.connect_toggled(on_toggle)
        pb.set_active(True)
        assert len(callback_result) == 1
        assert callback_result[0] == True


class TestMasterPalette:
    """Test MasterPalette class."""

    def test_palette_creation(self):
        """Test basic palette creation."""
        mp = MasterPalette()
        widget = mp.get_widget()
        assert isinstance(widget, Gtk.Widget)
        assert widget.get_orientation() == Gtk.Orientation.VERTICAL

    def test_buttons_present(self):
        """Test all expected buttons are created."""
        mp = MasterPalette()
        assert 'files' in mp.buttons
        assert 'analyses' in mp.buttons
        assert 'pathways' in mp.buttons
        assert 'topology' in mp.buttons
        assert len(mp.buttons) == 4

    def test_button_order(self):
        """Test buttons are in expected order."""
        mp = MasterPalette()
        button_names = list(mp.buttons.keys())
        assert button_names == ['files', 'pathways', 'analyses', 'topology']

    def test_topology_disabled_by_default(self):
        """Test topology button is disabled on startup."""
        mp = MasterPalette()
        assert mp.buttons['topology'].widget.get_sensitive() == False

    def test_connect_callback(self):
        """Test connecting callbacks to buttons."""
        mp = MasterPalette()
        callback_result = []
        
        def on_files_toggle(active):
            callback_result.append(('files', active))
        
        mp.connect('files', on_files_toggle)
        mp.set_active('files', True)
        
        assert len(callback_result) == 1
        assert callback_result[0] == ('files', True)

    def test_set_sensitive(self):
        """Test enabling/disabling buttons."""
        mp = MasterPalette()
        mp.set_sensitive('topology', True)
        assert mp.buttons['topology'].widget.get_sensitive() == True
        mp.set_sensitive('topology', False)
        assert mp.buttons['topology'].widget.get_sensitive() == False


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
