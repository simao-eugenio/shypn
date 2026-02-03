#!/usr/bin/env python3
"""Test signal place to arc conversion behavior.

Verifies that when a place is converted to a signal place:
1. The place properties are updated (is_signal_place=True, shape=hexagon)
2. Connected normal Arcs are converted to SignalFlowArcs
3. Arc type property is correctly set to 'signal_flow'
4. When signal designation is removed, SignalFlowArcs convert back to normal Arcs
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_signal_place_conversion():
    """Test converting place to signal place updates connected arcs."""
    from shypn.netobjs.place import Place
    from shypn.netobjs.transition import Transition
    from shypn.netobjs.arc import Arc
    from shypn.netobjs.signal_flow_arc import SignalFlowArc
    from shypn.data.canvas.document_model import DocumentModel
    
    print("Testing signal place conversion with arc transformation...")
    
    # Create simple P-T-P model
    doc = DocumentModel()
    
    p1 = doc.create_place(x=100, y=100, label="P1")
    t1 = doc.create_transition(x=200, y=100, label="T1")
    p2 = doc.create_place(x=300, y=100, label="P2")
    
    # Create arcs (should be normal Arcs initially)
    arc1 = doc.create_arc(p1, t1)
    arc2 = doc.create_arc(t1, p2)
    
    print(f"  Initial setup:")
    print(f"    P1 -> T1 -> P2")
    print(f"    Arc1 type: {type(arc1).__name__}, arc_type='{arc1.arc_type}'")
    print(f"    Arc2 type: {type(arc2).__name__}, arc_type='{arc2.arc_type}'")
    print(f"    P1 is_signal_place: {getattr(p1, 'is_signal_place', False)}")
    
    # Verify initial state
    assert isinstance(arc1, Arc) and not isinstance(arc1, SignalFlowArc), "Arc1 should be normal Arc"
    assert isinstance(arc2, Arc) and not isinstance(arc2, SignalFlowArc), "Arc2 should be normal Arc"
    assert arc1.arc_type == 'normal', "Arc1 should have arc_type='normal'"
    assert arc2.arc_type == 'normal', "Arc2 should have arc_type='normal'"
    
    # Convert P1 to signal place (simulating the menu action)
    p1.is_signal_place = True
    p1.signal_type = 'regulatory'
    p1.shape = 'hexagon'
    
    print(f"\n  After marking P1 as signal place:")
    print(f"    P1 is_signal_place: {p1.is_signal_place}")
    print(f"    P1 signal_type: {p1.signal_type}")
    print(f"    P1 shape: {p1.shape}")
    
    # Now simulate arc conversion (what should happen in _on_convert_to_signal)
    from shypn.utils.arc_transform import convert_to_signal_flow
    
    arcs_to_replace = []
    for arc in doc.arcs[:]:
        if arc.source == p1 or arc.target == p1:
            if isinstance(arc, Arc) and arc.__class__ == Arc:
                try:
                    new_arc = convert_to_signal_flow(arc)
                    arcs_to_replace.append((arc, new_arc))
                except ValueError as e:
                    print(f"    Error converting arc: {e}")
    
    # Replace arcs
    for old_arc, new_arc in arcs_to_replace:
        idx = doc.arcs.index(old_arc)
        doc.arcs[idx] = new_arc
        # Update references
        if old_arc == arc1:
            arc1 = new_arc
    
    print(f"\n  After arc conversion:")
    print(f"    Arc1 type: {type(arc1).__name__}, arc_type='{arc1.arc_type}'")
    print(f"    Arc2 type: {type(arc2).__name__}, arc_type='{arc2.arc_type}'")
    print(f"    Arc1 connects to signal place: {arc1._is_signal_arc()}")
    
    # Verify conversion
    assert isinstance(arc1, SignalFlowArc), "Arc1 should be converted to SignalFlowArc"
    assert arc1.arc_type == 'signal_flow', "Arc1 should have arc_type='signal_flow'"
    assert isinstance(arc2, Arc) and not isinstance(arc2, SignalFlowArc), "Arc2 should remain normal Arc"
    assert arc2.arc_type == 'normal', "Arc2 should remain arc_type='normal'"
    
    print(f"\n  ✅ Signal place conversion successful!")
    print(f"     - P1 is now a signal place")
    print(f"     - Connected arc (P1→T1) is now SignalFlowArc")
    print(f"     - Non-connected arc (T1→P2) remains normal Arc")
    
    return True

def test_remove_signal_designation():
    """Test removing signal designation converts SignalFlowArcs back to normal."""
    from shypn.netobjs.place import Place
    from shypn.netobjs.transition import Transition
    from shypn.netobjs.signal_flow_arc import SignalFlowArc
    from shypn.netobjs.arc import Arc
    from shypn.data.canvas.document_model import DocumentModel
    from shypn.utils.arc_transform import convert_to_signal_flow, convert_to_normal
    
    print("\nTesting signal designation removal...")
    
    # Create model with signal place
    doc = DocumentModel()
    
    p1 = doc.create_place(x=100, y=100, label="P1")
    p1.is_signal_place = True
    p1.signal_type = 'regulatory'
    
    t1 = doc.create_transition(x=200, y=100, label="T1")
    
    # Create arc and convert to SignalFlowArc
    arc1_normal = doc.create_arc(p1, t1)
    arc1 = convert_to_signal_flow(arc1_normal)
    doc.arcs[doc.arcs.index(arc1_normal)] = arc1
    
    print(f"  Initial state:")
    print(f"    P1 is_signal_place: {p1.is_signal_place}")
    print(f"    Arc1 type: {type(arc1).__name__}, arc_type='{arc1.arc_type}'")
    
    assert isinstance(arc1, SignalFlowArc), "Arc1 should be SignalFlowArc"
    
    # Remove signal designation
    p1.is_signal_place = False
    p1.signal_type = None
    
    # Convert arc back to normal
    if isinstance(arc1, SignalFlowArc):
        source_is_signal = getattr(arc1.source, 'is_signal_place', False)
        target_is_signal = getattr(arc1.target, 'is_signal_place', False)
        
        if not (source_is_signal or target_is_signal):
            arc1 = convert_to_normal(arc1)
            doc.arcs[0] = arc1
    
    print(f"\n  After removing signal designation:")
    print(f"    P1 is_signal_place: {p1.is_signal_place}")
    print(f"    Arc1 type: {type(arc1).__name__}, arc_type='{arc1.arc_type}'")
    
    assert isinstance(arc1, Arc) and not isinstance(arc1, SignalFlowArc), "Arc1 should be normal Arc"
    assert arc1.arc_type == 'normal', "Arc1 should have arc_type='normal'"
    
    print(f"\n  ✅ Signal designation removal successful!")
    print(f"     - P1 is no longer a signal place")
    print(f"     - SignalFlowArc converted back to normal Arc")
    
    return True

def test_arc_property_consistency():
    """Test that arc_type property is consistent with arc class."""
    from shypn.netobjs.signal_flow_arc import SignalFlowArc
    from shypn.netobjs.arc import Arc
    from shypn.netobjs.place import Place
    from shypn.netobjs.transition import Transition
    
    print("\nTesting arc_type property consistency...")
    
    # Create objects
    p1 = Place(x=100, y=100, id="P1", name="P1")
    p1.is_signal_place = True
    
    t1 = Transition(x=200, y=100, id="T1", name="T1")
    
    # Create SignalFlowArc
    signal_arc = SignalFlowArc(p1, t1, "A1", "A1", weight=1.0)
    
    # Create normal Arc
    p2 = Place(x=300, y=100, id="P2", name="P2")
    normal_arc = Arc(t1, p2, "A2", "A2", weight=1.0)
    
    print(f"  SignalFlowArc:")
    print(f"    Class: {type(signal_arc).__name__}")
    print(f"    arc_type property: '{signal_arc.arc_type}'")
    print(f"    Expected: 'signal_flow'")
    
    print(f"\n  Normal Arc:")
    print(f"    Class: {type(normal_arc).__name__}")
    print(f"    arc_type property: '{normal_arc.arc_type}'")
    print(f"    Expected: 'normal'")
    
    assert signal_arc.arc_type == 'signal_flow', "SignalFlowArc should have arc_type='signal_flow'"
    assert normal_arc.arc_type == 'normal', "Normal Arc should have arc_type='normal'"
    
    print(f"\n  ✅ Arc type properties are consistent!")
    
    return True

def main():
    """Run all tests."""
    print("=" * 70)
    print("🔍 TESTING SIGNAL PLACE TO ARC CONVERSION")
    print("=" * 70)
    print()
    
    tests = [
        ("Signal Place Conversion", test_signal_place_conversion),
        ("Remove Signal Designation", test_remove_signal_designation),
        ("Arc Property Consistency", test_arc_property_consistency),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ {test_name}: FAILED - {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n🎯 Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 SUCCESS! Signal place to arc conversion works correctly!")
        return 0
    else:
        print("\n⚠️  WARNING: Some tests failed.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
