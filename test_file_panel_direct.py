#!/usr/bin/env python3
"""Direct test of file panel TreeView."""

import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# Add src to path
sys.path.insert(0, 'src')

from shypn.helpers.file_panel_v3_loader import FilePanelV3Loader

def main():
    # Create loader
    loader = FilePanelV3Loader()
    
    print(f"Base path: {loader.base_path}")
    print(f"Tree view: {loader.tree_view}")
    print(f"Tree store rows: {len(loader.tree_store)}")
    print(f"Tree view visible: {loader.tree_view.get_visible()}")
    print(f"Tree scroll visible: {loader.tree_scroll.get_visible()}")
    
    # Print first few items in tree
    print("\nTree items:")
    iter = loader.tree_store.get_iter_first()
    count = 0
    while iter and count < 10:
        name = loader.tree_store.get_value(iter, 0)
        path = loader.tree_store.get_value(iter, 1)
        is_dir = loader.tree_store.get_value(iter, 2)
        print(f"  {'📁' if is_dir else '📄'} {name}")
        iter = loader.tree_store.iter_next(iter)
        count += 1
    
    # Create test window
    win = Gtk.Window()
    win.set_title("File Panel Test")
    win.set_default_size(400, 600)
    win.connect('destroy', Gtk.main_quit)
    
    # Add file panel content
    win.add(loader.content)
    
    win.show_all()
    
    print("\nWindow shown - check if TreeView is visible")
    print(f"After show_all - Tree view visible: {loader.tree_view.get_visible()}")
    print(f"After show_all - Tree scroll visible: {loader.tree_scroll.get_visible()}")
    
    Gtk.main()

if __name__ == '__main__':
    main()
