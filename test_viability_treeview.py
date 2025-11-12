#!/usr/bin/env python3
"""Test script to verify viability category TreeView creation."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.ui.panels.viability.structural_category import StructuralCategory
from shypn.ui.panels.viability.kinetic_category import KineticCategory
from shypn.ui.panels.viability.biological_category import BiologicalCategory
from shypn.ui.panels.viability.diagnosis_category import DiagnosisCategory


def test_category_initialization(category_class, category_name):
    """Test that a category initializes its TreeView correctly."""
    print(f"\n{'='*80}")
    print(f"Testing: {category_name}")
    print('='*80)
    
    # Create category instance
    category = category_class(model_canvas=None, expanded=False)
    
    # Check for TreeView components
    print(f"✓ Category created: {category}")
    print(f"✓ Has issues_store: {hasattr(category, 'issues_store')}")
    print(f"✓ issues_store value: {getattr(category, 'issues_store', 'NOT_FOUND')}")
    print(f"✓ Has issues_tree: {hasattr(category, 'issues_tree')}")
    print(f"✓ issues_tree value: {getattr(category, 'issues_tree', 'NOT_FOUND')}")
    print(f"✓ Has repair_button: {hasattr(category, 'repair_button')}")
    print(f"✓ Has select_column: {hasattr(category, 'select_column')}")
    
    # Check issues_store type
    if hasattr(category, 'issues_store') and category.issues_store:
        print(f"✓ issues_store type: {type(category.issues_store)}")
        print(f"✓ issues_store is Gtk.ListStore: {isinstance(category.issues_store, Gtk.ListStore)}")
        print(f"✓ issues_store n_columns: {category.issues_store.get_n_columns()}")
    else:
        print(f"❌ ERROR: issues_store not found or None!")
        return False
    
    # Check issues_tree type
    if hasattr(category, 'issues_tree') and category.issues_tree:
        print(f"✓ issues_tree type: {type(category.issues_tree)}")
        print(f"✓ issues_tree is Gtk.TreeView: {isinstance(category.issues_tree, Gtk.TreeView)}")
        print(f"✓ issues_tree n_columns: {len(category.issues_tree.get_columns())}")
        
        # List columns
        for i, col in enumerate(category.issues_tree.get_columns()):
            print(f"  Column {i}: {col.get_title()}")
    else:
        print(f"❌ ERROR: issues_tree not found or None!")
        return False
    
    print(f"\n✓ {category_name} PASSED")
    return True


def main():
    """Run all category tests."""
    print("="*80)
    print("VIABILITY CATEGORY TREEVIEW INITIALIZATION TEST")
    print("="*80)
    
    results = {}
    
    # Test each category
    categories = [
        (StructuralCategory, "Structural Category"),
        (KineticCategory, "Kinetic Category"),
        (BiologicalCategory, "Biological Category"),
        (DiagnosisCategory, "Diagnosis Category"),
    ]
    
    for category_class, category_name in categories:
        try:
            results[category_name] = test_category_initialization(category_class, category_name)
        except Exception as e:
            print(f"❌ {category_name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
            results[category_name] = False
    
    # Print summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\n{passed}/{total} categories passed")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
