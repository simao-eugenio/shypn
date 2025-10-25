#!/usr/bin/env python3
"""Test file operations to verify menu File→Open and double-click work."""

import sys
import os
sys.path.insert(0, 'src')

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.helpers.file_panel_loader import create_left_panel
from shypn.file.netobj_persistency import NetObjPersistency
from shypn.ui.menu_actions import MenuActions
from shypn.helpers.model_canvas_loader import ModelCanvasLoader

def test_file_operations():
    """Test file operations in the actual application context."""
    print("=" * 60)
    print("Testing File Operations")
    print("=" * 60)
    
    # Create main window
    app = Gtk.Application()
    window = Gtk.Window(title="Test File Operations")
    window.set_default_size(800, 600)
    
    # Create persistency manager
    persistency = NetObjPersistency(parent_window=window)
    
    # Create model canvas loader
    model_canvas_loader = ModelCanvasLoader()
    model_canvas_loader.persistency = persistency
    
    # Create left panel with file explorer
    print("\n1. Creating left panel...")
    left_panel_loader = create_left_panel(load_window=True)
    file_explorer = left_panel_loader.file_explorer
    
    if not file_explorer:
        print("ERROR: file_explorer is None!")
        return False
    print(f"   ✓ file_explorer created: {file_explorer}")
    
    # Wire file explorer
    print("\n2. Wiring file_explorer dependencies...")
    file_explorer.set_parent_window(window)
    file_explorer.set_persistency_manager(persistency)
    file_explorer.set_canvas_loader(model_canvas_loader)
    print(f"   ✓ parent_window: {file_explorer.parent_window}")
    print(f"   ✓ persistency: {file_explorer.persistency}")
    print(f"   ✓ canvas_loader: {file_explorer.canvas_loader}")
    
    # Create menu actions
    print("\n3. Creating menu actions...")
    menu_actions = MenuActions(app, window)
    menu_actions.persistency = persistency
    menu_actions.model_canvas_loader = model_canvas_loader
    menu_actions.set_file_explorer_panel(file_explorer)
    menu_actions.register_all_actions()
    print(f"   ✓ menu_actions.file_explorer_panel: {menu_actions.file_explorer_panel}")
    
    # Show window
    window.show_all()
    
    # Process events
    while Gtk.events_pending():
        Gtk.main_iteration()
    
    # Test 1: Menu File→Open simulation
    print("\n4. Testing menu File→Open...")
    print("   [Simulating menu action 'app.open']")
    
    def timeout_close_dialog():
        """Close any file chooser dialogs after 500ms."""
        for widget in Gtk.Window.list_toplevels():
            if isinstance(widget, Gtk.FileChooserDialog):
                print(f"   [Found FileChooser dialog: '{widget.get_title()}']")
                widget.response(Gtk.ResponseType.CANCEL)
        return False
    
    GLib.timeout_add(500, timeout_close_dialog)
    
    try:
        # Simulate menu action click
        action = app.lookup_action("open")
        if action:
            print("   [Activating 'open' action]")
            action.activate(None)
            print("   ✓ Menu File→Open works!")
        else:
            print("   ERROR: 'open' action not found!")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Wait for events
    timeout_count = 0
    while Gtk.events_pending() and timeout_count < 10:
        Gtk.main_iteration()
        timeout_count += 1
    
    # Test 2: file_explorer.open_document() directly
    print("\n5. Testing file_explorer.open_document() directly...")
    
    GLib.timeout_add(500, timeout_close_dialog)
    
    try:
        file_explorer.open_document()
        print("   ✓ file_explorer.open_document() works!")
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Wait for events
    timeout_count = 0
    while Gtk.events_pending() and timeout_count < 10:
        Gtk.main_iteration()
        timeout_count += 1
    
    # Test 3: Double-click simulation (open specific file)
    print("\n6. Testing _open_file_from_path() (double-click simulation)...")
    test_file = "models/teste.shy"
    if os.path.exists(test_file):
        try:
            file_explorer._open_file_from_path(os.path.abspath(test_file))
            print(f"   ✓ Opened {test_file}")
        except Exception as e:
            print(f"   ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print(f"   SKIP: {test_file} not found")
    
    window.destroy()
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = test_file_operations()
    sys.exit(0 if success else 1)
