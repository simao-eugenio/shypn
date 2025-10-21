#!/usr/bin/env python3
"""Test FileChooser from actual application context."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.helpers.left_panel_loader import create_left_panel
from shypn.file.netobj_persistency import NetObjPersistency

def test_from_app_context():
    """Test FileChooser in the actual application context."""
    print("Creating main window...")
    window = Gtk.Window(title="Test Main Window")
    window.set_default_size(800, 600)
    
    print("Creating persistency manager with parent window...")
    persistency = NetObjPersistency(parent_window=window)
    
    print("Creating left panel...")
    left_panel = create_left_panel()
    
    print("Getting file explorer from panel...")
    file_explorer = left_panel.file_explorer
    
    if file_explorer:
        print("Setting parent window on file_explorer...")
        file_explorer.set_parent_window(window)
        
        print("Setting persistency manager on file_explorer...")
        file_explorer.set_persistency_manager(persistency)
        
        # Verify wiring
        print(f"file_explorer.parent_window: {file_explorer.parent_window}")
        print(f"file_explorer.persistency: {file_explorer.persistency}")
        print(f"file_explorer.persistency.parent_window: {file_explorer.persistency.parent_window}")
        
        # Show window
        print("\nShowing main window...")
        window.show_all()
        
        # Process events
        while Gtk.events_pending():
            Gtk.main_iteration()
        
        # Try to open file chooser
        print("\nAttempting to call persistency._show_open_dialog()...")
        
        def timeout_close():
            print("  Timeout - closing any open dialogs")
            for widget in Gtk.Window.list_toplevels():
                if isinstance(widget, Gtk.FileChooserDialog):
                    print(f"  Found and closing: {widget.get_title()}")
                    widget.response(Gtk.ResponseType.CANCEL)
            return False
        
        GLib.timeout_add(1000, timeout_close)
        
        try:
            filepath = persistency._show_open_dialog()
            print(f"SUCCESS: Dialog returned: {filepath}")
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        # Now try via file_explorer method
        print("\nAttempting to call file_explorer.open_document()...")
        
        GLib.timeout_add(1000, timeout_close)
        
        try:
            file_explorer.open_document()
            print("SUCCESS: open_document() completed")
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("ERROR: No file_explorer found!")
    
    window.destroy()
    print("\nTest completed")

if __name__ == '__main__':
    print("=" * 60)
    print("FileChooser Test from Application Context")
    print("=" * 60)
    print()
    
    test_from_app_context()
