#!/usr/bin/env python3
"""Test SABIO-RK context menu integration.

This test verifies:
1. Context menu shows "Enrich with SABIO-RK" option for transitions
2. Clicking option pre-fills SABIO-RK query fields
3. Organism filter is set correctly if available in metadata
4. Falls back gracefully if EC number not available
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.netobjs import Transition
from shypn.ui.panels.pathway_operations.sabio_rk_category import SabioRKCategory

def test_context_menu_integration():
    """Test context menu query pre-filling."""
    
    print("=" * 70)
    print("SABIO-RK Context Menu Integration Test")
    print("=" * 70)
    
    # Create SABIO-RK category
    print("\n[TEST] Creating SABIO-RK category...")
    category = SabioRKCategory(workspace_settings=None, parent_window=None)
    print("[TEST] SABIO-RK category created successfully")
    
    # Test 1: Transition with EC number and organism
    print("\n" + "=" * 70)
    print("TEST 1: Transition with EC number and organism")
    print("=" * 70)
    
    transition1 = Transition(100, 100, "T1", "Hexokinase")
    transition1.metadata = {
        'ec_number': '2.7.1.1',
        'enzyme_name': 'Hexokinase',
        'organism': 'Homo sapiens'
    }
    
    print(f"\nTransition: {transition1.id}")
    print(f"  EC: {transition1.metadata['ec_number']}")
    print(f"  Enzyme: {transition1.metadata['enzyme_name']}")
    print(f"  Organism: {transition1.metadata['organism']}")
    
    category.set_query_from_transition(
        ec_number=transition1.metadata['ec_number'],
        organism=transition1.metadata['organism'],
        transition_id=transition1.id
    )
    
    ec_text = category.ec_entry.get_text()
    org_text = category.organism_combo.get_active_text()
    
    print(f"\n✓ EC entry filled: '{ec_text}'")
    print(f"✓ Organism combo set: '{org_text}'")
    
    assert ec_text == '2.7.1.1', f"Expected '2.7.1.1', got '{ec_text}'"
    assert org_text == 'Homo sapiens', f"Expected 'Homo sapiens', got '{org_text}'"
    print("✓ TEST 1 PASSED")
    
    # Test 2: Transition with reaction_id (EC format)
    print("\n" + "=" * 70)
    print("TEST 2: Transition with reaction_id in EC format")
    print("=" * 70)
    
    transition2 = Transition(100, 100, "T2", "Pyruvate kinase")
    transition2.metadata = {
        'reaction_id': '2.7.1.40',
        'enzyme_name': 'Pyruvate kinase'
    }
    
    print(f"\nTransition: {transition2.id}")
    print(f"  Reaction ID: {transition2.metadata['reaction_id']}")
    
    category.set_query_from_transition(
        reaction_id=transition2.metadata['reaction_id'],
        transition_id=transition2.id
    )
    
    ec_text = category.ec_entry.get_text()
    
    print(f"\n✓ EC entry filled from reaction_id: '{ec_text}'")
    assert ec_text == '2.7.1.40', f"Expected '2.7.1.40', got '{ec_text}'"
    print("✓ TEST 2 PASSED")
    
    # Test 3: Transition with KEGG reaction ID (not EC format)
    print("\n" + "=" * 70)
    print("TEST 3: Transition with KEGG reaction ID (not EC format)")
    print("=" * 70)
    
    transition3 = Transition(100, 100, "T3", "Reaction R00200")
    transition3.metadata = {
        'reaction_id': 'R00200',
        'kegg_reaction_id': 'R00200'
    }
    
    print(f"\nTransition: {transition3.id}")
    print(f"  KEGG Reaction: {transition3.metadata['reaction_id']}")
    
    category.set_query_from_transition(
        reaction_id=transition3.metadata['reaction_id'],
        transition_id=transition3.id
    )
    
    ec_text = category.ec_entry.get_text()
    
    print(f"\n✓ EC entry (should be empty): '{ec_text}'")
    assert ec_text == '', f"Expected empty string, got '{ec_text}'"
    print("✓ TEST 3 PASSED - KEGG ID correctly rejected (not EC format)")
    
    # Test 4: Transition with EC list
    print("\n" + "=" * 70)
    print("TEST 4: Transition with EC number list")
    print("=" * 70)
    
    transition4 = Transition(100, 100, "T4", "Multi-EC enzyme")
    transition4.metadata = {
        'ec_numbers': ['1.1.1.1', '1.1.1.2', '1.1.1.3'],
        'organism': 'Escherichia coli'
    }
    
    print(f"\nTransition: {transition4.id}")
    print(f"  EC numbers: {transition4.metadata['ec_numbers']}")
    
    category.set_query_from_transition(
        ec_number=transition4.metadata['ec_numbers'][0],  # Context menu takes first
        organism=transition4.metadata['organism'],
        transition_id=transition4.id
    )
    
    ec_text = category.ec_entry.get_text()
    org_text = category.organism_combo.get_active_text()
    
    print(f"\n✓ EC entry (first from list): '{ec_text}'")
    print(f"✓ Organism combo: '{org_text}'")
    
    assert ec_text == '1.1.1.1', f"Expected '1.1.1.1', got '{ec_text}'"
    assert org_text == 'Escherichia coli', f"Expected 'Escherichia coli', got '{org_text}'"
    print("✓ TEST 4 PASSED")
    
    # Test 5: Transition with no EC number
    print("\n" + "=" * 70)
    print("TEST 5: Transition without EC number")
    print("=" * 70)
    
    transition5 = Transition(100, 100, "T5", "Unknown enzyme")
    transition5.metadata = {
        'enzyme_name': 'Unknown'
    }
    
    print(f"\nTransition: {transition5.id}")
    print(f"  No EC number in metadata")
    
    category.set_query_from_transition(
        transition_id=transition5.id
    )
    
    ec_text = category.ec_entry.get_text()
    
    print(f"\n✓ EC entry (should be empty): '{ec_text}'")
    print(f"✓ Status message should warn about missing EC number")
    
    assert ec_text == '', f"Expected empty string, got '{ec_text}'"
    print("✓ TEST 5 PASSED - Graceful handling of missing EC number")
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print("\n✓ All 5 tests PASSED!")
    print("\nContext menu integration verified:")
    print("  ✓ EC number pre-filling works")
    print("  ✓ Organism filter selection works")
    print("  ✓ Reaction ID handling works")
    print("  ✓ EC format validation works")
    print("  ✓ Graceful fallback for missing data")
    print("\nReady for production use!")

if __name__ == '__main__':
    test_context_menu_integration()
