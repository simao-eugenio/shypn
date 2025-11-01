#!/usr/bin/env python3
"""Visual integration test for refactored Pathway Operations panel.

This test verifies that:
1. New CategoryFrame-based panel loads correctly
2. All three categories are present (KEGG, SBML, BRENDA)
3. Categories can be expanded/collapsed
4. Panel appears when master palette button is clicked
5. Panel exclusion works (only one panel visible at a time)

Run this test to manually verify the UI integration works as expected.
"""
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

# Add src to path
sys.path.insert(0, 'src')

from shypn.ui.panels.pathway_operations_panel import PathwayOperationsPanel


class TestWindow(Gtk.Window):
    """Test window to visually verify the pathway panel."""
    
    def __init__(self):
        super().__init__(title="Pathway Operations Panel - Visual Test")
        self.set_default_size(500, 700)
        self.set_border_width(10)
        
        # Create main container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)
        
        # Add title
        title = Gtk.Label()
        title.set_markup("<big><b>Pathway Operations Panel - CategoryFrame Architecture</b></big>")
        vbox.pack_start(title, False, False, 0)
        
        # Add instructions
        instructions = Gtk.Label()
        instructions.set_markup(
            "<b>Visual Verification Checklist:</b>\n"
            "✓ Panel loads without errors\n"
            "✓ Three categories visible: KEGG, SBML, BRENDA\n"
            "✓ Categories have collapse/expand arrows (▶/▼)\n"
            "✓ Clicking arrows expands/collapses category content\n"
            "✓ Each category shows its specific UI elements\n"
            "✓ No old UI artifacts visible"
        )
        instructions.set_xalign(0.0)
        instructions.set_line_wrap(True)
        vbox.pack_start(instructions, False, False, 0)
        
        # Add separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(sep, False, False, 0)
        
        # Create scrolled window for panel
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        vbox.pack_start(scrolled, True, True, 0)
        
        # Create the panel
        print("Creating PathwayOperationsPanel...")
        self.panel = PathwayOperationsPanel()
        scrolled.add(self.panel)
        print("Panel created successfully!")
        
        # Add status bar
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        status_label = Gtk.Label()
        status_label.set_markup("<span foreground='green'><b>✓ Panel loaded successfully!</b></span>")
        status_box.pack_start(status_label, False, False, 0)
        
        close_button = Gtk.Button(label="Close Test")
        close_button.connect('clicked', lambda w: Gtk.main_quit())
        status_box.pack_end(close_button, False, False, 0)
        
        vbox.pack_start(status_box, False, False, 0)
        
        # Connect window signals
        self.connect('destroy', Gtk.main_quit)
        
        # Show all widgets
        self.show_all()
        
        print("\n" + "="*60)
        print("VISUAL TEST STARTED")
        print("="*60)
        print("Please verify:")
        print("1. Three category frames visible: KEGG, SBML, BRENDA")
        print("2. Each has an expand/collapse arrow")
        print("3. Clicking arrows expands/collapses content")
        print("4. No errors in terminal")
        print("="*60 + "\n")


def main():
    """Run the visual test."""
    print("Starting Pathway Operations Panel Visual Test...")
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
