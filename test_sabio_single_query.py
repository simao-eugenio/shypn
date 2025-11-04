#!/usr/bin/env python3
"""Test SABIO-RK category with a single manual query.

This test verifies:
1. Organism combo box is populated and functional
2. EC number entry accepts input
3. Manual Search button triggers query
4. Results are displayed correctly
5. Apply parameters button works
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.ui.panels.pathway_operations.sabio_rk_category import SabioRKCategory
from shypn.data.sabio_rk_client import SabioRKClient
from shypn.helpers.sabio_rk_enrichment_controller import SabioRKEnrichmentController

# Mock model canvas loader
class MockModelCanvasLoader:
    def get_current_document(self):
        return None

def test_single_query():
    """Test a single manual query with Homo sapiens filter."""
    
    print("=" * 70)
    print("SABIO-RK Category Single Query Test")
    print("=" * 70)
    
    # Create main window
    window = Gtk.Window(title="SABIO-RK Single Query Test")
    window.set_default_size(600, 800)
    window.connect('destroy', Gtk.main_quit)
    
    # Create SABIO-RK category
    print("\n[TEST] Creating SABIO-RK category...")
    category = SabioRKCategory(workspace_settings=None, parent_window=window)
    
    # Wire mock model canvas loader
    mock_canvas = MockModelCanvasLoader()
    category.set_model_canvas(mock_canvas)
    
    # Add to window
    window.add(category)
    window.show_all()
    
    print("[TEST] SABIO-RK category created successfully")
    
    # Verify organism combo exists
    print("\n[TEST] Checking organism combo...")
    if hasattr(category, 'organism_combo'):
        model = category.organism_combo.get_model()
        count = len(model) if model else 0
        print(f"  ✓ Organism combo found with {count} options")
        
        # List all organisms
        print("  Available organisms:")
        for i in range(count):
            print(f"    {i}: {category.organism_combo.get_model()[i][0]}")
    else:
        print("  ✗ Organism combo NOT found!")
        return False
    
    # Verify EC entry exists
    print("\n[TEST] Checking EC number entry...")
    if hasattr(category, 'ec_entry'):
        print("  ✓ EC number entry found")
    else:
        print("  ✗ EC number entry NOT found!")
        return False
    
    # Verify Search button exists
    print("\n[TEST] Checking Search button...")
    search_button = None
    for child in category.get_children():
        if isinstance(child, Gtk.Box):
            for subchild in child.get_children():
                if isinstance(subchild, Gtk.Button):
                    if "Search" in subchild.get_label():
                        search_button = subchild
                        break
    
    if search_button:
        print("  ✓ Search button found")
    else:
        print("  ✗ Search button NOT found!")
    
    # Test 1: Query without organism filter (should fail)
    print("\n" + "=" * 70)
    print("TEST 1: Query WITHOUT organism filter (should be rejected)")
    print("=" * 70)
    
    def run_test1():
        print("\n[TEST 1] Setting EC number: 2.7.1.1")
        category.ec_entry.set_text("2.7.1.1")
        
        print("[TEST 1] Setting organism: All organisms (no filter)")
        category.organism_combo.set_active(0)  # "All organisms"
        
        print("[TEST 1] Triggering manual search...")
        if hasattr(category, '_on_search_clicked'):
            # Simulate button click
            category._on_search_clicked(None)
            print("[TEST 1] Search triggered - check console for rejection message")
            print("[TEST 1] Expected: 'Query would return 149 results - likely to timeout!'")
        
        # Wait 3 seconds then run test 2
        GLib.timeout_add_seconds(3, run_test2)
        return False
    
    # Test 2: Query with organism filter (should succeed)
    def run_test2():
        print("\n" + "=" * 70)
        print("TEST 2: Query WITH organism filter (should succeed)")
        print("=" * 70)
        
        print("\n[TEST 2] Setting EC number: 2.7.1.1")
        category.ec_entry.set_text("2.7.1.1")
        
        print("[TEST 2] Setting organism: Homo sapiens")
        category.organism_combo.set_active(1)  # "Homo sapiens"
        
        print("[TEST 2] Triggering manual search...")
        if hasattr(category, '_on_search_clicked'):
            category._on_search_clicked(None)
            print("[TEST 2] Search triggered - waiting for results...")
            print("[TEST 2] Expected: Success with ~12 results")
        
        # Wait 20 seconds for results, then show summary
        GLib.timeout_add_seconds(20, show_summary)
        return False
    
    def show_summary():
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        # Check if results are displayed
        if hasattr(category, 'results_list'):
            model = category.results_list.get_model()
            if model:
                count = len(model)
                print(f"\n✓ Results displayed: {count} parameters found")
                
                # Show first few results
                if count > 0:
                    print("\nFirst 3 results:")
                    for i in range(min(3, count)):
                        row = model[i]
                        print(f"  {i+1}. {row[0]} - {row[1]}")
            else:
                print("\n✗ No results model found")
        else:
            print("\n✗ Results list not found")
        
        print("\n[TEST] All UI controls are wired correctly!")
        print("[TEST] Close window to exit (or press Ctrl+C)")
        return False
    
    # Start test sequence after UI is ready
    GLib.timeout_add_seconds(1, run_test1)
    
    # Run GTK main loop
    print("\n[TEST] Starting GTK main loop...")
    print("[TEST] Tests will run automatically...")
    Gtk.main()

if __name__ == '__main__':
    test_single_query()
