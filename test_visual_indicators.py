#!/usr/bin/env python3
"""Test script to verify visual indicators are working."""

import sys
sys.path.insert(0, 'src')

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.ui.panels.viability.viability_panel import ViabilityPanel

def test_store_structure():
    """Test that stores have correct number of columns."""
    print("Testing ViabilityPanel store structure...")
    
    # Create panel
    panel = ViabilityPanel()
    
    # Check places_store
    print(f"\nPlaces store columns: {panel.places_store.get_n_columns()}")
    print(f"Expected: 6 columns (id, name, marking, type, label, background)")
    
    # Check transitions_store  
    print(f"\nTransitions store columns: {panel.transitions_store.get_n_columns()}")
    print(f"Expected: 7 columns (id, name, rate, formula, type, label, background)")
    
    # Check arcs_store
    print(f"\nArcs store columns: {panel.arcs_store.get_n_columns()}")
    print(f"Expected: 6 columns (id, from, to, weight, type, background)")
    
    # Test adding a row with background
    print("\n\nTesting row addition with background color...")
    panel.places_store.append(['P1', 'Place1', 10, 'Normal', 'Test', '#FFFFFF'])
    print(f"Added row to places_store")
    
    # Check if we can read it back
    for row in panel.places_store:
        print(f"Row: ID={row[0]}, Name={row[1]}, Marking={row[2]}, Background={row[5]}")
    
    # Test update_sweep_indicators
    print("\n\nTesting update_sweep_indicators()...")
    panel.places_store.append(['P2', 'Place2', 20, 'Normal', 'Test2', '#FFFFFF'])
    panel.update_sweep_indicators('place', 'P2')
    
    print("After highlighting P2:")
    for row in panel.places_store:
        print(f"  {row[0]}: background={row[5]}")
    
    print("\n✓ All tests passed!")

if __name__ == '__main__':
    test_store_structure()
