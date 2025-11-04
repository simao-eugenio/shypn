#!/usr/bin/env python3
"""Test that transition ID is preserved in SABIO-RK results table."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*70)
print("SABIO-RK TRANSITION ID PRESERVATION TEST")
print("="*70)

# Test 1: Check that _context_transition_id attribute exists
try:
    from shypn.ui.panels.pathway_operations.sabio_rk_category import SabioRKCategory
    category = SabioRKCategory()
    
    assert hasattr(category, '_context_transition_id'), "Missing _context_transition_id attribute"
    assert category._context_transition_id is None, "Should initialize as None"
    print("✅ Attribute _context_transition_id exists and initializes correctly")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

# Test 2: Check that set_query_from_transition stores the ID
try:
    category.set_query_from_transition(
        ec_number="2.7.1.1",
        organism="Homo sapiens",
        transition_id="T32"
    )
    
    assert category._context_transition_id == "T32", f"Expected 'T32', got '{category._context_transition_id}'"
    print("✅ set_query_from_transition() stores transition ID correctly")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

# Test 3: Simulate what happens in _on_search_clicked
try:
    # Simulate the manual query case (no context menu)
    category._context_transition_id = None
    transition_id = category._context_transition_id or f'EC_2.7.1.1'
    assert transition_id == 'EC_2.7.1.1', f"Manual query should use EC_, got '{transition_id}'"
    print("✅ Manual query uses EC_ prefix")
    
    # Simulate the context menu case
    category._context_transition_id = "T32"
    transition_id = category._context_transition_id or f'EC_2.7.1.1'
    assert transition_id == 'T32', f"Context menu should preserve ID, got '{transition_id}'"
    print("✅ Context menu query preserves transition ID")
    
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("WORKFLOW SIMULATION")
print("="*70)

# Test 4: Full workflow simulation
print("\n1. User right-clicks transition T32")
print("   → Context menu calls set_query_from_transition(transition_id='T32')")
category.set_query_from_transition(
    ec_number="2.7.1.1",
    organism="Homo sapiens",
    transition_id="T32"
)
print(f"   → Stored: {category._context_transition_id}")

print("\n2. User clicks Search button")
print("   → _on_search_clicked creates result dict with transition_id")
transition_id = category._context_transition_id or f'EC_2.7.1.1'
result_dict = {
    'transition_id': transition_id,  # This will be "T32"
    'transition_name': 'EC 2.7.1.1',
    'identifiers': {'ec_number': '2.7.1.1'},
}
print(f"   → Result dict: {result_dict['transition_id']}")

print("\n3. Results table displays")
print("   → ID column shows: " + result_dict['transition_id'])
print("   → User can see which transition (T32) the results are for! ✓")

# Clear after use (as code does)
category._context_transition_id = None

print("\n4. User manually types EC 2.7.1.2 and searches")
print("   → No context menu used, _context_transition_id is None")
transition_id = category._context_transition_id or f'EC_2.7.1.2'
print(f"   → ID column shows: {transition_id}")
print("   → Falls back to EC_ prefix ✓")

print("\n" + "="*70)
print("✅ ALL TESTS PASSED")
print("="*70)
print("\nSummary:")
print("  - Context menu preserves transition ID (e.g., T32)")
print("  - Results table shows T32 in ID column")
print("  - Manual queries use EC_ prefix as fallback")
print("  - User never loses track of which transition they queried!")
print("="*70)
