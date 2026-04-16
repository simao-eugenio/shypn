#!/usr/bin/env python3
"""Test: Simulate GUI arc conversion to test arc and verify firing behavior."""

import sys
sys.path.insert(0, 'src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition, Arc
from shypn.netobjs.test_arc import TestArc
from shypn.utils.arc_transform import convert_to_test
from shypn.engine.immediate_behavior import ImmediateBehavior

print("=" * 70)
print("Testing GUI Arc Conversion Workflow")
print("=" * 70)

# Step 1: Create model with normal arc (like drawing in GUI)
print("\n1. Creating P(25)→T(immediate)→P(0) with normal arc...")
document = DocumentModel()

p1 = Place(id="P1", name="P1", label="Source Place", x=100, y=100)
p1.tokens = 25
p2 = Place(id="P2", name="P2", label="Target Place", x=300, y=100)
p2.tokens = 0

t1 = Transition(id="T1", name="T1", label="Test Transition", x=200, y=100)
t1.transition_type = "immediate"

# Create NORMAL arc from P1 to T1 (default behavior when drawing)
arc1 = Arc(source=p1, target=t1, id="A1", name="A1", weight=1.0)
arc2 = Arc(source=t1, target=p2, id="A2", name="A2", weight=1.0)

document.places = [p1, p2]
document.transitions = [t1]
document.arcs = [arc1, arc2]

print(f"   P1: {p1.tokens} tokens")
print(f"   P2: {p2.tokens} tokens")
print(f"   Arc A1: {type(arc1).__name__}, arc_type={arc1.arc_type}, consumes={arc1.consumes_tokens()}")

# Step 2: Convert arc to test arc (simulating right-click menu action)
print("\n2. Converting A1 to test arc (simulating GUI action)...")
new_arc1 = convert_to_test(arc1)
# Replace in model (this is what manager.replace_arc does)
document.arcs[0] = new_arc1

print(f"   New arc A1: {type(new_arc1).__name__}, arc_type={new_arc1.arc_type}, consumes={new_arc1.consumes_tokens()}")
print(f"   Arc in document.arcs[0]: {type(document.arcs[0]).__name__}, consumes={document.arcs[0].consumes_tokens()}")

# Step 3: Create behavior and fire (simulating "Step" button click)
print("\n3. Creating behavior and firing transition...")
behavior = ImmediateBehavior(t1, document)

# Get arcs from behavior (this is what happens in firing)
input_arcs = behavior.get_input_arcs()
output_arcs = behavior.get_output_arcs()

print(f"   Input arcs retrieved by behavior: {len(input_arcs)}")
for arc in input_arcs:
    print(f"      - {arc.id}: {type(arc).__name__}, arc_type={arc.arc_type}, consumes={arc.consumes_tokens()}")

print(f"   Output arcs retrieved by behavior: {len(output_arcs)}")
for arc in output_arcs:
    print(f"      - {arc.id}: {type(arc).__name__}")

# Fire the transition
print("\n4. Firing transition T1...")
success, result = behavior.fire(input_arcs, output_arcs)

print(f"\n   Fire result: {success}")
print(f"   Consumed: {result.get('consumed', {})}")
print(f"   Produced: {result.get('produced', {})}")

print(f"\n5. AFTER firing:")
print(f"   P1: {p1.tokens} tokens")
print(f"   P2: {p2.tokens} tokens")

# Analysis
print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)

if p1.tokens == 25:
    print("✓ CORRECT: P1 tokens unchanged (test arc did NOT consume)")
else:
    print(f"✗ BUG: P1 tokens changed from 25 to {p1.tokens}")
    print(f"   Arc in model: {type(document.arcs[0]).__name__}")
    print(f"   Arc retrieved by behavior: {type(input_arcs[0]).__name__}")
    print(f"   Are they the same object? {input_arcs[0] is document.arcs[0]}")

if p2.tokens == 1:
    print("✓ CORRECT: P2 gained 1 token")
else:
    print(f"✗ BUG: P2 has {p2.tokens} tokens (expected 1)")
