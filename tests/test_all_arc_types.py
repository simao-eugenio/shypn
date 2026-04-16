#!/usr/bin/env python3
"""Comprehensive test: All arc types with defensive pattern."""

import sys
sys.path.insert(0, 'src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition, Arc
from shypn.netobjs.test_arc import TestArc
from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.netobjs.signal_flow_arc import SignalFlowArc
from shypn.engine.immediate_behavior import ImmediateBehavior

print("=" * 70)
print("Comprehensive Arc Type Test (v2.1.0 Defensive Pattern)")
print("=" * 70)

# Test 1: Normal Arc (consumes tokens)
print("\n" + "=" * 70)
print("TEST 1: Normal Arc (should consume)")
print("=" * 70)

document = DocumentModel()
p1 = Place(id="P1", name="P1", label="Place 1", x=100, y=100)
p1.tokens = 10
p2 = Place(id="P2", name="P2", label="Place 2", x=300, y=100)
p2.tokens = 0
t1 = Transition(id="T1", name="T1", label="Trans 1", x=200, y=100)
t1.transition_type = "immediate"

arc1 = Arc(source=p1, target=t1, id="A1", name="A1", weight=1.0)
arc2 = Arc(source=t1, target=p2, id="A2", name="A2", weight=1.0)

document.places = [p1, p2]
document.transitions = [t1]
document.arcs = [arc1, arc2]

behavior = ImmediateBehavior(t1, document)
input_arcs = behavior.get_input_arcs()
output_arcs = behavior.get_output_arcs()

print(f"Arc type: {type(arc1).__name__}, arc_type={arc1.arc_type}")
print(f"Before: P1={p1.tokens}, P2={p2.tokens}")

success, result = behavior.fire(input_arcs, output_arcs)

print(f"After:  P1={p1.tokens}, P2={p2.tokens}")

if p1.tokens == 9 and p2.tokens == 1:
    print("✓ PASS: Normal arc consumed 1 token")
else:
    print(f"✗ FAIL: Expected P1=9, P2=1, got P1={p1.tokens}, P2={p2.tokens}")

# Test 2: TestArc (does NOT consume)
print("\n" + "=" * 70)
print("TEST 2: TestArc (should NOT consume)")
print("=" * 70)

document2 = DocumentModel()
p3 = Place(id="P3", name="P3", label="Place 3", x=100, y=100)
p3.tokens = 10
p4 = Place(id="P4", name="P4", label="Place 4", x=300, y=100)
p4.tokens = 0
t2 = Transition(id="T2", name="T2", label="Trans 2", x=200, y=100)
t2.transition_type = "immediate"

arc3 = TestArc(source=p3, target=t2, id="A3", name="A3", weight=1.0)
arc4 = Arc(source=t2, target=p4, id="A4", name="A4", weight=1.0)

document2.places = [p3, p4]
document2.transitions = [t2]
document2.arcs = [arc3, arc4]

behavior2 = ImmediateBehavior(t2, document2)
input_arcs2 = behavior2.get_input_arcs()
output_arcs2 = behavior2.get_output_arcs()

print(f"Arc type: {type(arc3).__name__}, arc_type={arc3.arc_type}")
print(f"Before: P3={p3.tokens}, P4={p4.tokens}")

success2, result2 = behavior2.fire(input_arcs2, output_arcs2)

print(f"After:  P3={p3.tokens}, P4={p4.tokens}")

if p3.tokens == 10 and p4.tokens == 1:
    print("✓ PASS: TestArc did NOT consume tokens")
else:
    print(f"✗ FAIL: Expected P3=10, P4=1, got P3={p3.tokens}, P4={p4.tokens}")

# Test 3: InhibitorArc enablement (inverted logic)
print("\n" + "=" * 70)
print("TEST 3: InhibitorArc Enablement")
print("=" * 70)

document3 = DocumentModel()
p5 = Place(id="P5", name="P5", label="Product Place", x=100, y=100)
p5.tokens = 5  # Product level
p6 = Place(id="P6", name="P6", label="Substrate", x=100, y=200)
p6.tokens = 10
p7 = Place(id="P7", name="P7", label="Output", x=300, y=150)
p7.tokens = 0
t3 = Transition(id="T3", name="T3", label="Production", x=200, y=150)
t3.transition_type = "immediate"

arc5 = InhibitorArc(source=p5, target=t3, id="A5", name="A5", weight=8.0)  # Inhibitor threshold = 8
arc6 = Arc(source=p6, target=t3, id="A6", name="A6", weight=1.0)  # Normal substrate
arc7 = Arc(source=t3, target=p7, id="A7", name="A7", weight=1.0)

document3.places = [p5, p6, p7]
document3.transitions = [t3]
document3.arcs = [arc5, arc6, arc7]

behavior3 = ImmediateBehavior(t3, document3)

print(f"Inhibitor arc: {type(arc5).__name__}, arc_type={arc5.arc_type}")
print(f"Product level (P5): {p5.tokens} (threshold: 8.0)")

can_fire, reason = behavior3.can_fire()
print(f"Can fire: {can_fire} (reason: {reason})")

if can_fire:
    print("✓ PASS: Transition enabled (product < threshold)")
else:
    print("✗ FAIL: Transition should be enabled when product is below threshold")

# Now increase product to inhibit
p5.tokens = 10  # Above threshold
can_fire2, reason2 = behavior3.can_fire()
print(f"\nAfter increasing product to 10:")
print(f"Can fire: {can_fire2} (reason: {reason2})")

if not can_fire2:
    print("✓ PASS: Transition inhibited (product >= threshold)")
else:
    print("✗ FAIL: Transition should be inhibited when product is above threshold")

# Test 4: SignalFlowArc (consumes tokens like normal arc)
print("\n" + "=" * 70)
print("TEST 4: SignalFlowArc (should consume like normal)")
print("=" * 70)

document4 = DocumentModel()
p8 = Place(id="P8", name="P8", label="Signal Place", x=100, y=100)
p8.tokens = 10
p8.is_signal_place = True  # Mark as signal place
p9 = Place(id="P9", name="P9", label="Target Place", x=300, y=100)
p9.tokens = 0
t4 = Transition(id="T4", name="T4", label="Signal Trans", x=200, y=100)
t4.transition_type = "immediate"

arc8 = SignalFlowArc(source=p8, target=t4, id="A8", name="A8", weight=1.0)
arc9 = Arc(source=t4, target=p9, id="A9", name="A9", weight=1.0)

document4.places = [p8, p9]
document4.transitions = [t4]
document4.arcs = [arc8, arc9]

behavior4 = ImmediateBehavior(t4, document4)
input_arcs4 = behavior4.get_input_arcs()
output_arcs4 = behavior4.get_output_arcs()

print(f"Arc type: {type(arc8).__name__}, arc_type={arc8.arc_type}")
print(f"Before: P8={p8.tokens}, P9={p9.tokens}")

success4, result4 = behavior4.fire(input_arcs4, output_arcs4)

print(f"After:  P8={p8.tokens}, P9={p9.tokens}")

if p8.tokens == 9 and p9.tokens == 1:
    print("✓ PASS: SignalFlowArc consumed 1 token")
else:
    print(f"✗ FAIL: Expected P8=9, P9=1, got P8={p8.tokens}, P9={p9.tokens}")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("All arc types tested with v2.1.0 defensive pattern:")
print("  - kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))")
print("  - arc_type = getattr(arc, 'arc_type', 'normal')")
print("  - Checks: kind != 'normal' or arc_type in ('inhibitor', 'test')")
print("\nThis pattern is more robust than isinstance() checks and matches")
print("the proven stable v2.1.0-validation-complete version.")
