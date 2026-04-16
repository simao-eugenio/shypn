#!/usr/bin/env python3
"""Test that TestArc instances are properly reconstructed from saved files.

This tests the fix for the bug where test arcs were being loaded as regular Arc
instances instead of TestArc instances, causing the simulation engine to not
recognize them as non-consuming arcs.
"""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.test_arc import TestArc
from shypn.netobjs.arc import Arc

def test_test_arc_serialization():
    """Test that TestArc can be saved and loaded correctly."""
    
    print("="*70)
    print("TEST: TestArc Serialization/Deserialization")
    print("="*70)
    
    # Create test objects
    p1 = Place(id="P1", name="Enzyme", x=0, y=0)
    p1.tokens = 1
    t1 = Transition(id="T1", name="Reaction", x=100, y=0)
    
    # Create test arc
    test_arc = TestArc(source=p1, target=t1, id="TA1", name="TestArc1")
    
    print(f"\n1. Created TestArc:")
    print(f"   Type: {type(test_arc).__name__}")
    print(f"   Has consumes_tokens(): {hasattr(test_arc, 'consumes_tokens')}")
    print(f"   consumes_tokens() returns: {test_arc.consumes_tokens()}")
    
    # Serialize
    data = test_arc.to_dict()
    print(f"\n2. Serialized to dict:")
    print(f"   arc_type: {data.get('arc_type', 'MISSING')}")
    print(f"   consumes: {data.get('consumes', 'MISSING')}")
    
    # Deserialize
    places = {p1.id: p1}
    transitions = {t1.id: t1}
    
    loaded_arc = Arc.from_dict(data, places, transitions)
    
    print(f"\n3. Deserialized from dict:")
    print(f"   Type: {type(loaded_arc).__name__}")
    print(f"   Has consumes_tokens(): {hasattr(loaded_arc, 'consumes_tokens')}")
    
    if hasattr(loaded_arc, 'consumes_tokens'):
        print(f"   consumes_tokens() returns: {loaded_arc.consumes_tokens()}")
        
        if type(loaded_arc).__name__ == 'TestArc' and not loaded_arc.consumes_tokens():
            print(f"\n✅ TEST PASSED: TestArc correctly reconstructed!")
            return True
        else:
            print(f"\n❌ TEST FAILED: TestArc reconstructed but wrong behavior")
            return False
    else:
        print(f"\n❌ TEST FAILED: Loaded as {type(loaded_arc).__name__}, not TestArc!")
        print(f"   This means test arcs won't work in simulation!")
        return False


if __name__ == '__main__':
    success = test_test_arc_serialization()
    sys.exit(0 if success else 1)
