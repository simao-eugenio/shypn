#!/usr/bin/env python3
"""Visual test for KEGG category content.

This test creates a window showing just the KEGG category
to verify that all content is properly displayed.
"""
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# Add src to path
sys.path.insert(0, 'src')

from shypn.ui.panels.pathway_operations.kegg_category import KEGGCategory


class TestWindow(Gtk.Window):
    """Test window to visually verify KEGG category."""
    
    def __init__(self):
        super().__init__(title="KEGG Category - Visual Test")
        self.set_default_size(600, 700)
        self.set_border_width(10)
        
        # Create main container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)
        
        # Add title
        title = Gtk.Label()
        title.set_markup("<big><b>KEGG Category Content Test</b></big>")
        vbox.pack_start(title, False, False, 0)
        
        # Add instructions
        instructions = Gtk.Label()
        instructions.set_markup(
            "<b>Test Instructions:</b>\n"
            "1. Click the arrow (▶) to expand the KEGG category\n"
            "2. Verify you see:\n"
            "   • Pathway ID input field\n"
            "   • Options section (cofactors checkbox, scale spinner)\n"
            "   • Preview section (text view)\n"
            "   • Import button\n"
            "3. Try entering a pathway ID (e.g., 'hsa00010')\n"
            "4. Check if all fields are accessible"
        )
        instructions.set_xalign(0.0)
        instructions.set_line_wrap(True)
        vbox.pack_start(instructions, False, False, 0)
        
        # Add separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(sep, False, False, 0)
        
        # Create KEGG category - START EXPANDED for this test
        print("Creating KEGG Category (expanded)...")
        self.kegg = KEGGCategory(expanded=True)
        print(f"Category created: {self.kegg}")
        print(f"  - Is expanded: {self.kegg.is_expanded()}")
        print(f"  - Has pathway_id_entry: {hasattr(self.kegg, 'pathway_id_entry')}")
        print(f"  - Has import_button: {hasattr(self.kegg, 'import_button')}")
        
        # Add category to window
        vbox.pack_start(self.kegg, True, True, 0)
        
        # Add status bar
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        status_label = Gtk.Label()
        status_label.set_markup("<span foreground='green'><b>✓ Category loaded!</b></span>")
        status_box.pack_start(status_label, False, False, 0)
        
        # Add button to toggle expansion
        toggle_btn = Gtk.Button(label="Toggle Expand/Collapse")
        toggle_btn.connect('clicked', self._on_toggle)
        status_box.pack_start(toggle_btn, False, False, 0)
        
        close_button = Gtk.Button(label="Close")
        close_button.connect('clicked', lambda w: Gtk.main_quit())
        status_box.pack_end(close_button, False, False, 0)
        
        vbox.pack_start(status_box, False, False, 0)
        
        # Connect window signals
        self.connect('destroy', Gtk.main_quit())
        
        # Show all widgets
        self.show_all()
        
        print("\n" + "="*60)
        print("KEGG CATEGORY VISUAL TEST STARTED")
        print("="*60)
        print("If the category content is not visible:")
        print("1. Click the ▶ arrow to expand")
        print("2. OR click 'Toggle Expand/Collapse' button")
        print("="*60 + "\n")
    
    def _on_toggle(self, button):
        """Toggle category expansion."""
        current = self.kegg.is_expanded()
        self.kegg.set_expanded(not current)
        print(f"Toggled expansion: was {current}, now {not current}")


def main():
    """Run the visual test."""
    print("Starting KEGG Category Visual Test...")
    print("-" * 60)
    
    try:
        window = TestWindow()
        Gtk.main()
        print("\nTest window closed successfully")
        return 0
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
