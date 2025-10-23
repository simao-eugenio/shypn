#!/usr/bin/env python3
"""Test float button functionality with simplified skeleton pattern."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.helpers.left_panel_loader import create_left_panel


def test_float_button():
    """Test float button with simplified pattern."""
    print("\n" + "="*60)
    print("FLOAT BUTTON TEST - Skeleton Pattern")
    print("="*60)
    
    # Create main window
    main_window = Gtk.Window(title="Float Button Test")
    main_window.set_default_size(800, 600)
    main_window.connect('destroy', Gtk.main_quit)
    
    # Create container layout
    main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
    main_window.add(main_box)
    
    # Create left dock area (where panel will be hanged)
    left_dock = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    left_dock.set_size_request(250, -1)
    main_box.pack_start(left_dock, False, False, 0)
    
    # Create right content area
    right_content = Gtk.Label(label="Main Content Area\n\nClick the float button in the panel\nto detach/reattach")
    right_content.set_halign(Gtk.Align.CENTER)
    right_content.set_valign(Gtk.Align.CENTER)
    main_box.pack_start(right_content, True, True, 0)
    
    # Create left panel
    print("\n[TEST] Creating left panel...")
    panel = create_left_panel()
    print(f"[TEST] Panel created: window={panel.window}, content={panel.content}")
    
    # Store parent window reference for float button
    panel.parent_window = main_window
    
    print("\n[TEST] Initial state:")
    print(f"  is_hanged: {panel.is_hanged}")
    print(f"  parent_container: {panel.parent_container}")
    
    # Hang panel on left dock
    print("\n[TEST] Hanging panel on left dock...")
    panel.hang_on(left_dock)
    
    print("\n[TEST] After hang_on:")
    print(f"  is_hanged: {panel.is_hanged}")
    print(f"  parent_container: {panel.parent_container}")
    print(f"  content parent: {panel.content.get_parent()}")
    print(f"  left_dock children: {left_dock.get_children()}")
    
    # Add test buttons
    test_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
    test_box.set_margin_start(10)
    test_box.set_margin_end(10)
    test_box.set_margin_top(10)
    test_box.set_margin_bottom(10)
    main_box.pack_end(test_box, False, False, 0)
    
    status_label = Gtk.Label(label="Status: Panel hanged")
    test_box.pack_start(status_label, False, False, 0)
    
    def update_status():
        """Update status label."""
        state = "HANGED" if panel.is_hanged else "FLOATING"
        status_label.set_text(f"Status: Panel {state}")
    
    btn_detach = Gtk.Button(label="Manual Detach")
    def on_detach(button):
        print("\n[TEST] Manual detach clicked...")
        panel.detach()
        update_status()
    btn_detach.connect('clicked', on_detach)
    test_box.pack_start(btn_detach, False, False, 0)
    
    btn_hang = Gtk.Button(label="Manual Hang On")
    def on_hang(button):
        print("\n[TEST] Manual hang_on clicked...")
        panel.hang_on(left_dock)
        update_status()
    btn_hang.connect('clicked', on_hang)
    test_box.pack_start(btn_hang, False, False, 0)
    
    info_label = Gtk.Label(label="\nFloat button in panel\nshould toggle\nbetween states")
    info_label.set_justify(Gtk.Justification.CENTER)
    test_box.pack_start(info_label, False, False, 10)
    
    # Show all
    main_window.show_all()
    
    print("\n[TEST] Window shown. Test the float button in the panel!")
    print("[TEST] Click float button to detach → panel becomes floating window")
    print("[TEST] Click float button again to reattach → panel returns to dock")
    
    Gtk.main()


if __name__ == '__main__':
    test_float_button()
