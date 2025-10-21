#!/usr/bin/env python3
"""Test FileChooser dialog behavior to identify Wayland crash."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

def test_file_chooser_with_parent():
    """Test FileChooser with parent window."""
    print("Test 1: FileChooser with parent window")
    
    # Create a window (simulating main application window)
    window = Gtk.Window(title="Test Parent")
    window.set_default_size(200, 200)
    window.show_all()
    
    # Process pending events
    while Gtk.events_pending():
        Gtk.main_iteration()
    
    print("  Parent window created and shown")
    
    # Create FileChooser with parent
    dialog = Gtk.FileChooserDialog(
        title='Test Open',
        parent=window,
        action=Gtk.FileChooserAction.OPEN
    )
    dialog.set_modal(True)
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        Gtk.STOCK_OPEN, Gtk.ResponseType.OK
    )
    
    print("  FileChooser created with modal=True")
    
    # Try to run it with timeout
    def timeout_close():
        print("  Timeout - closing dialog")
        dialog.response(Gtk.ResponseType.CANCEL)
        return False
    
    GLib.timeout_add(1000, timeout_close)  # Close after 1 second
    
    try:
        print("  About to call dialog.run()...")
        response = dialog.run()
        print(f"  Dialog returned: {response}")
    except Exception as e:
        print(f"  ERROR during run(): {e}")
        import traceback
        traceback.print_exc()
    finally:
        dialog.destroy()
        window.destroy()
    
    print("  Test 1 complete\n")

def test_file_chooser_no_parent():
    """Test FileChooser without parent."""
    print("Test 2: FileChooser without parent")
    
    dialog = Gtk.FileChooserDialog(
        title='Test Open No Parent',
        parent=None,
        action=Gtk.FileChooserAction.OPEN
    )
    dialog.set_modal(True)
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        Gtk.STOCK_OPEN, Gtk.ResponseType.OK
    )
    
    print("  FileChooser created without parent")
    
    def timeout_close():
        print("  Timeout - closing dialog")
        dialog.response(Gtk.ResponseType.CANCEL)
        return False
    
    GLib.timeout_add(1000, timeout_close)
    
    try:
        print("  About to call dialog.run()...")
        response = dialog.run()
        print(f"  Dialog returned: {response}")
    except Exception as e:
        print(f"  ERROR during run(): {e}")
        import traceback
        traceback.print_exc()
    finally:
        dialog.destroy()
    
    print("  Test 2 complete\n")

def test_file_chooser_with_hidden_parent():
    """Test FileChooser with hidden parent window."""
    print("Test 3: FileChooser with hidden parent")
    
    # Create window but keep it hidden
    window = Gtk.Window(title="Test Hidden Parent")
    window.set_default_size(200, 200)
    # Don't call show_all() - keep window hidden
    
    print("  Parent window created but NOT shown")
    
    dialog = Gtk.FileChooserDialog(
        title='Test Open Hidden Parent',
        parent=window,
        action=Gtk.FileChooserAction.OPEN
    )
    dialog.set_modal(True)
    dialog.add_buttons(
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
        Gtk.STOCK_OPEN, Gtk.ResponseType.OK
    )
    
    print("  FileChooser created with hidden parent")
    
    def timeout_close():
        print("  Timeout - closing dialog")
        dialog.response(Gtk.ResponseType.CANCEL)
        return False
    
    GLib.timeout_add(1000, timeout_close)
    
    try:
        print("  About to call dialog.run()...")
        response = dialog.run()
        print(f"  Dialog returned: {response}")
    except Exception as e:
        print(f"  ERROR during run(): {e}")
        import traceback
        traceback.print_exc()
    finally:
        dialog.destroy()
        window.destroy()
    
    print("  Test 3 complete\n")

def test_persistency_pattern():
    """Test the actual pattern used in NetObjPersistency."""
    print("Test 4: NetObjPersistency pattern")
    
    from shypn.file.netobj_persistency import NetObjPersistency
    
    # Create a visible parent window
    window = Gtk.Window(title="Test Parent for Persistency")
    window.set_default_size(400, 300)
    window.show_all()
    
    while Gtk.events_pending():
        Gtk.main_iteration()
    
    print("  Creating NetObjPersistency with parent window")
    persistency = NetObjPersistency(parent_window=window)
    
    print("  Calling _show_open_dialog() with timeout...")
    
    def timeout_close():
        print("  Timeout - need to close dialog manually")
        # This is tricky - we need to find and close the dialog
        for widget in Gtk.Window.list_toplevels():
            if isinstance(widget, Gtk.FileChooserDialog):
                print(f"  Found FileChooserDialog: {widget.get_title()}")
                widget.response(Gtk.ResponseType.CANCEL)
        return False
    
    GLib.timeout_add(1000, timeout_close)
    
    try:
        filepath = persistency._show_open_dialog()
        print(f"  Dialog returned filepath: {filepath}")
    except Exception as e:
        print(f"  ERROR during _show_open_dialog(): {e}")
        import traceback
        traceback.print_exc()
    
    window.destroy()
    print("  Test 4 complete\n")

if __name__ == '__main__':
    print("=" * 60)
    print("FileChooser Dialog Wayland Test")
    print("=" * 60)
    print()
    
    try:
        test_file_chooser_with_parent()
        test_file_chooser_no_parent()
        test_file_chooser_with_hidden_parent()
        test_persistency_pattern()
        
        print("=" * 60)
        print("All tests completed!")
        print("=" * 60)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
