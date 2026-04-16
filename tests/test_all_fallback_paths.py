#!/usr/bin/env python3
"""
Test ALL fallback paths for test arc behavior

This test uses behaviors directly like test_gui_conversion.py.
""" 

import sys
sys.path.insert(0, 'src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition, Arc
from shypn.netobjs.test_arc import TestArc
from shypn.engine.immediate_behavior import ImmediateBehavior
 
def test_immediate_with_test_arc():
    """Test immediate transitions don't consume test arc tokens"""
    print("=" * 70)
    print("TEST 1: Immediate Transition + Test Arc")
    print("=" * 70)
    
    document = DocumentModel()
    
    p1 = Place(id='P1', name='P1', x=100, y=100)
    p1.tokens = 25
    p2 = Place(id='P2', name='P2', x=300, y=100)
    p2.tokens = 0
    t = Transition(id='T1', name='T1', x=200, y=100)
    t.transition_type = 'immediate'
    
    arc_in = TestArc(source=p1, target=t, id='A1', name='A1', weight=1)
    arc_out = Arc(source=t, target=p2, id='A2', name='A2', weight=1)
    
    document.places = [p1, p2]
    document.transitions = [t]
    document.arcs = [arc_in, arc_out]
    
    behavior = ImmediateBehavior(t, document)
    input_arcs = behavior.get_input_arcs()
    output_arcs = behavior.get_output_arcs()
    
    print(f"  Before: P1={p1.tokens}, P2={p2.tokens}")
    print(f"  Arc type: {type(arc_in).__name__}, arc_type={arc_in.arc_type}")
    print(f"  Consumes tokens: {arc_in.consumes_tokens()}")
    
    # Fire transition
    success, result = behavior.fire(input_arcs, output_arcs)
    
    print(f"  After:  P1={p1.tokens}, P2={p2.tokens}")
    print(f"  Fire success: {success}")
    
    if p1.tokens == 25:
        print("✅ PASS: P1 unchanged (test arc didn't consume)")
    else:
        print(f"❌ FAIL: P1 consumed! 25 → {p1.tokens}")
        return False
        
    if p2.tokens == 1:
        print("✅ PASS: P2 gained 1 token")
    else:
        print(f"❌ FAIL: P2 incorrect! Expected 1, got {p2.tokens}")
        return False
    
    return True


def test_multiple_firings():
    """Test multiple firings don't consume test arc tokens"""
    print("=" * 70)
    print("TEST 2: Multiple Firings + Test Arc")
    print("=" * 70)
    
    document = DocumentModel()
    
    p1 = Place(id='P1', name='P1', x=100, y=100)
    p1.tokens = 5  # Limited catalyst
    p2 = Place(id='P2', name='P2', x=300, y=100)
    p2.tokens = 0
    t = Transition(id='T1', name='T1', x=200, y=100)
    t.transition_type = 'immediate'
    
    arc_in = TestArc(source=p1, target=t, id='A1', name='A1', weight=1)
    arc_out = Arc(source=t, target=p2, id='A2', name='A2', weight=1)
    
    document.places = [p1, p2]
    document.transitions = [t]
    document.arcs = [arc_in, arc_out]
    
    behavior = ImmediateBehavior(t, document)
    input_arcs = behavior.get_input_arcs()
    output_arcs = behavior.get_output_arcs()
    
    print(f"  Initial: P1={p1.tokens}, P2={p2.tokens}")
    
    # Fire 10 times
    for i in range(10):
        success, result = behavior.fire(input_arcs, output_arcs)
        print(f"  Step {i+1}: P1={p1.tokens}, P2={p2.tokens}")
    
    if p1.tokens == 5:
        print("✅ PASS: P1 unchanged after 10 firings")
    else:
        print(f"❌ FAIL: P1 consumed! 5 → {p1.tokens}")
        return False
        
    if p2.tokens == 10:
        print("✅ PASS: P2 has 10 tokens")
    else:
        print(f"❌ FAIL: P2 incorrect! Expected 10, got {p2.tokens}")
        return False
    
    return True


def main():
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "TEST ALL FALLBACK PATHS" + " " * 30 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    tests = [
        ("Immediate + Test Arc", test_immediate_with_test_arc),
        ("Multiple Firings + Test Arc", test_multiple_firings),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"❌ {name} raised exception: {e}")
            import traceback
            traceback.print_exc()
        print()
    
    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed > 0:
        print("\n❌ SOME TESTS FAILED - Test arcs still consuming tokens!")
        sys.exit(1)
    else:
        print("\n✅ ALL TESTS PASSED - Test arcs working correctly!")
        sys.exit(0)


if __name__ == '__main__':
    main()
