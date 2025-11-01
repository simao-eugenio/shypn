#!/usr/bin/env python3
"""Test that load_objects() resets tokens to initial_marking.

This test verifies that the load_objects() method (used by KEGG import, File Open, etc.)
correctly resets place tokens to their initial_marking value, which is CRITICAL for
test arcs (catalysts) to function correctly.

Test Case:
1. Create a place with initial_marking=1 but tokens=0 (simulates loaded state)
2. Load it via load_objects()
3. Verify tokens was reset to 1 (not left at 0)
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.netobjs.place import Place
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.core.controllers.document_controller import DocumentController


def test_load_objects_resets_tokens():
    """Test that load_objects() resets tokens to initial_marking."""
    print("\n" + "="*70)
    print("TEST: load_objects() Token Reset")
    print("="*70)
    
    # Create a manager
    manager = ModelCanvasManager(canvas_width=1000, canvas_height=1000, filename="test")
    
    # Create a place with initial_marking=1 but tokens=0
    # This simulates what happens when loading a saved file where simulation ran
    place = Place(
        x=100, 
        y=100, 
        id="P1",
        name="P1",
        label="Catalyst"
    )
    # Set the initial marking and tokens separately (simulates loaded corrupted state)
    place.initial_marking = 1  # Should have 1 token
    place.tokens = 0            # But currently has 0 (wrong!)
    
    print(f"\n1. Before load_objects():")
    print(f"   Place P1: initial_marking={place.initial_marking}, tokens={place.tokens}")
    print(f"   ❌ Tokens do NOT match initial_marking (simulates loaded corrupted state)")
    
    # Load the place via load_objects() - this should reset tokens
    manager.load_objects(places=[place], transitions=[], arcs=[])
    
    print(f"\n2. After load_objects():")
    print(f"   Place P1: initial_marking={place.initial_marking}, tokens={place.tokens}")
    
    # Verify tokens was reset to initial_marking
    if place.tokens == place.initial_marking:
        print(f"   ✅ SUCCESS: Tokens reset to initial_marking!")
        return True
    else:
        print(f"   ❌ FAILURE: Tokens NOT reset (still {place.tokens}, should be {place.initial_marking})")
        return False


def test_multiple_places():
    """Test with multiple places with different initial markings."""
    print("\n" + "="*70)
    print("TEST: Multiple Places Token Reset")
    print("="*70)
    
    manager = ModelCanvasManager(canvas_width=1000, canvas_height=1000, filename="test")
    
    # Create multiple places with various states
    places = []
    
    p1 = Place(x=100, y=100, id="P1", name="P1", label="Catalyst")
    p1.initial_marking = 1
    p1.tokens = 0
    places.append(p1)
    
    p2 = Place(x=200, y=100, id="P2", name="P2", label="Substrate")
    p2.initial_marking = 5
    p2.tokens = 2
    places.append(p2)
    
    p3 = Place(x=300, y=100, id="P3", name="P3", label="Product")
    p3.initial_marking = 0
    p3.tokens = 3
    places.append(p3)
    
    print(f"\n1. Before load_objects():")
    for p in places:
        match = "✅" if p.tokens == p.initial_marking else "❌"
        print(f"   {p.id}: initial_marking={p.initial_marking}, tokens={p.tokens} {match}")
    
    # Load all places
    manager.load_objects(places=places, transitions=[], arcs=[])
    
    print(f"\n2. After load_objects():")
    all_correct = True
    for p in places:
        match = "✅" if p.tokens == p.initial_marking else "❌"
        print(f"   {p.id}: initial_marking={p.initial_marking}, tokens={p.tokens} {match}")
        if p.tokens != p.initial_marking:
            all_correct = False
    
    if all_correct:
        print(f"\n✅ SUCCESS: All places reset correctly!")
        return True
    else:
        print(f"\n❌ FAILURE: Some places not reset correctly")
        return False


if __name__ == '__main__':
    results = []
    
    try:
        results.append(("Basic Token Reset", test_load_objects_resets_tokens()))
        results.append(("Multiple Places", test_multiple_places()))
        
        print("\n" + "="*70)
        print("FINAL RESULTS")
        print("="*70)
        
        all_passed = True
        for test_name, passed in results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{status}: {test_name}")
            if not passed:
                all_passed = False
        
        print("="*70)
        
        if all_passed:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ load_objects() correctly resets tokens to initial_marking")
            print("✅ This ensures catalysts work correctly in all loading paths:")
            print("   - File → Open")
            print("   - KEGG Import")
            print("   - SBML Import (when file is later opened)")
            sys.exit(0)
        else:
            print("\n❌ SOME TESTS FAILED")
            print("The load_objects() fix needs adjustment")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
