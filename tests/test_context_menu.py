#!/usr/bin/env python3
"""Test script for enhanced context menu operations.

Tests:
1. Cut and paste operations
2. Copy and paste operations  
3. Duplicate operation
4. Open operation
5. Refresh operation
"""

import os
import sys
import time

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, GLib
except Exception as e:
    print(f'ERROR: GTK4 not available: {e}', file=sys.stderr)
    sys.exit(1)

from shypn.ui.panels.file_explorer_panel import FileExplorerPanel


def create_test_files():
    """Create test files for context menu operations."""
    models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Create test files
    test_file1 = os.path.join(models_dir, 'test_copy.txt')
    test_file2 = os.path.join(models_dir, 'test_cut.txt')
    test_folder = os.path.join(models_dir, 'test_folder_ops')
    
    with open(test_file1, 'w') as f:
        f.write("This file will be copied\n")
    
    with open(test_file2, 'w') as f:
        f.write("This file will be cut\n")
    
    os.makedirs(test_folder, exist_ok=True)
    with open(os.path.join(test_folder, 'nested.txt'), 'w') as f:
        f.write("Nested file\n")
    
    print("✓ Test files created")
    return models_dir


def test_context_menu_operations(app):
    """Test context menu operations."""
    print("\n=== Testing Context Menu Operations ===\n")
    
    models_dir = create_test_files()
    
    # Create builder and load UI
    builder = Gtk.Builder()
    ui_path = os.path.join(os.path.dirname(__file__), '..', 'ui', 'panels', 'left_panel.ui')
    builder.add_from_file(ui_path)
    
    # Create file explorer panel
    explorer = FileExplorerPanel(builder, base_path=models_dir)
    
    print("✓ File explorer initialized\n")
    
    # Test 1: Copy operation
    print("Test 1: Copy Operation")
    test_file = os.path.join(models_dir, 'test_copy.txt')
    explorer.selected_item_path = test_file
    explorer.selected_item_name = 'test_copy.txt'
    explorer.selected_item_is_dir = False
    explorer._on_copy_action(None, None)
    print(f"  Clipboard: {explorer.clipboard_path}")
    print(f"  Operation: {explorer.clipboard_operation}")
    assert explorer.clipboard_operation == 'copy', "Copy operation failed"
    print("  ✓ Copy operation successful\n")
    
    # Test 2: Paste (copy) operation
    print("Test 2: Paste (Copy) Operation")
    explorer.selected_item_path = models_dir
    explorer.selected_item_is_dir = True
    explorer._on_paste_action(None, None)
    copied_file = os.path.join(models_dir, 'test_copy_1.txt')
    assert os.path.exists(copied_file), "Paste (copy) failed"
    print(f"  ✓ File copied successfully to: {os.path.basename(copied_file)}\n")
    
    # Test 3: Cut operation
    print("Test 3: Cut Operation")
    test_file = os.path.join(models_dir, 'test_cut.txt')
    explorer.selected_item_path = test_file
    explorer.selected_item_name = 'test_cut.txt'
    explorer.selected_item_is_dir = False
    explorer._on_cut_action(None, None)
    print(f"  Clipboard: {explorer.clipboard_path}")
    print(f"  Operation: {explorer.clipboard_operation}")
    assert explorer.clipboard_operation == 'cut', "Cut operation failed"
    print("  ✓ Cut operation successful\n")
    
    # Test 4: Paste (cut) operation
    print("Test 4: Paste (Move) Operation")
    test_folder = os.path.join(models_dir, 'test_folder_ops')
    explorer.selected_item_path = test_folder
    explorer.selected_item_is_dir = True
    explorer._on_paste_action(None, None)
    moved_file = os.path.join(test_folder, 'test_cut.txt')
    assert os.path.exists(moved_file), "Paste (move) failed"
    assert not os.path.exists(test_file), "Original file still exists after cut"
    print(f"  ✓ File moved successfully to: {moved_file}\n")
    
    # Test 5: Duplicate operation
    print("Test 5: Duplicate Operation")
    original = os.path.join(models_dir, 'test_copy.txt')
    explorer.selected_item_path = original
    explorer.selected_item_name = 'test_copy.txt'
    explorer.selected_item_is_dir = False
    explorer._on_duplicate_action(None, None)
    duplicate = os.path.join(models_dir, 'test_copy_copy.txt')
    assert os.path.exists(duplicate), "Duplicate failed"
    print(f"  ✓ File duplicated successfully: {os.path.basename(duplicate)}\n")
    
    # Test 6: Open operation (just check it doesn't crash)
    print("Test 6: Open Operation")
    explorer.selected_item_path = original
    explorer.selected_item_name = 'test_copy.txt'
    explorer.selected_item_is_dir = False
    explorer._on_open_action(None, None)
    print("  ✓ Open operation successful (file set as current)\n")
    
    # Test 7: Refresh operation
    print("Test 7: Refresh Operation")
    explorer._on_refresh_action(None, None)
    print("  ✓ Refresh operation successful\n")
    
    print("=== All Context Menu Tests Passed! ===\n")
    
    # Cleanup
    print("Cleaning up test files...")
    import shutil
    for item in ['test_copy.txt', 'test_copy_1.txt', 'test_copy_copy.txt', 
                 'test_folder_ops', 'test_cut.txt']:
        path = os.path.join(models_dir, item)
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.exists(path):
                os.remove(path)
        except:
            pass
    print("✓ Cleanup complete")
    
    app.quit()


def main():
    """Main test function."""
    print("Starting context menu operations test...")
    
    app = Gtk.Application(application_id='com.shypn.test.contextmenu')
    app.connect('activate', test_context_menu_operations)
    app.run(None)


if __name__ == '__main__':
    main()
