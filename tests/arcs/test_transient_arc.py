#!/usr/bin/env python3
"""Test script for TransientArc visual feedback system."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.api import Place, Transition
from shypn.edit import TransientArc
from shypn.edit.transient_arc import TransientArcManager


def test_transient_arc_creation():
    """Test creating a TransientArc (not added to model)."""
    place = Place(x=100, y=100, id=1, name="P1")
    
    # Create transient arc (temporary, for visual feedback only)
    transient = TransientArc(source=place, target_x=200, target_y=200)
    
    assert transient.source == place
    assert transient.target_x == 200
    assert transient.target_y == 200
    
    print("✓ TransientArc created successfully")
    print(f"  Source: {place.name} at ({place.x}, {place.y})")
    print(f"  Target cursor: ({transient.target_x}, {transient.target_y})")
    return True


def test_transient_arc_update():
    """Test updating transient arc target (follows cursor)."""
    place = Place(x=100, y=100, id=1, name="P1")
    transient = TransientArc(source=place, target_x=200, target_y=200)
    
    # Simulate cursor movement
    transient.update_target(250, 300)
    assert transient.target_x == 250
    assert transient.target_y == 300
    
    transient.update_target(180, 150)
    assert transient.target_x == 180
    assert transient.target_y == 150
    
    print("✓ TransientArc follows cursor updates")
    print(f"  Position updated: (200,200) → (250,300) → (180,150)")
    return True


def test_not_a_petri_net_object():
    """Verify TransientArc is NOT a PetriNetObject."""
    from shypn.api.petri_net_object import PetriNetObject
    
    place = Place(x=100, y=100, id=1, name="P1")
    transient = TransientArc(source=place, target_x=200, target_y=200)
    
    # TransientArc should NOT be a PetriNetObject
    assert not isinstance(transient, PetriNetObject)
    
    # It should not have id/name properties
    assert not hasattr(transient, 'id')
    assert not hasattr(transient, 'name')
    
    print("✓ TransientArc is NOT a PetriNetObject")
    print("  (Correct - it's only for visual feedback, not part of the model)")
    return True


def test_transient_arc_manager():
    """Test TransientArcManager helper class."""
    manager = TransientArcManager()
    
    # Initially no active arc
    assert not manager.has_active_arc()
    assert manager.get_active_arc() is None
    
    # Start arc creation
    place = Place(x=100, y=100, id=1, name="P1")
    manager.start_arc(place, cursor_x=100, cursor_y=100)
    
    assert manager.has_active_arc()
    assert manager.get_active_arc() is not None
    assert manager.get_source() == place
    
    # Update cursor
    manager.update_cursor(200, 200)
    arc = manager.get_active_arc()
    assert arc.target_x == 200
    assert arc.target_y == 200
    
    # Finish arc
    manager.finish_arc()
    assert not manager.has_active_arc()
    
    print("✓ TransientArcManager state management works")
    print("  Start → Update → Finish sequence successful")
    return True


def test_transient_arc_cancel():
    """Test canceling arc creation."""
    manager = TransientArcManager()
    place = Place(x=100, y=100, id=1, name="P1")
    
    # Start arc
    manager.start_arc(place)
    assert manager.has_active_arc()
    
    # Cancel instead of finish
    manager.cancel_arc()
    assert not manager.has_active_arc()
    assert manager.get_source() is None
    
    print("✓ TransientArc can be canceled")
    print("  (e.g., user presses ESC or right-clicks)")
    return True


def test_different_source_types():
    """Test TransientArc works with both Place and Transition sources."""
    # From Place
    place = Place(x=100, y=100, id=1, name="P1")
    trans_from_place = TransientArc(source=place, target_x=200, target_y=200)
    assert trans_from_place.source == place
    
    # From Transition
    trans = Transition(x=200, y=200, id=1, name="T1")
    trans_from_trans = TransientArc(source=trans, target_x=300, target_y=300)
    assert trans_from_trans.source == trans
    
    print("✓ TransientArc works with both Place and Transition sources")
    return True


def test_visual_styling():
    """Verify TransientArc has distinct visual styling."""
    place = Place(x=100, y=100, id=1, name="P1")
    transient = TransientArc(source=place, target_x=200, target_y=200)
    
    # Check preview color (orange, not black like real arcs)
    assert transient.PREVIEW_COLOR == (0.95, 0.5, 0.1)
    assert transient.PREVIEW_ALPHA == 0.85
    assert transient.PREVIEW_WIDTH == 2.0
    
    # Different from real Arc styling
    from shypn.api import Arc
    assert transient.PREVIEW_COLOR != Arc.DEFAULT_COLOR
    
    print("✓ TransientArc has distinct visual styling")
    print(f"  Color: Orange {transient.PREVIEW_COLOR} (vs black for real arcs)")
    print(f"  Alpha: {transient.PREVIEW_ALPHA} (semi-transparent)")
    print(f"  Width: {transient.PREVIEW_WIDTH}px")
    return True


def test_no_bipartite_validation():
    """Verify TransientArc does NOT validate bipartite connections."""
    # This is correct - validation happens when creating the real Arc
    
    place1 = Place(x=100, y=100, id=1, name="P1")
    place2 = Place(x=200, y=200, id=2, name="P2")
    
    # TransientArc allows invalid connections (it's just visual feedback)
    try:
        transient = TransientArc(source=place1, target_x=place2.x, target_y=place2.y)
        # Should succeed - no validation yet
        print("✓ TransientArc does NOT validate connections")
        print("  (Correct - validation happens when creating real Arc)")
        return True
    except ValueError:
        print("✗ FAILED: TransientArc should not validate connections")
        return False


def main():
    """Run all transient arc tests."""
    print("\n=== Testing TransientArc System ===\n")
    
    tests = [
        ("TransientArc Creation", test_transient_arc_creation),
        ("Cursor Updates", test_transient_arc_update),
        ("Not a PetriNetObject", test_not_a_petri_net_object),
        ("TransientArcManager", test_transient_arc_manager),
        ("Arc Cancellation", test_transient_arc_cancel),
        ("Different Source Types", test_different_source_types),
        ("Visual Styling", test_visual_styling),
        ("No Validation", test_no_bipartite_validation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
            print()
        except Exception as e:
            print(f"✗ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
            print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n✓ All TransientArc tests passed!\n")
        print("Summary:")
        print("  ✓ TransientArc created for visual feedback")
        print("  ✓ Updates with cursor movement")
        print("  ✓ NOT a PetriNetObject (correct)")
        print("  ✓ TransientArcManager simplifies state management")
        print("  ✓ Can be canceled (ESC, right-click)")
        print("  ✓ Works with Place and Transition sources")
        print("  ✓ Distinct orange styling (vs black for real arcs)")
        print("  ✓ No connection validation (happens when creating real Arc)")
        print("\nLesson from legacy:")
        print("  • arc_preview.py: Orange preview line with arrowhead")
        print("  • interactions.py: Store source, update on motion")
        print("  • validate_ui.py: Render preview, discard on cancel")
        print("\nUsage pattern:")
        print("  1. User clicks source → create TransientArc")
        print("  2. Mouse moves → update TransientArc target")
        print("  3. User clicks target → create real Arc, discard TransientArc")
        print("  4. User cancels → discard TransientArc\n")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
