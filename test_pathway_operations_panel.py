#!/usr/bin/env python3
"""Test the new Pathway Operations panel with CategoryFrame architecture.

This script verifies:
1. Panel loads correctly
2. All three categories are present (KEGG, SBML, BRENDA)
3. Categories can be expanded/collapsed
4. UI elements are accessible
"""
import os
import sys

# Suppress Wayland warnings
os.environ['G_MESSAGES_DEBUG'] = ''

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
except Exception as e:
    print(f'ERROR: GTK3 not available: {e}', file=sys.stderr)
    sys.exit(1)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.ui.panels.pathway_operations_panel import PathwayOperationsPanel

def test_panel_creation():
    """Test that panel creates successfully."""
    print("=" * 60)
    print("TEST 1: Panel Creation")
    print("=" * 60)
    
    try:
        panel = PathwayOperationsPanel()
        print("✓ Panel created successfully")
        
        # Check that categories exist
        assert hasattr(panel, 'kegg_category'), "Missing KEGG category"
        print("✓ KEGG category exists")
        
        assert hasattr(panel, 'sbml_category'), "Missing SBML category"
        print("✓ SBML category exists")
        
        assert hasattr(panel, 'brenda_category'), "Missing BRENDA category"
        print("✓ BRENDA category exists")
        
        return True
    except Exception as e:
        print(f"✗ Panel creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_category_frames():
    """Test that CategoryFrames are properly set up."""
    print("\n" + "=" * 60)
    print("TEST 2: CategoryFrame Structure")
    print("=" * 60)
    
    try:
        panel = PathwayOperationsPanel()
        
        # Check that categories ARE CategoryFrames (inherit from it)
        from shypn.ui.category_frame import CategoryFrame
        
        assert isinstance(panel.kegg_category, CategoryFrame), "KEGG not a CategoryFrame"
        print("✓ KEGG is a CategoryFrame")
        
        assert isinstance(panel.sbml_category, CategoryFrame), "SBML not a CategoryFrame"
        print("✓ SBML is a CategoryFrame")
        
        assert isinstance(panel.brenda_category, CategoryFrame), "BRENDA not a CategoryFrame"
        print("✓ BRENDA is a CategoryFrame")
        
        # Check they have titles
        assert hasattr(panel.kegg_category, 'title'), "KEGG missing title"
        assert panel.kegg_category.title == "KEGG", f"KEGG wrong title: {panel.kegg_category.title}"
        print("✓ KEGG title correct")
        
        assert hasattr(panel.sbml_category, 'title'), "SBML missing title"
        assert panel.sbml_category.title == "SBML", f"SBML wrong title: {panel.sbml_category.title}"
        print("✓ SBML title correct")
        
        assert hasattr(panel.brenda_category, 'title'), "BRENDA missing title"
        assert panel.brenda_category.title == "BRENDA", f"BRENDA wrong title: {panel.brenda_category.title}"
        print("✓ BRENDA title correct")
        
        return True
    except Exception as e:
        print(f"✗ CategoryFrame check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_elements():
    """Test that UI elements are accessible."""
    print("\n" + "=" * 60)
    print("TEST 3: UI Elements")
    print("=" * 60)
    
    try:
        panel = PathwayOperationsPanel()
        
        # KEGG UI elements
        kegg = panel.kegg_category
        assert hasattr(kegg, 'pathway_id_entry'), "KEGG missing pathway_id_entry"
        assert hasattr(kegg, 'import_button'), "KEGG missing import_button"
        print("✓ KEGG UI elements present")
        
        # SBML UI elements
        sbml = panel.sbml_category
        assert hasattr(sbml, 'local_radio'), "SBML missing local_radio"
        assert hasattr(sbml, 'import_button'), "SBML missing import_button"
        print("✓ SBML UI elements present")
        
        # BRENDA UI elements
        brenda = panel.brenda_category
        assert hasattr(brenda, 'email_entry'), "BRENDA missing email_entry"
        assert hasattr(brenda, 'search_button'), "BRENDA missing search_button"
        print("✓ BRENDA UI elements present")
        
        return True
    except Exception as e:
        print(f"✗ UI elements check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_flow():
    """Test that data flow signals are connected."""
    print("\n" + "=" * 60)
    print("TEST 4: Data Flow Signals")
    print("=" * 60)
    
    try:
        panel = PathwayOperationsPanel()
        
        # Check that callbacks are set
        assert hasattr(panel.kegg_category, 'import_complete_callback'), "KEGG missing callback attribute"
        assert panel.kegg_category.import_complete_callback is not None, "KEGG callback not set"
        print("✓ KEGG→BRENDA data flow configured")
        
        assert hasattr(panel.sbml_category, 'import_complete_callback'), "SBML missing callback attribute"
        assert panel.sbml_category.import_complete_callback is not None, "SBML callback not set"
        print("✓ SBML→BRENDA data flow configured")
        
        assert hasattr(panel.brenda_category, 'receive_import_data'), "BRENDA missing receive method"
        print("✓ BRENDA can receive import data")
        
        return True
    except Exception as e:
        print(f"✗ Data flow check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_expansion():
    """Test that categories can be expanded/collapsed."""
    print("\n" + "=" * 60)
    print("TEST 5: Category Expansion")
    print("=" * 60)
    
    try:
        panel = PathwayOperationsPanel()
        
        # Test KEGG expansion (use is_expanded method from CategoryFrame)
        kegg = panel.kegg_category
        initial_state = kegg.is_expanded()
        kegg.set_expanded(not initial_state)
        new_state = kegg.is_expanded()
        assert new_state != initial_state, "KEGG expansion didn't change"
        print(f"✓ KEGG expansion works (initial={initial_state}, new={new_state})")
        
        # Test SBML expansion
        sbml = panel.sbml_category
        initial_state = sbml.is_expanded()
        sbml.set_expanded(not initial_state)
        new_state = sbml.is_expanded()
        assert new_state != initial_state, "SBML expansion didn't change"
        print(f"✓ SBML expansion works (initial={initial_state}, new={new_state})")
        
        # Test BRENDA expansion
        brenda = panel.brenda_category
        initial_state = brenda.is_expanded()
        brenda.set_expanded(not initial_state)
        new_state = brenda.is_expanded()
        assert new_state != initial_state, "BRENDA expansion didn't change"
        print(f"✓ BRENDA expansion works (initial={initial_state}, new={new_state})")
        
        return True
    except Exception as e:
        print(f"✗ Expansion test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_loader():
    """Test that loader works with new panel."""
    print("\n" + "=" * 60)
    print("TEST 6: Loader Integration")
    print("=" * 60)
    
    try:
        from shypn.helpers.pathway_panel_loader import PathwayPanelLoader
        
        loader = PathwayPanelLoader()
        window = loader.load()
        
        assert window is not None, "Loader didn't return window"
        print("✓ Loader created window")
        
        assert loader.panel is not None, "Loader didn't create panel"
        print("✓ Loader created panel")
        
        assert isinstance(loader.panel, PathwayOperationsPanel), "Wrong panel type"
        print("✓ Loader created correct panel type")
        
        # Check legacy compatibility
        assert loader.kegg_import_controller is not None, "Legacy KEGG controller missing"
        assert loader.sbml_import_controller is not None, "Legacy SBML controller missing"
        assert loader.brenda_enrichment_controller is not None, "Legacy BRENDA controller missing"
        print("✓ Legacy compatibility maintained")
        
        return True
    except Exception as e:
        print(f"✗ Loader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PATHWAY OPERATIONS PANEL - CATEGORY FRAME TESTS")
    print("=" * 60 + "\n")
    
    results = []
    
    # Run tests
    results.append(("Panel Creation", test_panel_creation()))
    results.append(("CategoryFrame Structure", test_category_frames()))
    results.append(("UI Elements", test_ui_elements()))
    results.append(("Data Flow Signals", test_data_flow()))
    results.append(("Category Expansion", test_expansion()))
    results.append(("Loader Integration", test_loader()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests PASSED! Panel is ready for use.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) FAILED. Check output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
