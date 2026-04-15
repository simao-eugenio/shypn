#!/usr/bin/env python3
"""Test arc consumption behavior - diagnose test arc bug."""

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.test_arc import TestArc

# Test 1: Direct TestArc instantiation
print("=" * 60)
print("TEST 1: Direct TestArc instantiation")
print("=" * 60)

p1 = Place(0, 0, "P1", "P1", label="Place1")
p1.set_tokens(10)
t1 = Transition(100, 0, "T1", "T1", label="Transition1")
test_arc = TestArc(source=p1, target=t1, id="TA1", name="TA1", weight=1)

print(f"Arc type: {test_arc.arc_type}")
print(f"Arc class: {type(test_arc).__name__}")
print(f"Has consumes_tokens: {hasattr(test_arc, 'consumes_tokens')}")
print(f"consumes_tokens() returns: {test_arc.consumes_tokens()}")
print(f"Is TestArc instance: {isinstance(test_arc, TestArc)}")

# Test 2: Regular Arc
print("\n" + "=" * 60)
print("TEST 2: Regular Arc")
print("=" * 60)

p2 = Place(0, 50, "P2", "P2", label="Place2")
p2.set_tokens(10)
t2 = Transition(100, 50, "T2", "T2", label="Transition2")
normal_arc = Arc(source=p2, target=t2, id="A1", name="A1", weight=1)

print(f"Arc type: {normal_arc.arc_type}")
print(f"Arc class: {type(normal_arc).__name__}")
print(f"Has consumes_tokens: {hasattr(normal_arc, 'consumes_tokens')}")
print(f"consumes_tokens() returns: {normal_arc.consumes_tokens()}")
print(f"Is TestArc instance: {isinstance(normal_arc, TestArc)}")

# Test 3: Arc.from_dict with arc_type='test'
print("\n" + "=" * 60)
print("TEST 3: Arc.from_dict with arc_type='test'")
print("=" * 60)

p3 = Place(0, 100, "P3", "P3", label="Place3")
p3.set_tokens(10)
t3 = Transition(100, 100, "T3", "T3", label="Transition3")

arc_data = {
    'id': 'A100',
    'name': 'A100',
    'source_id': 'P3',
    'target_id': 'T3',
    'weight': 1,
    'arc_type': 'test',
    'color': [0.0, 0.0, 1.0]
}

places = {'P3': p3}
transitions = {'T3': t3}

loaded_arc = Arc.from_dict(arc_data, places, transitions)

print(f"Arc type: {loaded_arc.arc_type}")
print(f"Arc class: {type(loaded_arc).__name__}")
print(f"Has consumes_tokens: {hasattr(loaded_arc, 'consumes_tokens')}")
print(f"consumes_tokens() returns: {loaded_arc.consumes_tokens()}")
print(f"Is TestArc instance: {isinstance(loaded_arc, TestArc)}")

# Test 4: Check the consumption logic like engines do
print("\n" + "=" * 60)
print("TEST 4: Consumption check logic (like engines)")
print("=" * 60)

test_arcs = [test_arc, normal_arc, loaded_arc]
for i, arc in enumerate(test_arcs, 1):
    print(f"\nArc {i} ({type(arc).__name__}):")
    
    # Current engine check
    should_skip = not arc.consumes_tokens()
    print(f"  should_skip = not arc.consumes_tokens() = {should_skip}")
    
    if should_skip:
        print(f"  → SKIP consumption (correct for test arcs)")
    else:
        print(f"  → CONSUME tokens (correct for normal arcs)")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("If test arcs are still consuming, check:")
print("1. Are arcs actually TestArc instances?")
print("2. Does consumes_tokens() return False?")
print("3. Is the consumption skip logic present in all engines?")
