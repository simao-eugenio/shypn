#!/usr/bin/env python3
"""Quick test to verify pathway panel shows correctly in stack mode (like in main app)."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.helpers.pathway_panel_loader import create_pathway_panel


class StackTestWindow(Gtk.Window):
    """Minimal reproduction of how shypn.py uses pathway panel."""
    
    def __init__(self):
        super().__init__(title="Pathway Panel Stack Test")
        self.set_default_size(600, 500)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_start(10)
        vbox.set_margin_end(10)
        vbox.set_margin_top(10)
        self.add(vbox)
        
        # Instructions
        label = Gtk.Label()
        label.set_markup(
            "<b>Stack Mode Test (Reproduces shypn.py setup)</b>\n\n"
            "Click 'Show Panel' - watch for Error 71\n"
            "Verify widgets are visible (radio buttons, entries, etc.)"
        )
        vbox.pack_start(label, False, False, 0)
        
        # Control button
        self.show_button = Gtk.Button(label="Show Pathway Panel")
        self.show_button.connect('clicked', self.on_show_clicked)
        vbox.pack_start(self.show_button, False, False, 0)
        
        vbox.pack_start(Gtk.Separator(), False, False, 5)
        
        # Create GtkStack (like in shypn.py)
        self.stack = Gtk.Stack()
        vbox.pack_start(self.stack, True, True, 0)
        
        # Create container for pathway panel
        self.pathways_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.stack.add_named(self.pathways_container, 'pathways')
        
        # Load pathway panel
        print("[TEST] Creating pathway panel...")
        self.pathway_panel = create_pathway_panel()
        
        # Add to stack (like shypn.py does)
        print("[TEST] Adding to stack...")
        self.pathway_panel.add_to_stack(self.stack, self.pathways_container, 'pathways')
        
        # Hide container initially (like shypn.py does)
        print("[TEST] Hiding container initially...")
        self.pathways_container.set_visible(False)
        self.pathways_container.set_no_show_all(False)
        
        # Hide stack
        self.stack.set_visible(False)
        
        print("[TEST] Setup complete. Click 'Show Pathway Panel' button.")
    
    def on_show_clicked(self, button):
        """Show the pathway panel (like Master Palette does)."""
        print("\n[TEST] ========== Showing Pathway Panel ==========")
        print("[TEST] Calling pathway_panel.show_in_stack()...")
        
        try:
            self.pathway_panel.show_in_stack()
            print("[TEST] ✓ show_in_stack() completed without error")
            
            # Verify widgets are visible
            builder = self.pathway_panel.builder
            notebook = builder.get_object('pathway_notebook')
            
            if notebook:
                print(f"[TEST] Notebook visible: {notebook.get_visible()}")
                
                # Check first tab (KEGG) - FIXED IDs
                kegg_database_radio = builder.get_object('kegg_database_radio')
                kegg_database_box = builder.get_object('kegg_database_box')
                kegg_local_radio = builder.get_object('kegg_local_radio')
                kegg_local_box = builder.get_object('kegg_local_box')
                pathway_id_entry = builder.get_object('pathway_id_entry')
                
                print(f"[TEST] KEGG database radio: {kegg_database_radio.get_visible() if kegg_database_radio else 'NOT FOUND'}")
                print(f"[TEST] KEGG database box: {kegg_database_box.get_visible() if kegg_database_box else 'NOT FOUND'}")
                print(f"[TEST] KEGG local radio: {kegg_local_radio.get_visible() if kegg_local_radio else 'NOT FOUND'}")
                print(f"[TEST] KEGG local box: {kegg_local_box.get_visible() if kegg_local_box else 'NOT FOUND'}")
                print(f"[TEST] Pathway ID entry: {pathway_id_entry.get_visible() if pathway_id_entry else 'NOT FOUND'}")
                
                print("[TEST] ✓ Widgets found and visibility checked")
            else:
                print("[TEST] ✗ ERROR: Notebook not found!")
                
        except Exception as e:
            print(f"[TEST] ✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print("[TEST] ========== Show Complete ==========\n")


def main():
    print("=" * 70)
    print("Pathway Panel Stack Mode Test")
    print("=" * 70)
    print("This reproduces how shypn.py uses the pathway panel.")
    print("Watch for: Gdk-Message: Error 71 (Protocol error)")
    print("=" * 70)
    print()
    
    win = StackTestWindow()
    win.connect('destroy', Gtk.main_quit)
    win.show_all()
    
    Gtk.main()


if __name__ == '__main__':
    main()
