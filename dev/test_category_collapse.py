#!/usr/bin/env python3
"""Test Category Collapse Behavior - Verify categories stack at top when collapsed."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.ui.file_panel_v2 import FilePanelV2


def main():
    print("=" * 70)
    print("Category Collapse Test")
    print("=" * 70)
    print()
    print("Instructions:")
    print("  1. Panel starts with Files category EXPANDED")
    print("  2. Click 'Files' title to collapse it")
    print("  3. All categories should stack tightly at the top")
    print("  4. Click any category title to expand it again")
    print()
    print("Expected behavior:")
    print("  ✓ Collapsed categories take minimal space")
    print("  ✓ Expanded Files category fills available space")
    print("  ✓ Categories stack at top when all collapsed")
    print("=" * 70)
    print()
    
    win = Gtk.Window(title="Category Collapse Test")
    win.set_default_size(400, 600)
    win.connect('destroy', Gtk.main_quit)
    
    # Create file panel
    panel = FilePanelV2(base_path=os.path.join(os.path.dirname(__file__), '..', 'workspace'))
    panel.set_parent_window(win)
    
    win.add(panel.get_widget())
    win.show_all()
    
    print("[TEST] Window shown - try collapsing/expanding categories")
    
    Gtk.main()


if __name__ == '__main__':
    main()
