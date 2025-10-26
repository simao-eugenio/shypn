#!/usr/bin/env python3
"""Test script for file explorer refinements.

Tests:
1. Folder expansion by clicking on folder name (not just arrow)
2. Context menu options are properly enabled/disabled
3. Cut/Copy/Paste operations work inline without dialogs
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
except ImportError as e:
    print(f"ERROR: GTK3 not available: {e}")
    sys.exit(1)

from shypn.helpers.file_explorer_panel import FileExplorerPanel


class TestWindow(Gtk.Window):
    """Test window for file explorer."""
    
    def __init__(self):
        super().__init__(title="File Explorer Refinements Test")
        self.set_default_size(400, 600)
        self.connect('destroy', Gtk.main_quit)
        
        # Create builder and load UI
        builder = Gtk.Builder()
        ui_file = os.path.join(os.path.dirname(__file__), 'ui', 'panels', 'left_panel_vscode.ui')
        builder.add_from_file(ui_file)
        
        # Get the main container from the UI
        main_box = builder.get_object('left_panel_main_box')
        
        # Create file explorer panel
        workspace = os.path.join(os.path.dirname(__file__), 'workspace')
        self.file_panel = FileExplorerPanel(builder, base_path=workspace, root_boundary=workspace)
        
        # Add to window
        self.add(main_box)
        self.show_all()
        
        # Print test instructions
        print("\n" + "="*60)
        print("FILE EXPLORER REFINEMENTS TEST")
        print("="*60)
        print("\nTest 1: Folder Expansion")
        print("  - Click directly on a FOLDER name (not the arrow)")
        print("  - Folder should expand/collapse")
        print("  - Expected: ✓ Works")
        print("\nTest 2: Context Menu - Right-click on tree")
        print("  - Cut, Copy options should be ENABLED when file/folder selected")
        print("  - Paste should be DISABLED initially (no clipboard)")
        print("  - After Cut/Copy, Paste should become ENABLED")
        print("  - Expected: ✓ All options active based on context")
        print("\nTest 3: Cut/Copy/Paste Operations")
        print("  1. Right-click on a file → Cut or Copy")
        print("  2. Right-click on a folder → Paste")
        print("  3. File should appear in destination")
        print("  4. NO dialog should appear (inline operation)")
        print("  Expected: ✓ Inline operations, no dialogs")
        print("\nTest 4: Context Menu State")
        print("  - Open should be DISABLED for folders")
        print("  - Open should be ENABLED for .shy files")
        print("  - Cut/Copy/Rename/Delete DISABLED when no selection")
        print("  Expected: ✓ Menu items properly enabled/disabled")
        print("="*60)
        print("\nStarting interactive test...\n")


def main():
    """Run the test."""
    try:
        window = TestWindow()
        Gtk.main()
    except Exception as e:
        print(f"\nERROR during test: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
