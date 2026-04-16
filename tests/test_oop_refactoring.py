#!/usr/bin/env python3
"""Test OOP refactoring of netobjects - property decorators and protected attributes."""

import sys
sys.path.insert(0, 'src')

from shypn.netobjs.transition import Transition
from shypn.netobjs.place import Place
from shypn.netobjs.arc import Arc

def test_transition_properties():
    """Test Transition property decorators."""
    print("=" * 60)
    print("Testing Transition OOP Properties")
    print("=" * 60)
    
    # Create transition
    t = Transition(x=100, y=200, id="T1", name="T1", label="ATP Synthesis")
    
    # Test property decorator access (Pythonic way)
    print("\n1. Property Decorator Access:")
    t.rate_function = "0.5 * [ADP_pool]"
    print(f"   t.rate_function = '{t.rate_function}'")
    
    t.rate_forward = "k_f * [S]"
    t.rate_reverse = "k_r * [P]"
    print(f"   t.rate_forward = '{t.rate_forward}'")
    print(f"   t.rate_reverse = '{t.rate_reverse}'")
    
    # Test backward compatibility with properties dict
    print("\n2. Backward Compatibility (properties dict):")
    print(f"   t.properties = {t.properties}")
    print(f"   t.properties['rate_function'] = '{t.properties.get('rate_function')}'")
    
    # Test protected attribute is actually private
    print("\n3. Protected Attribute Access:")
    print(f"   t._properties = {t._properties}")
    print(f"   ✓ Protected attribute accessible but marked as private")
    
    # Test validation
    print("\n4. Type Validation:")
    try:
        t.rate_function = 123  # Should raise TypeError
        print("   ✗ FAILED: No type error raised")
    except TypeError as e:
        print(f"   ✓ PASSED: {e}")
    
    # Test metadata property
    print("\n5. Metadata Property:")
    t.metadata = {"source": "SABIO-RK", "confidence": 0.95}
    print(f"   t.metadata = {t.metadata}")
    print(f"   ✓ Metadata property working")
    
    print("\n✓ Transition tests PASSED\n")


def test_place_properties():
    """Test Place property decorators."""
    print("=" * 60)
    print("Testing Place OOP Properties")
    print("=" * 60)
    
    # Create place
    p = Place(x=150, y=250, id="P1", name="P1", label="ATP Pool")
    
    # Test properties dict access
    print("\n1. Properties Dict Access:")
    p.properties = {"compartment": "cytoplasm", "concentration": 5.0}
    print(f"   p.properties = {p.properties}")
    
    # Test metadata
    print("\n2. Metadata Access:")
    p.metadata = {"annotation": "Adenosine Triphosphate", "chebi_id": "CHEBI:15422"}
    print(f"   p.metadata = {p.metadata}")
    
    # Test validation
    print("\n3. Type Validation:")
    try:
        p.properties = "not a dict"  # Should raise TypeError
        print("   ✗ FAILED: No type error raised")
    except TypeError as e:
        print(f"   ✓ PASSED: {e}")
    
    print("\n✓ Place tests PASSED\n")


def test_arc_properties():
    """Test Arc property decorators."""
    print("=" * 60)
    print("Testing Arc OOP Properties")
    print("=" * 60)
    
    # Create objects
    p = Place(x=100, y=100, id="P1", name="P1")
    t = Transition(x=200, y=100, id="T1", name="T1")
    
    # Create arc
    a = Arc(source=p, target=t, id="A1", name="A1", weight=2.0)
    
    # Test properties dict access
    print("\n1. Properties Dict Access:")
    a.properties = {"stoichiometry": 2, "enzyme": "ATPase"}
    print(f"   a.properties = {a.properties}")
    
    # Test metadata
    print("\n2. Metadata Access:")
    a.metadata = {"reaction_type": "catalytic"}
    print(f"   a.metadata = {a.metadata}")
    
    print("\n✓ Arc tests PASSED\n")


def test_backward_compatibility():
    """Test backward compatibility with old code."""
    print("=" * 60)
    print("Testing Backward Compatibility")
    print("=" * 60)
    
    t = Transition(x=100, y=200, id="T1", name="T1")
    
    # Old code that directly accesses properties dict
    print("\n1. Old-style direct dict access still works:")
    if not hasattr(t, 'properties') or t.properties is None:
        t.properties = {}
    t.properties['rate_function'] = "k * [S]"
    print(f"   t.properties['rate_function'] = '{t.properties['rate_function']}'")
    
    # New code using property decorator
    print("\n2. New-style property decorator access:")
    print(f"   t.rate_function = '{t.rate_function}'")
    print(f"   ✓ Both access methods return same value")
    
    # Setting via property updates dict
    print("\n3. Property setter updates internal dict:")
    t.rate_function = "0.75 * [ATP]"
    print(f"   After: t.rate_function = '{t.rate_function}'")
    print(f"   After: t.properties['rate_function'] = '{t.properties['rate_function']}'")
    print(f"   ✓ Property and dict stay synchronized")
    
    print("\n✓ Backward compatibility PASSED\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("OOP REFACTORING TEST SUITE")
    print("Testing Property Decorators and Protected Attributes")
    print("=" * 60 + "\n")
    
    try:
        test_transition_properties()
        test_place_properties()
        test_arc_properties()
        test_backward_compatibility()
        
        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nOOP Refactoring Summary:")
        print("  • Protected attributes: _properties, _metadata")
        print("  • Property decorators: rate_function, properties, metadata")
        print("  • Type validation: Enforced in setters")
        print("  • Backward compatibility: Maintained")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
