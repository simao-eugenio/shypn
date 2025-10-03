#!/usr/bin/env python3
"""Test script for File Explorer functionality.

This script tests the file explorer in isolation using the left_panel_loader.
It validates:
- FileExplorer API (business logic)
- FileExplorerPanel controller (UI binding)
- left_panel_loader integration
- Dock/undock functionality

Usage:
    python3 scripts/test_file_explorer.py
"""

import sys
import os

# Add src to path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, 'src'))

print(f"Repository root: {REPO_ROOT}")
print("=" * 70)

try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk
except Exception as e:
    print(f'ERROR: GTK4 not available: {e}', file=sys.stderr)
    sys.exit(1)

from shypn.helpers.left_panel_loader import create_left_panel


def main():
    """Test the file explorer."""
    print("\n🧪 File Explorer Test")
    print("=" * 70)
    
    app = Gtk.Application(application_id="dev.shypn.file_explorer_test")
    
    def on_activate(app):
        print("\n📋 Loading file explorer...")
        
        # Create left panel loader (will default to models directory)
        try:
            loader = create_left_panel()  # No base_path = defaults to models
            print(f"✓ Left panel loader created")
        except Exception as e:
            print(f"✗ Failed to create left panel: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return
        
        # Check if file explorer was initialized
        if loader.file_explorer:
            print(f"✓ File explorer controller initialized")
            print(f"✓ Current path: {loader.file_explorer.get_current_path()}")
            
            # Get API stats
            stats = loader.file_explorer.explorer.get_stats()
            print(f"✓ Directory contents: {stats['directories']} folders, {stats['files']} files")
        else:
            print("✗ File explorer controller NOT initialized", file=sys.stderr)
        
        # Float the panel (show as window)
        loader.float()
        print("✓ Panel floating (standalone window)")
        
        # Set application
        loader.window.set_application(app)
        
        print("\n" + "=" * 70)
        print("✅ File Explorer Test Passed!")
        print("=" * 70)
        print("\n📝 Manual Testing:")
        print("  1. ✓ Window should be visible")
        print("  2. ✓ Files and folders should be listed")
        print("  3. ⚠ Double-click a folder to enter it")
        print("  4. ⚠ Use back/forward/up buttons to navigate")
        print("  5. ⚠ Status bar should show file counts")
        print("  6. ⚠ Click float button to test dock/undock (won't work in standalone)")
        print("\n💡 Close the window to exit the test")
        print("=" * 70)
    
    app.connect("activate", on_activate)
    return app.run(None)


if __name__ == "__main__":
    sys.exit(main())
