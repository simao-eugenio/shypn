#!/usr/bin/env python3
"""Test actual save operation with a real model file."""

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

def test_actual_save():
    """Test saving an actual file."""
    print("=" * 60)
    print("Testing Actual Save with Real Model")
    print("=" * 60)
    
    # Create main window
    app = Gtk.Application()
    window = Gtk.Window(title="Test Actual Save")
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
    
    # Test 1: Open an existing file
    print("\n3. Opening existing file...")
    test_file = "models/teste.shy"
    if not os.path.exists(test_file):
        print(f"   ERROR: Test file not found: {test_file}")
        return False
    
    try:
        file_explorer._open_file_from_path(os.path.abspath(test_file))
        print(f"   ✓ Opened {test_file}")
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Wait for file to load
    timeout_count = 0
    while Gtk.events_pending() and timeout_count < 20:
        Gtk.main_iteration()
        timeout_count += 1
    
    # Check current canvas state
    print("\n4. Checking current canvas state...")
    drawing_area = model_canvas_loader.get_current_document()
    if not drawing_area:
        print("   ERROR: No current document!")
        return False
    
    canvas_manager = model_canvas_loader.get_canvas_manager(drawing_area)
    if not canvas_manager:
        print("   ERROR: No canvas manager!")
        return False
    
    print(f"   Current file: {canvas_manager.get_filepath()}")
    print(f"   is_default_filename: {canvas_manager.is_default_filename()}")
    print(f"   is_dirty: {canvas_manager.is_dirty()}")
    print(f"   filename: {canvas_manager.filename}")
    
    # Make a change to mark it as dirty
    print("\n5. Marking canvas as dirty (simulating edit)...")
    canvas_manager.mark_dirty()
    print(f"   is_dirty: {canvas_manager.is_dirty()}")
    
    # Create a temporary copy to save to
    print("\n6. Creating temporary save location...")
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, "test_save.shy")
    print(f"   Temp file: {temp_file}")
    
    # Test Save As to temp location
    print("\n7. Testing Save As operation...")
    
    # Mock the save dialog to return our temp path
    original_show_save = persistency._show_save_dialog
    
    def mock_save_dialog():
        print(f"   [Mocking save dialog to return: {temp_file}]")
        return temp_file
    
    persistency._show_save_dialog = mock_save_dialog
    
    try:
        file_explorer.save_current_document_as()
        print(f"   ✓ save_current_document_as() executed")
        
        # Check if file was saved
        if os.path.exists(temp_file):
            file_size = os.path.getsize(temp_file)
            print(f"   ✓ File saved: {temp_file} ({file_size} bytes)")
            
            # Verify it's a valid .shy file
            with open(temp_file, 'r') as f:
                content = f.read(100)
                if 'xml' in content.lower() or '{' in content:
                    print(f"   ✓ File appears valid (contains XML or JSON)")
                else:
                    print(f"   ⚠ File content unclear: {content[:50]}")
        else:
            print(f"   ✗ File NOT saved!")
            
        # Check canvas manager state after save
        print(f"   is_dirty after save: {canvas_manager.is_dirty()}")
        print(f"   filepath after save: {canvas_manager.get_filepath()}")
        
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original method
        persistency._show_save_dialog = original_show_save
    
    # Test direct Save (should now save to temp_file)
    print("\n8. Testing direct Save operation...")
    
    # Mark dirty again
    canvas_manager.mark_dirty()
    print(f"   is_dirty before save: {canvas_manager.is_dirty()}")
    
    # Remove temp file to verify it's created again
    if os.path.exists(temp_file):
        os.remove(temp_file)
        print(f"   Removed temp file to test save")
    
    try:
        file_explorer.save_current_document()
        print(f"   ✓ save_current_document() executed")
        
        # Check if file was saved
        if os.path.exists(temp_file):
            file_size = os.path.getsize(temp_file)
            print(f"   ✓ File saved again: {temp_file} ({file_size} bytes)")
        else:
            print(f"   ✗ File NOT saved (should save to existing filepath)")
            
        print(f"   is_dirty after save: {canvas_manager.is_dirty()}")
        
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Cleanup
    print("\n9. Cleanup...")
    try:
        shutil.rmtree(temp_dir)
        print(f"   ✓ Cleaned up temp directory")
    except Exception as e:
        print(f"   Warning: Cleanup failed: {e}")
    
    window.destroy()
    print("\n" + "=" * 60)
    print("Actual save test completed! ✓")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = test_actual_save()
    sys.exit(0 if success else 1)
