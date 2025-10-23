#!/usr/bin/env python3
"""Test File Panel V2 - Standalone test for refactored file panel.

Tests:
- Category-based layout
- TreeView file browser
- Context menu operations
- Inline buttons
- Wayland Error 71 prevention

Expected: NO Error 71 when using file operations
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.ui.file_panel_v2 import FilePanelV2


class TestWindow(Gtk.ApplicationWindow):
    """Test window for File Panel V2."""
    
    def __init__(self, app):
        super().__init__(application=app, title="File Panel V2 Test")
        self.set_default_size(400, 600)
        
        # Create file panel
        print("[TEST] Creating File Panel V2...")
        self.file_panel = FilePanelV2(base_path=os.path.join(os.path.dirname(__file__), '..', 'workspace'))
        self.file_panel.set_parent_window(self)
        
        # Add panel to window
        self.add(self.file_panel.get_widget())
        
        print("[TEST] File Panel V2 ready!")
        print("[TEST] Try:")
        print("[TEST]   - Click category titles to expand/collapse")
        print("[TEST]   - Double-click files/folders in tree")
        print("[TEST]   - Right-click for context menu")
        print("[TEST]   - Use inline buttons [+][📁][↻][─]")
        print("[TEST]   - Watch for Error 71 in terminal")


class TestApplication(Gtk.Application):
    """Test application."""
    
    def __init__(self):
        super().__init__(application_id='org.shypn.test.filepanelv2')
    
    def do_activate(self):
        """Activate the application."""
        win = TestWindow(self)
        win.show_all()


def main():
    """Run the test application."""
    print("=" * 70)
    print("File Panel V2 Standalone Test")
    print("=" * 70)
    print("Watch for: Gdk-Message: Error 71 (Protocol error)")
    print()
    print("Features to test:")
    print("  ✓ Category expansion/collapse")
    print("  ✓ TreeView file browser")
    print("  ✓ Double-click to open files/folders")
    print("  ✓ Right-click context menu")
    print("  ✓ Inline buttons: New File, New Folder, Refresh, Collapse All")
    print("  ✓ Context menu: New, Open, Rename, Delete, Properties")
    print("=" * 70)
    print()
    
    app = TestApplication()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())
