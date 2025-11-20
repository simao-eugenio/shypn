#!/usr/bin/env python3
"""
Test case: Normal arc + Inhibitor arc from same place

Model: P2 → T1 → P1 (normal flow)
       P2 ⊸ T1 (inhibitor, threshold=2)

Initial state: P1=0, P2=3
Expected: T1 disabled (P2=3 ≥ 2 threshold)
"""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.engine.continuous_behavior import ContinuousBehavior

# Create model
doc = DocumentModel()

# Places
p1 = Place(x=100, y=200, id="P1", name="P1", label="P1")
p1.tokens = 0.0
p1.initial_marking = 0.0

p2 = Place(x=300, y=200, id="P2", name="P2", label="P2")
p2.tokens = 3.0
p2.initial_marking = 3.0

doc.add_place(p1)
doc.add_place(p2)

# Transition
t1 = Transition(x=200, y=200, id="T1", name="T1", label="T1")
t1.transition_type = "continuous"
t1.rate = "1.0"  # Constant rate
doc.add_transition(t1)

# Arc 1: P2 → T1 (normal, consumes from P2)
arc1 = Arc(source=p2, target=t1, id="A1", name="A1", weight=1)
doc.add_arc(arc1)

# Arc 2: P2 ⊸ T1 (inhibitor, blocks when P2 ≥ 2)
arc2 = InhibitorArc(source=p2, target=t1, id="A2", name="A2", weight=2.0)
doc.add_arc(arc2)

# Arc 3: T1 → P1 (produces to P1)
arc3 = Arc(source=t1, target=p1, id="A3", name="A3", weight=1)
doc.add_arc(arc3)

print("=" * 80)
print("TEST: Normal + Inhibitor arc from same place (P2)")
print("=" * 80)
print(f"\nInitial state:")
print(f"  P1 = {p1.tokens}")
print(f"  P2 = {p2.tokens}")
print(f"\nArcs:")
print(f"  A1: P2 → T1 (normal, weight=1)")
print(f"  A2: P2 ⊸ T1 (inhibitor, weight=2)")
print(f"  A3: T1 → P1 (normal, weight=1)")
print(f"\nTransition T1:")
print(f"  Type: {t1.transition_type}")
print(f"  Rate: {t1.rate}")

# Create behavior
behavior = ContinuousBehavior(t1, doc)

# Check enablement
enabled, reason = behavior.can_fire()

print(f"\n" + "-" * 80)
print(f"ENABLEMENT CHECK:")
print(f"  T1 enabled: {enabled}")
print(f"  Reason: {reason}")
print(f"-" * 80)

# Expected result
expected = False  # Should be disabled (P2=3 ≥ 2)
print(f"\nExpected: enabled = {expected}")
print(f"Actual:   enabled = {enabled}")

if enabled == expected:
    print("✅ TEST PASSED")
else:
    print("❌ TEST FAILED")
    
    # Debug: Check what arcs are being evaluated
    print(f"\nDEBUG INFO:")
    input_arcs = behavior.get_input_arcs()
    print(f"  Input arcs found: {len(input_arcs)}")
    for arc in input_arcs:
        arc_type = type(arc).__name__
        print(f"    - {arc.name}: {arc.source.name} → {arc.target.name}")
        print(f"      Type: {arc_type}")
        if hasattr(arc, 'weight'):
            print(f"      Weight: {arc.weight}")
        if isinstance(arc, InhibitorArc):
            print(f"      Source tokens: {arc.source.tokens}")
            print(f"      Check: {arc.source.tokens} >= {arc.weight} → {arc.source.tokens >= arc.weight}")

sys.exit(0 if enabled == expected else 1)
