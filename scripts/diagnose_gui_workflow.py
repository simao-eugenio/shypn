#!/usr/bin/env python3
"""
Diagnose arc type behavior in GUI - simulate full GUI conversion workflow
"""

import sys
sys.path.insert(0, 'src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition, Arc
from shypn.netobjs.test_arc import TestArc
from shypn.utils.arc_transform import convert_to_test
from shypn.engine.immediate_behavior import ImmediateBehavior

print("=" * 70)
print("SIMULATING GUI ARC CONVERSION WORKFLOW")
print("=" * 70)

# Step 1: Create model like GUI does
print("\n1. Creating DocumentModel with P1(10) → T → P2(0)...")
document = DocumentModel()

p1 = Place(id='P1', name='P1', x=100, y=100)
p1.tokens = 10
p2 = Place(id='P2', name='P2', x=300, y=100)
p2.tokens = 0
t = Transition(id='T1', name='T1', x=200, y=100)
t.transition_type = 'immediate'

# Create NORMAL arc like GUI does
arc_in = Arc(source=p1, target=t, id='A1', name='A1', weight=1)
arc_out = Arc(source=t, target=p2, id='A2', name='A2', weight=1)

document.arcs = [arc_in, arc_out]
document.places = [p1, p2]
document.transitions = [t]

print(f"   Created: arc_in type={type(arc_in).__name__}, arc_type={arc_in.arc_type}")
print(f"   document.arcs[0] is arc_in: {document.arcs[0] is arc_in}")

# Step 2: Convert arc like GUI dialog does
print("\n2. Converting arc A1 to TestArc (like GUI)...")
old_arc = document.arcs[0]
new_arc = convert_to_test(old_arc)

print(f"   Before replacement:")
print(f"     document.arcs[0] type={type(document.arcs[0]).__name__}, arc_type={document.arcs[0].arc_type}")
print(f"     Object ID: {id(document.arcs[0])}")

# Replace in model (like arc_prop_dialog_loader does)
for i, arc in enumerate(document.arcs):
    if arc.id == new_arc.id:
        document.arcs[i] = new_arc
        print(f"   Replaced arc at index {i}")
        break

print(f"   After replacement:")
print(f"     document.arcs[0] type={type(document.arcs[0]).__name__}, arc_type={document.arcs[0].arc_type}")
print(f"     Object ID: {id(document.arcs[0])}")
print(f"     document.arcs[0] is new_arc: {document.arcs[0] is new_arc}")

# Step 3: Create behavior and check what arcs it sees
print("\n3. Creating behavior and checking arcs...")
behavior = ImmediateBehavior(t, document)
input_arcs = behavior.get_input_arcs()

print(f"   Behavior sees {len(input_arcs)} input arcs:")
for arc in input_arcs:
    print(f"     - {arc.id}: type={type(arc).__name__}, arc_type={arc.arc_type}")
    print(f"       Object ID: {id(arc)}")
    print(f"       Is new_arc: {arc is new_arc}")
    print(f"       Is old_arc: {arc is old_arc}")

# Step 4: Check defensive pattern
print("\n4. Testing defensive pattern on retrieved arc...")
test_arc = input_arcs[0]
kind = getattr(test_arc, 'kind', getattr(test_arc, 'properties', {}).get('kind', 'normal'))
arc_type = getattr(test_arc, 'arc_type', 'normal')
should_skip = kind != 'normal' or arc_type in ('inhibitor', 'test')

print(f"   kind = {kind}")
print(f"   arc_type = {arc_type}")
print(f"   should_skip_consumption = {should_skip}")

# Step 5: Fire and check consumption
print("\n5. Firing transition...")
print(f"   Before: P1={p1.tokens}, P2={p2.tokens}")

success, result = behavior.fire(input_arcs, behavior.get_output_arcs())

print(f"   After:  P1={p1.tokens}, P2={p2.tokens}")
print(f"   Success: {success}")

# Step 6: Analysis
print("\n6. ANALYSIS:")
print("=" * 70)
if p1.tokens == 10:
    print("✅ PASS: P1 unchanged (test arc didn't consume)")
else:
    print(f"❌ FAIL: P1 consumed! 10 → {p1.tokens}")
    print(f"   Arc in behavior: type={type(input_arcs[0]).__name__}, arc_type={input_arcs[0].arc_type}")
    print(f"   Arc in document: type={type(document.arcs[0]).__name__}, arc_type={document.arcs[0].arc_type}")
    print(f"   Same object? {input_arcs[0] is document.arcs[0]}")

if p2.tokens == 1:
    print("✅ PASS: P2 gained 1 token")
else:
    print(f"❌ FAIL: P2 has {p2.tokens} tokens")
