#!/usr/bin/env python3
"""Test script to verify pathway panel window close behavior.

This script tests that clicking the X button on the floating pathway panel
window properly hides the window instead of causing a segmentation fault.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.helpers.pathway_panel_loader import create_pathway_panel

def test_close_behavior():
    """Test that closing the window doesn't crash."""
    print("Creating pathway panel...")
    panel = create_pathway_panel()
    
    print("Floating panel...")
    panel.float()
    
    print("Panel is now floating. You can:")
    print("  1. Click the X button to close - should hide, not crash")
    print("  2. Click the float button (⇲) to dock back")
    print("  3. Close this window to exit cleanly")
    
    # Run GTK main loop
    try:
        Gtk.main()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    
    print("✅ Test completed without segfault!")

if __name__ == '__main__':
    test_close_behavior()
