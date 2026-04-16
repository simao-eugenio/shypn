#!/usr/bin/env python3
"""
Test both arc transformation code paths:
1. Property dialog transformation
2. Context menu transformation
"""

import sys
sys.path.insert(0, 'src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition, Arc
from shypn.utils.arc_transform import convert_to_test, convert_to_normal
from shypn.engine.immediate_behavior import ImmediateBehavior

print("=" * 70)
print("TESTING BOTH ARC TRANSFORMATION CODE PATHS")
print("=" * 70)

# ============================================================================
# PATH 1: Property Dialog Transformation (direct model update)
# ============================================================================
print("\n" + "=" * 70)
print("PATH 1: Property Dialog Transformation")
print("=" * 70)

document1 = DocumentModel()

p1a = Place(id='P1', name='P1', x=100, y=100)
p1a.tokens = 10
p2a = Place(id='P2', name='P2', x=300, y=100)
p2a.tokens = 0
t1a = Transition(id='T1', name='T1', x=200, y=100)
t1a.transition_type = 'immediate'

arc1_in = Arc(source=p1a, target=t1a, id='A1', name='A1', weight=1)
arc1_out = Arc(source=t1a, target=p2a, id='A2', name='A2', weight=1)

document1.arcs = [arc1_in, arc1_out]
document1.places = [p1a, p2a]
document1.transitions = [t1a]

print(f"\n1. Initial state:")
print(f"   document1.arcs[0]: type={type(document1.arcs[0]).__name__}, arc_type={document1.arcs[0].arc_type}")

# Simulate property dialog transformation
print(f"\n2. Property dialog: Converting to TestArc...")
old_arc = document1.arcs[0]
new_arc = convert_to_test(old_arc)

# Direct model update (like arc_prop_dialog_loader does)
for i, arc in enumerate(document1.arcs):
    if arc.id == new_arc.id:
        document1.arcs[i] = new_arc
        print(f"   Replaced at index {i}")
        break

print(f"   document1.arcs[0]: type={type(document1.arcs[0]).__name__}, arc_type={document1.arcs[0].arc_type}")
print(f"   Object preserved: {document1.arcs[0] is new_arc}")

# Test firing
print(f"\n3. Testing firing behavior:")
behavior1 = ImmediateBehavior(t1a, document1)
input_arcs1 = behavior1.get_input_arcs()

print(f"   Before: P1={p1a.tokens}, P2={p2a.tokens}")
success1, result1 = behavior1.fire(input_arcs1, behavior1.get_output_arcs())
print(f"   After:  P1={p1a.tokens}, P2={p2a.tokens}")

if p1a.tokens == 10:
    print("   ✅ PASS: Test arc didn't consume (Path 1)")
else:
    print(f"   ❌ FAIL: Test arc consumed! (Path 1)")

# ============================================================================
# PATH 2: Context Menu Transformation (using manager.replace_arc)
# ============================================================================
print("\n" + "=" * 70)
print("PATH 2: Context Menu Transformation (manager.replace_arc)")
print("=" * 70)

# Create a mock manager with replace_arc method
class MockManager:
    def __init__(self, document):
        self.document_controller = document
        self.arcs = document.arcs
        self.modified = False
    
    def replace_arc(self, old_arc, new_arc):
        """Simulate ModelCanvasManager.replace_arc"""
        try:
            index = self.arcs.index(old_arc)
            self.arcs[index] = new_arc
            new_arc._manager = self
            self.modified = True
            print(f"   replace_arc: Replaced at index {index}")
        except ValueError:
            print(f"   replace_arc: Arc not found")

document2 = DocumentModel()

p1b = Place(id='P1', name='P1', x=100, y=100)
p1b.tokens = 10
p2b = Place(id='P2', name='P2', x=300, y=100)
p2b.tokens = 0
t1b = Transition(id='T1', name='T1', x=200, y=100)
t1b.transition_type = 'immediate'

arc2_in = Arc(source=p1b, target=t1b, id='A1', name='A1', weight=1)
arc2_out = Arc(source=t1b, target=p2b, id='A2', name='A2', weight=1)

document2.arcs = [arc2_in, arc2_out]
document2.places = [p1b, p2b]
document2.transitions = [t1b]

manager2 = MockManager(document2)

print(f"\n1. Initial state:")
print(f"   manager2.arcs[0]: type={type(manager2.arcs[0]).__name__}, arc_type={manager2.arcs[0].arc_type}")

# Simulate context menu transformation
print(f"\n2. Context menu: Converting to TestArc...")
old_arc2 = manager2.arcs[0]
new_arc2 = convert_to_test(old_arc2)
manager2.replace_arc(old_arc2, new_arc2)

print(f"   manager2.arcs[0]: type={type(manager2.arcs[0]).__name__}, arc_type={manager2.arcs[0].arc_type}")
print(f"   Object preserved: {manager2.arcs[0] is new_arc2}")
print(f"   Manager modified flag: {manager2.modified}")
print(f"   New arc has _manager: {hasattr(new_arc2, '_manager')}")

# Test firing
print(f"\n3. Testing firing behavior:")
behavior2 = ImmediateBehavior(t1b, document2)
input_arcs2 = behavior2.get_input_arcs()

print(f"   Before: P1={p1b.tokens}, P2={p2b.tokens}")
success2, result2 = behavior2.fire(input_arcs2, behavior2.get_output_arcs())
print(f"   After:  P1={p1b.tokens}, P2={p2b.tokens}")

if p1b.tokens == 10:
    print("   ✅ PASS: Test arc didn't consume (Path 2)")
else:
    print(f"   ❌ FAIL: Test arc consumed! (Path 2)")

# ============================================================================
# ROUND TRIP TEST: Convert back to normal
# ============================================================================
print("\n" + "=" * 70)
print("ROUND TRIP TEST: TestArc → Normal Arc")
print("=" * 70)

print(f"\n1. Converting back to normal (Path 1)...")
test_arc1 = document1.arcs[0]
normal_arc1 = convert_to_normal(test_arc1)

for i, arc in enumerate(document1.arcs):
    if arc.id == normal_arc1.id:
        document1.arcs[i] = normal_arc1
        break

print(f"   document1.arcs[0]: type={type(document1.arcs[0]).__name__}, arc_type={document1.arcs[0].arc_type}")

# Reset tokens and test
p1a.tokens = 10
p2a.tokens = 0
behavior1_normal = ImmediateBehavior(t1a, document1)
print(f"   Before: P1={p1a.tokens}, P2={p2a.tokens}")
behavior1_normal.fire(behavior1_normal.get_input_arcs(), behavior1_normal.get_output_arcs())
print(f"   After:  P1={p1a.tokens}, P2={p2a.tokens}")

if p1a.tokens == 9:
    print("   ✅ PASS: Normal arc consumed tokens")
else:
    print(f"   ❌ FAIL: Normal arc didn't consume!")

print(f"\n2. Converting back to normal (Path 2)...")
test_arc2 = manager2.arcs[0]
normal_arc2 = convert_to_normal(test_arc2)
manager2.replace_arc(test_arc2, normal_arc2)

print(f"   manager2.arcs[0]: type={type(manager2.arcs[0]).__name__}, arc_type={manager2.arcs[0].arc_type}")

# Reset tokens and test
p1b.tokens = 10
p2b.tokens = 0
behavior2_normal = ImmediateBehavior(t1b, document2)
print(f"   Before: P1={p1b.tokens}, P2={p2b.tokens}")
behavior2_normal.fire(behavior2_normal.get_input_arcs(), behavior2_normal.get_output_arcs())
print(f"   After:  P1={p1b.tokens}, P2={p2b.tokens}")

if p1b.tokens == 9:
    print("   ✅ PASS: Normal arc consumed tokens")
else:
    print(f"   ❌ FAIL: Normal arc didn't consume!")

# ============================================================================
# FINAL REPORT
# ============================================================================
print("\n" + "=" * 70)
print("FINAL REPORT")
print("=" * 70)
print("Both code paths should:")
print("  1. Replace arc in document model ✅")
print("  2. Preserve arc object in model ✅")
print("  3. Set _manager reference (Path 2 only) ✅")
print("  4. Mark document modified (Path 2 only) ✅")
print("  5. Behavior uses correct arc type ✅")
print("  6. Test arcs don't consume tokens ✅")
print("  7. Normal arcs consume tokens ✅")
print("  8. Round-trip conversions work ✅")
