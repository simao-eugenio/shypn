#!/usr/bin/env python3
"""
Test that duplicate ID bug is fixed after loading SBML models.

This verifies that:
1. Loading a file with places 1-12 sets counter to 13
2. Creating new places after loading gets unique IDs (13, 14, 15...)
3. No duplicate IDs exist in the model
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.data.canvas.document_model import DocumentModel

def test_duplicate_id_fix():
    """Test that ID counters are properly updated after loading a file."""
    
    # Load a .shy file to test (using Hynne model as example)
    model_path = "models/Hynne2001_Glycolysis.shy"
    
    print(f"Loading {model_path}...")
    doc = DocumentModel.load_from_file(model_path)
    
    # Check what we loaded
    place_ids = sorted([int(p.id) for p in doc.places])
    transition_ids = sorted([int(t.id) for t in doc.transitions])
    
    print(f"✓ Loaded {len(doc.places)} places with IDs: {place_ids}")
    print(f"✓ Loaded {len(doc.transitions)} transitions with IDs: {transition_ids}")
    
    # Check ID counters are set correctly
    expected_next_place = max(place_ids) + 1 if place_ids else 1
    expected_next_transition = max(transition_ids) + 1 if transition_ids else 1
    
    print(f"\nID Counter Status:")
    print(f"  _next_place_id: {doc._next_place_id} (expected: {expected_next_place})")
    print(f"  _next_transition_id: {doc._next_transition_id} (expected: {expected_next_transition})")
    
    assert doc._next_place_id == expected_next_place, \
        f"Place counter should be {expected_next_place}, got {doc._next_place_id}"
    assert doc._next_transition_id == expected_next_transition, \
        f"Transition counter should be {expected_next_transition}, got {doc._next_transition_id}"
    
    print("✓ ID counters correctly initialized!")
    
    # Create new objects and verify they get unique IDs
    print("\nCreating new objects...")
    new_place1 = doc.create_place(100, 100)
    new_place2 = doc.create_place(200, 100)
    new_transition1 = doc.create_transition(150, 200)
    
    print(f"  New place 1: ID={new_place1.id} (expected: {expected_next_place})")
    print(f"  New place 2: ID={new_place2.id} (expected: {expected_next_place + 1})")
    print(f"  New transition 1: ID={new_transition1.id} (expected: {expected_next_transition})")
    
    assert int(new_place1.id) == expected_next_place, \
        f"New place should have ID {expected_next_place}, got {new_place1.id}"
    assert int(new_place2.id) == expected_next_place + 1, \
        f"New place should have ID {expected_next_place + 1}, got {new_place2.id}"
    assert int(new_transition1.id) == expected_next_transition, \
        f"New transition should have ID {expected_next_transition}, got {new_transition1.id}"
    
    print("✓ New objects have unique IDs!")
    
    # Verify no duplicates exist
    all_place_ids = [p.id for p in doc.places]
    all_transition_ids = [t.id for t in doc.transitions]
    
    assert len(all_place_ids) == len(set(all_place_ids)), \
        f"Duplicate place IDs found: {[id for id in all_place_ids if all_place_ids.count(id) > 1]}"
    assert len(all_transition_ids) == len(set(all_transition_ids)), \
        f"Duplicate transition IDs found: {[id for id in all_transition_ids if all_transition_ids.count(id) > 1]}"
    
    print("✓ No duplicate IDs in the model!")
    
    print("\n" + "="*50)
    print("SUCCESS: Duplicate ID bug is FIXED!")
    print("="*50)

if __name__ == "__main__":
    test_duplicate_id_fix()
