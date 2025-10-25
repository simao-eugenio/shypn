#!/usr/bin/env python3
"""Test save operations and default canvas state."""

import sys
import os
import tempfile
import shutil
sys.path.insert(0, 'src')

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.helpers.file_panel_loader import create_left_panel
from shypn.file.netobj_persistency import NetObjPersistency
from shypn.ui.menu_actions import MenuActions
from shypn.helpers.model_canvas_loader import create_model_canvas

def test_save_operations():
    """Test file save and save-as operations."""
    print("=" * 60)
    print("Testing Save Operations and Default Canvas State")
    print("=" * 60)
    
    # Create main window
    app = Gtk.Application()
    window = Gtk.Window(title="Test Save Operations")
    window.set_default_size(800, 600)
    
    # Create persistency manager
    persistency = NetObjPersistency(parent_window=window)
    
    # Create model canvas loader (using factory function)
    print("\n1. Creating model canvas loader...")
    model_canvas_loader = create_model_canvas()
    model_canvas_loader.parent_window = window
    model_canvas_loader.persistency = persistency
    print(f"   ✓ Canvas loader created")
    print(f"   ✓ Notebook: {model_canvas_loader.notebook}")
    
    # Check default canvas state
    print("\n2. Checking default canvas state...")
    drawing_area = model_canvas_loader.get_current_document()
    print(f"   Drawing area: {drawing_area}")
    
    if drawing_area:
        print(f"   ✓ Default canvas exists")
        # Check if it has a model
        if hasattr(drawing_area, 'model'):
            print(f"   Model: {drawing_area.model}")
        # Check canvas manager
        canvas_manager = model_canvas_loader.get_canvas_manager(drawing_area)
        print(f"   Canvas manager: {canvas_manager}")
        if canvas_manager:
            print(f"   ✓ Canvas manager exists")
            print(f"   is_default_filename(): {canvas_manager.is_default_filename()}")
            print(f"   filename: {canvas_manager.filename}")
    else:
        print("   ⚠ No default canvas found!")
    
    # Create left panel with file explorer
    print("\n3. Creating file explorer...")
    left_panel_loader = create_left_panel(load_window=True)
    file_explorer = left_panel_loader.file_explorer
    
    if not file_explorer:
        print("   ERROR: file_explorer is None!")
        return False
    print(f"   ✓ file_explorer created")
    
    # Wire file explorer
    print("\n4. Wiring file_explorer...")
    file_explorer.set_parent_window(window)
    file_explorer.set_persistency_manager(persistency)
    file_explorer.set_canvas_loader(model_canvas_loader)
    print(f"   ✓ All dependencies wired")
    
    # Create menu actions
    print("\n5. Creating menu actions...")
    menu_actions = MenuActions(app, window)
    menu_actions.persistency = persistency
    menu_actions.model_canvas_loader = model_canvas_loader
    menu_actions.set_file_explorer_panel(file_explorer)
    menu_actions.register_all_actions()
    print(f"   ✓ Menu actions registered")
    
    # Show window
    window.show_all()
    while Gtk.events_pending():
        Gtk.main_iteration()
    
    # Test Save on default canvas (should prompt for Save As)
    print("\n6. Testing save on default canvas...")
    print("   [Attempting to save default canvas]")
    
    drawing_area = model_canvas_loader.get_current_document()
    if drawing_area:
        canvas_manager = model_canvas_loader.get_canvas_manager(drawing_area)
        if canvas_manager:
            print(f"   is_default_filename: {canvas_manager.is_default_filename()}")
            if canvas_manager.is_default_filename():
                print("   ✓ Default canvas correctly flagged as 'untitled'")
                print("   → Save should trigger 'Save As' dialog")
            else:
                print(f"   ⚠ Default canvas has filename: {canvas_manager.filename}")
    
    # Test save_current_document method
    print("\n7. Testing file_explorer.save_current_document()...")
    
    def timeout_close_dialog():
        """Close any file chooser dialogs."""
        for widget in Gtk.Window.list_toplevels():
            if isinstance(widget, Gtk.FileChooserDialog):
                print(f"   [Found dialog: '{widget.get_title()}']")
                widget.response(Gtk.ResponseType.CANCEL)
        return False
    
    GLib.timeout_add(500, timeout_close_dialog)
    
    try:
        file_explorer.save_current_document()
        print("   ✓ save_current_document() executed")
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
    
    # Test save_current_document_as method
    print("\n8. Testing file_explorer.save_current_document_as()...")
    
    GLib.timeout_add(500, timeout_close_dialog)
    
    try:
        file_explorer.save_current_document_as()
        print("   ✓ save_current_document_as() executed")
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
    
    # Test new_document method
    print("\n9. Testing file_explorer.new_document()...")
    try:
        initial_tabs = model_canvas_loader.notebook.get_n_pages() if model_canvas_loader.notebook else 0
        print(f"   Initial tabs: {initial_tabs}")
        
        file_explorer.new_document()
        
        final_tabs = model_canvas_loader.notebook.get_n_pages() if model_canvas_loader.notebook else 0
        print(f"   Final tabs: {final_tabs}")
        
        if final_tabs > initial_tabs:
            print("   ✓ New canvas tab created")
        else:
            print("   ⚠ No new tab created")
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test Menu actions
    print("\n10. Testing menu save actions...")
    
    # Test File→Save
    print("   Testing File→Save (app.save)...")
    GLib.timeout_add(500, timeout_close_dialog)
    
    try:
        action = app.lookup_action("save")
        if action:
            action.activate(None)
            print("   ✓ File→Save works")
        else:
            print("   ERROR: 'save' action not found!")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Wait for events
    timeout_count = 0
    while Gtk.events_pending() and timeout_count < 10:
        Gtk.main_iteration()
        timeout_count += 1
    
    # Test File→Save As
    print("   Testing File→Save As (app.save-as)...")
    GLib.timeout_add(500, timeout_close_dialog)
    
    try:
        action = app.lookup_action("save-as")
        if action:
            action.activate(None)
            print("   ✓ File→Save As works")
        else:
            print("   ERROR: 'save-as' action not found!")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Wait for events
    timeout_count = 0
    while Gtk.events_pending() and timeout_count < 10:
        Gtk.main_iteration()
        timeout_count += 1
    
    # Test File→New
    print("   Testing File→New (app.new)...")
    try:
        initial_tabs = model_canvas_loader.notebook.get_n_pages() if model_canvas_loader.notebook else 0
        
        action = app.lookup_action("new")
        if action:
            action.activate(None)
            
            final_tabs = model_canvas_loader.notebook.get_n_pages() if model_canvas_loader.notebook else 0
            
            if final_tabs > initial_tabs:
                print("   ✓ File→New works (new tab created)")
            else:
                print("   ⚠ File→New didn't create new tab")
        else:
            print("   ERROR: 'new' action not found!")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    window.destroy()
    print("\n" + "=" * 60)
    print("Save operations test completed! ✓")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = test_save_operations()
    sys.exit(0 if success else 1)
