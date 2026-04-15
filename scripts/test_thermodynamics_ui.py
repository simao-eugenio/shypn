#!/usr/bin/env python3
"""Test script for THERMODYNAMICS category UI.

This script tests the newly created UI components.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.data.canvas.document_model import DocumentModel
from shypn.ui.panels.pathway_operations.thermodynamics import ThermodynamicsCategory


class TestWindow(Gtk.Window):
    """Test window for THERMODYNAMICS category."""
    
    def __init__(self):
        super().__init__(title="THERMODYNAMICS Category Test")
        self.set_default_size(600, 800)
        
        # Create test document with places
        self.document = DocumentModel()
        self.document.create_place(100, 100, label="ATP")
        self.document.create_place(200, 100, label="Glucose (C00031)")
        self.document.create_place(300, 100, label="NADH")
        self.document.create_place(400, 100, label="Pyruvate")
        self.document.create_place(500, 100, label="Unknown Metabolite")
        
        # Create reversible transition for validation testing
        t1 = self.document.create_transition(150, 200, label="R1")
        t1.properties['is_reversible'] = True
        t1.properties['k_forward'] = 1e6
        t1.properties['k_reverse'] = 1e3
        
        # Create arcs
        p1 = self.document.places[0]  # ATP
        p2 = self.document.places[1]  # Glucose
        self.document.create_arc(p1, t1, weight=1)
        self.document.create_arc(t1, p2, weight=1)
        
        # Create THERMODYNAMICS category
        self.thermodynamics_category = ThermodynamicsCategory(expanded=True)
        self.thermodynamics_category.set_document(self.document)
        
        # Layout
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.thermodynamics_category)
        
        self.add(scrolled)
        
        # Connect destroy signal
        self.connect("destroy", Gtk.main_quit)
    
    def show(self):
        """Show window and all widgets."""
        self.show_all()
        
        # Print test info
        print("=" * 60)
        print("THERMODYNAMICS Category UI Test")
        print("=" * 60)
        print(f"\nTest document created:")
        print(f"  Places: {len(self.document.places)}")
        print(f"  Transitions: {len(self.document.transitions)}")
        print(f"  Arcs: {len(self.document.arcs)}")
        print(f"\nThermodynamic settings:")
        for key, value in self.document.thermodynamic_settings.items():
            print(f"  {key}: {value}")
        print("\n" + "=" * 60)
        print("Test Instructions:")
        print("=" * 60)
        print("1. Settings Section:")
        print("   - Try changing pH slider")
        print("   - Try different presets")
        print("   - Click 'Apply Settings'")
        print("\n2. Mapping Section:")
        print("   - Click 'Auto-Map Compounds'")
        print("   - Edit compound IDs in table")
        print("   - Try Remove/Clear buttons")
        print("\n3. Validation Section:")
        print("   - Click 'Run Validation'")
        print("   - Check results display")
        print("\nClose window when done.")
        print("=" * 60)


def main():
    """Run test application."""
    print("Initializing GTK test application...")
    
    try:
        window = TestWindow()
        window.show()
        
        print("\nStarting GTK main loop...")
        Gtk.main()
        
        print("\nTest completed successfully!")
        return True
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
