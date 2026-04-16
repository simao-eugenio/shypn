#!/usr/bin/env python3
"""Debug arc_type property for different arc types."""

import sys
sys.path.insert(0, 'src')

from shypn.netobjs import Place, Transition, Arc
from shypn.netobjs.test_arc import TestArc
from shypn.netobjs.inhibitor_arc import InhibitorArc

# Create test objects
p1 = Place(id='P1', name='P1', x=100, y=100)
p2 = Place(id='P2', name='P2', x=300, y=100)
t = Transition(id='T1', name='T1', x=200, y=100)

# Create different arc types
normal_arc = Arc(source=p1, target=t, id='A_normal', name='A_normal', weight=1)
test_arc = TestArc(source=p1, target=t, id='A_test', name='A_test', weight=1)
inhibitor_arc = InhibitorArc(source=p1, target=t, id='A_inhibitor', name='A_inhibitor', weight=1)

print("=" * 70)
print("Testing arc_type property for different arc types")
print("=" * 70)

for arc_name, arc in [('Normal Arc', normal_arc), ('Test Arc', test_arc), ('Inhibitor Arc', inhibitor_arc)]:
    print(f"\n{arc_name}:")
    print(f"  type(arc).__name__ = {type(arc).__name__}")
    print(f"  hasattr(arc, 'arc_type') = {hasattr(arc, 'arc_type')}")
    print(f"  arc.arc_type = {arc.arc_type}")
    print(f"  getattr(arc, 'arc_type', 'normal') = {getattr(arc, 'arc_type', 'normal')}")
    print(f"  hasattr(arc, 'kind') = {hasattr(arc, 'kind')}")
    print(f"  getattr(arc, 'kind', 'NOTFOUND') = {getattr(arc, 'kind', 'NOTFOUND')}")
    print(f"  hasattr(arc, 'properties') = {hasattr(arc, 'properties')}")
    print(f"  arc.properties = {arc.properties}")
    print(f"  properties.get('kind', 'normal') = {arc.properties.get('kind', 'normal')}")
    
    # Test the defensive pattern
    kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
    arc_type = getattr(arc, 'arc_type', 'normal')
    should_skip = kind != 'normal' or arc_type in ('inhibitor', 'test')
    print(f"  Defensive pattern result:")
    print(f"    kind = {kind}")
    print(f"    arc_type = {arc_type}")
    print(f"    should_skip_consumption = {should_skip}")

print("\n" + "=" * 70)
print("Summary:")
print("=" * 70)
print("Normal Arc should_skip: False (consumes)")
print("Test Arc should_skip: True (doesn't consume)")
print("Inhibitor Arc should_skip: True (doesn't consume via defensive check)")
