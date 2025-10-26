#!/usr/bin/env python3
"""Test inline file operations (no dialogs)."""

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
from shypn.helpers.model_canvas_loader import create_model_canvas

def test_inline_operations():
    """Test inline file operations without dialogs."""
    print("=" * 60)
    print("Testing Inline File Operations (No Dialogs)")
    print("=" * 60)
    
    # Create main window
    app = Gtk.Application()
    window = Gtk.Window(title="Test Inline Operations")
    window.set_default_size(800, 600)
    
    # Create persistency manager
    persistency = NetObjPersistency(parent_window=window)
    
    # Create model canvas loader
    print("\n1. Creating model canvas loader...")
    model_canvas_loader = create_model_canvas()
    model_canvas_loader.parent_window = window
    model_canvas_loader.persistency = persistency
    print(f"   ✓ Canvas loader created")
    
    # Create file explorer
    print("\n2. Creating file explorer...")
    left_panel_loader = create_left_panel(load_window=True)
    file_explorer = left_panel_loader.file_explorer
    
    if not file_explorer:
        print("   ERROR: file_explorer is None!")
        return False
    print(f"   ✓ file_explorer created")
    
    # Wire file explorer
    file_explorer.set_parent_window(window)
    file_explorer.set_persistency_manager(persistency)
    file_explorer.set_canvas_loader(model_canvas_loader)
    print(f"   ✓ All dependencies wired")
    
    # Show window
    window.show_all()
    while Gtk.events_pending():
        Gtk.main_iteration()
    
    # Test 1: Inline save (auto-generate filename)
    print("\n3. Testing inline save (no dialog)...")
    drawing_area = model_canvas_loader.get_current_document()
    if drawing_area:
        canvas_manager = model_canvas_loader.get_canvas_manager(drawing_area)
        if canvas_manager:
            # Mark as dirty to trigger save
            canvas_manager.mark_dirty()
            print(f"   Initial filepath: {canvas_manager.get_filepath()}")
            print(f"   is_default_filename: {canvas_manager.is_default_filename()}")
            
            # Count files in workspace before save
            workspace_files_before = [f for f in os.listdir(file_explorer.explorer.current_path) 
                                     if f.endswith('.shy')]
            print(f"   Workspace files before: {len(workspace_files_before)}")
            
            # Call save - should auto-generate filename
            file_explorer.save_current_document()
            
            # Wait for save to complete
            timeout_count = 0
            while Gtk.events_pending() and timeout_count < 10:
                Gtk.main_iteration()
                timeout_count += 1
            
            # Check if file was created
            workspace_files_after = [f for f in os.listdir(file_explorer.explorer.current_path) 
                                    if f.endswith('.shy')]
            print(f"   Workspace files after: {len(workspace_files_after)}")
            
            new_filepath = canvas_manager.get_filepath()
            print(f"   New filepath: {new_filepath}")
            
            if os.path.exists(new_filepath):
                print(f"   ✓ File auto-saved: {os.path.basename(new_filepath)}")
            else:
                print(f"   ✗ File NOT saved!")
            
            print(f"   is_dirty after save: {canvas_manager.is_dirty()}")
    
    # Test 2: Inline Save As (auto-generate copy)
    print("\n4. Testing inline Save As (no dialog)...")
    if drawing_area:
        canvas_manager = model_canvas_loader.get_canvas_manager(drawing_area)
        if canvas_manager:
            original_filepath = canvas_manager.get_filepath()
            print(f"   Original filepath: {original_filepath}")
            
            # Call save as - should auto-generate copy
            file_explorer.save_current_document_as()
            
            # Wait for save to complete
            timeout_count = 0
            while Gtk.events_pending() and timeout_count < 10:
                Gtk.main_iteration()
                timeout_count += 1
            
            new_filepath = canvas_manager.get_filepath()
            print(f"   New filepath: {new_filepath}")
            
            if new_filepath != original_filepath:
                print(f"   ✓ New file created: {os.path.basename(new_filepath)}")
                if os.path.exists(new_filepath):
                    print(f"   ✓ File exists on disk")
                else:
                    print(f"   ✗ File NOT on disk!")
            else:
                print(f"   ✗ Filepath unchanged!")
    
    # Test 3: Inline open (select file from tree)
    print("\n5. Testing inline open (selected file, no dialog)...")
    
    # First, we need to select a file in the tree
    test_file = "models/teste.shy"
    if os.path.exists(test_file):
        abs_path = os.path.abspath(test_file)
        
        # Navigate to models directory
        file_explorer.explorer.navigate_to(os.path.dirname(abs_path))
        file_explorer._load_current_directory()
        
        # Wait for directory to load
        timeout_count = 0
        while Gtk.events_pending() and timeout_count < 10:
            Gtk.main_iteration()
            timeout_count += 1
        
        # Find and select the file in tree view
        model = file_explorer.store
        iter = model.get_iter_first()
        file_found = False
        
        while iter:
            filepath = model.get_value(iter, 2)
            if filepath == abs_path:
                file_explorer.tree_view.get_selection().select_iter(iter)
                file_found = True
                print(f"   Selected file: {os.path.basename(abs_path)}")
                break
            iter = model.iter_next(iter)
        
        if file_found:
            initial_tabs = model_canvas_loader.notebook.get_n_pages()
            
            # Call open_document - should open selected file
            file_explorer.open_document()
            
            # Wait for file to open
            timeout_count = 0
            while Gtk.events_pending() and timeout_count < 10:
                Gtk.main_iteration()
                timeout_count += 1
            
            final_tabs = model_canvas_loader.notebook.get_n_pages()
            
            if final_tabs > initial_tabs:
                print(f"   ✓ File opened (tabs: {initial_tabs} → {final_tabs})")
            else:
                print(f"   ✗ File NOT opened (tabs unchanged)")
        else:
            print(f"   ⚠ Could not find file in tree: {abs_path}")
    else:
        print(f"   SKIP: Test file not found: {test_file}")
    
    # Cleanup - remove auto-generated files
    print("\n6. Cleanup...")
    try:
        workspace_files = [f for f in os.listdir(file_explorer.explorer.current_path) 
                          if f.startswith('model_') and f.endswith('.shy')]
        for f in workspace_files:
            filepath = os.path.join(file_explorer.explorer.current_path, f)
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"   Removed: {f}")
    except Exception as e:
        print(f"   Warning: Cleanup error: {e}")
    
    window.destroy()
    print("\n" + "=" * 60)
    print("Inline operations test completed! ✓")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = test_inline_operations()
    sys.exit(0 if success else 1)
