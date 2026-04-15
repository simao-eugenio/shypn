#!/usr/bin/env python3
"""Test script for inline rename functionality.

# This is a script-style test intended to be run directly (not via pytest).
if __name__ != '__main__':
    import pytest
    pytest.skip('Script-style test, run directly with python3', allow_module_level=True)

Tests:
1. Right-click on file → Rename → Edit inline (no dialog)
2. Right-click on folder → Rename → Edit inline (no dialog)
3. Cancel editing with Escape key
4. Validate .shy extension is preserved for files
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
    """Test window for inline rename."""
    
    def __init__(self):
        super().__init__(title="Inline Rename Test")
        self.set_default_size(500, 600)
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
        print("\n" + "="*70)
        print("INLINE RENAME FUNCTIONALITY TEST")
        print("="*70)
        print("\n📝 TEST PROCEDURE:")
        print("\n1. RIGHT-CLICK on a file in the tree")
        print("   → Select 'Rename' from context menu")
        print("   → File name should become EDITABLE INLINE (no dialog!)")
        print("   → Edit the name and press ENTER")
        print("   → File should be renamed")
        print("   ✓ Expected: NO DIALOG, inline editing only")
        
        print("\n2. RIGHT-CLICK on a folder in the tree")
        print("   → Select 'Rename' from context menu")
        print("   → Folder name should become EDITABLE INLINE")
        print("   → Edit the name and press ENTER")
        print("   → Folder should be renamed")
        print("   ✓ Expected: NO DIALOG, inline editing only")
        
        print("\n3. START RENAME and press ESCAPE")
        print("   → Name should revert to original")
        print("   → No changes made")
        print("   ✓ Expected: Cancel works properly")
        
        print("\n4. RENAME a .shy file WITHOUT typing .shy")
        print("   → Type just the base name (e.g., 'mymodel')")
        print("   → Press ENTER")
        print("   → .shy extension should be auto-added")
        print("   ✓ Expected: Extension preserved automatically")
        
        print("\n5. TRY TO RENAME to existing name")
        print("   → Should show error message")
        print("   → Name should not change")
        print("   ✓ Expected: Duplicate names prevented")
        
        print("\n" + "="*70)
        print("🚀 Application ready. Start testing!")
        print("="*70 + "\n")


def main():
    """Run the test."""
    try:
        window = TestWindow()
        Gtk.main()
    except Exception as e:
        print(f"\n❌ ERROR during test: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n✅ Test completed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
