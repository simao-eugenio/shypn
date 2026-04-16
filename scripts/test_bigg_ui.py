#!/usr/bin/env python3
"""Test BiGG category UI integration.

This script creates a standalone window with just the BiGG category
to test the UI components without the full shypn application.

Usage:
    python scripts/test_bigg_ui.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.ui.panels.pathway_operations.bigg_category import BiGGCategory


def main():
    """Run standalone BiGG category test."""
    # Create window
    window = Gtk.Window(title="BiGG Category Test")
    window.set_default_size(600, 700)
    window.connect("destroy", Gtk.main_quit)
    
    # Create BiGG category
    bigg_category = BiGGCategory()
    bigg_category.set_expanded(True)  # Expand by default for testing
    
    # Add to window
    window.add(bigg_category)
    window.show_all()
    
    print("=" * 80)
    print("BiGG Category UI Test")
    print("=" * 80)
    print("✓ Window created")
    print("✓ BiGG category loaded")
    print("✓ Fetching models from BiGG API...")
    print()
    print("Instructions:")
    print("  1. Wait for model list to load")
    print("  2. Try organism filter dropdown")
    print("  3. Try search entry")
    print("  4. Select a model (e.g., e_coli_core)")
    print("  5. Check metadata panel updates")
    print("  6. Click 'Import to Project' button")
    print()
    print("Close window to exit.")
    print("=" * 80)
    
    Gtk.main()


if __name__ == "__main__":
    main()
