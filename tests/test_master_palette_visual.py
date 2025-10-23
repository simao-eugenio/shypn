#!/usr/bin/env python3
"""Test script to verify Master Palette appears correctly in main window.

This script loads the main window with the master palette and displays it.
Use this to visually confirm the palette is visible and properly positioned.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.ui import MasterPalette

def main():
    # Load main window UI
    builder = Gtk.Builder()
    ui_path = os.path.join(os.path.dirname(__file__), 'ui', 'main', 'main_window.ui')
    builder.add_from_file(ui_path)
    
    # Get main window and palette slot
    window = builder.get_object('main_window')
    palette_slot = builder.get_object('master_palette_slot')
    
    if not palette_slot:
        print("ERROR: master_palette_slot not found!")
        sys.exit(1)
    
    # Create and add palette
    palette = MasterPalette()
    palette_widget = palette.get_widget()
    palette_slot.pack_start(palette_widget, True, True, 0)
    
    # Show window
    window.show_all()
    
    # Print status
    print("=" * 60)
    print("MASTER PALETTE TEST")
    print("=" * 60)
    print(f"Palette widget visible: {palette_widget.get_visible()}")
    print(f"Palette widget size request: {palette_widget.get_size_request()}")
    print(f"Palette slot visible: {palette_slot.get_visible()}")
    print(f"Palette slot children: {len(palette_slot.get_children())}")
    print(f"Buttons created: {list(palette.buttons.keys())}")
    print(f"Topology button sensitive: {palette.buttons['topology'].widget.get_sensitive()}")
    print("=" * 60)
    print("Window is displayed. Check if you see:")
    print("  - Vertical toolbar on far left (48px wide)")
    print("  - 4 buttons from top to bottom: Files, Pathways, Analyses, Topology")
    print("  - Topology button should appear disabled (grayed out)")
    print("  - Status bar at the bottom")
    print("=" * 60)
    print("Press Ctrl+C to exit")
    
    # Run GTK main loop
    try:
        Gtk.main()
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == '__main__':
    main()
