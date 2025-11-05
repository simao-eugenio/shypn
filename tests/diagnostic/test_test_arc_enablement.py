#!/usr/bin/env python3
"""
Test that TestArc (catalyst) enablement works correctly.

This verifies the fix for catalyst interference in simulation.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.test_arc import TestArc
from shypn.engine.immediate_behavior import ImmediateBehavior

print("=" * 80)
print("TEST: TestArc Enablement in Simulation")
print("=" * 80)

# Create a simple model: Substrate + Enzyme -> Product
# Where Enzyme is connected via TestArc (non-consuming)

# Create places
substrate = Place(x=100, y=100, id="P1", name="P1", label="Substrate")
substrate.tokens = 10
substrate.initial_marking = 10

enzyme = Place(x=100, y=50, id="P2", name="P2", label="Enzyme")
enzyme.tokens = 1
enzyme.initial_marking = 1
enzyme.is_catalyst = True

product = Place(x=200, y=100, id="P3", name="P3", label="Product")
product.tokens = 0
product.initial_marking = 0

# Create transition
reaction = Transition(x=150, y=100, id="T1", name="T1", label="Reaction")
reaction.type = "immediate"

# Create arcs
# Normal arc: Substrate -> Reaction (consumes substrate)
arc_substrate = Arc(substrate, reaction, id="A1", name="A1", weight=1)

# TEST ARC: Enzyme -> Reaction (catalyst, non-consuming)
arc_enzyme = TestArc(enzyme, reaction, id="TA1", name="TA1", weight=1)

# Normal arc: Reaction -> Product (produces product)
arc_product = Arc(reaction, product, id="A2", name="A2", weight=1)

# Create mock model
class MockModel:
    def __init__(self):
        self.places = {
            "P1": substrate,
            "P2": enzyme,
            "P3": product
        }
        self.transitions = {
            "T1": reaction
        }
        self.arcs = {
            "A1": arc_substrate,
            "TA1": arc_enzyme,
            "A2": arc_product
        }

model = MockModel()

# Create behavior
behavior = ImmediateBehavior(reaction, model)

print("\n📊 Initial State:")
print("-" * 80)
print(f"  Substrate (P1): {substrate.tokens} tokens")
print(f"  Enzyme (P2): {enzyme.tokens} tokens (catalyst)")
print(f"  Product (P3): {product.tokens} tokens")

print("\n🔍 Arc Configuration:")
print("-" * 80)
print(f"  A1: Substrate -> Reaction (normal, weight=1, consumes=True)")
print(f"  TA1: Enzyme -> Reaction (TEST ARC, weight=1, consumes=False)")
print(f"  A2: Reaction -> Product (normal, weight=1)")

print("\n✓ Checking TestArc properties:")
print(f"  isinstance(arc_enzyme, TestArc): {isinstance(arc_enzyme, TestArc)}")
print(f"  arc_enzyme.is_test_arc(): {arc_enzyme.is_test_arc()}")
print(f"  arc_enzyme.consumes_tokens(): {arc_enzyme.consumes_tokens()}")

# Test 1: Check enablement WITH enzyme present
print("\n" + "=" * 80)
print("TEST 1: Enzyme present (tokens=1) - Should be ENABLED")
print("=" * 80)

enzyme.tokens = 1
enabled = behavior.is_enabled()
print(f"\n  Enzyme tokens: {enzyme.tokens}")
print(f"  Substrate tokens: {substrate.tokens}")
print(f"  Transition enabled: {enabled}")

if enabled:
    print("  ✅ PASS: Transition correctly enabled with catalyst present")
else:
    print("  ❌ FAIL: Transition should be enabled when catalyst has tokens")
    sys.exit(1)

# Test 2: Fire the transition
print("\n" + "=" * 80)
print("TEST 2: Fire transition - Enzyme should NOT be consumed")
print("=" * 80)

can_fire, reason = behavior.can_fire()
print(f"\n  can_fire(): {can_fire}, reason: {reason}")

if can_fire:
    # Get input and output arcs for fire() method
    input_arcs = [arc_substrate, arc_enzyme]
    output_arcs = [arc_product]
    
    result = behavior.fire(input_arcs, output_arcs)
    print(f"\n  After firing:")
    print(f"    Substrate tokens: {substrate.tokens} (should be 9)")
    print(f"    Enzyme tokens: {enzyme.tokens} (should be 1 - NOT consumed)")
    print(f"    Product tokens: {product.tokens} (should be 1)")
    
    if enzyme.tokens == 1:
        print("  ✅ PASS: Enzyme NOT consumed (catalyst behavior)")
    else:
        print(f"  ❌ FAIL: Enzyme should not be consumed, but tokens={enzyme.tokens}")
        sys.exit(1)
    
    if substrate.tokens == 9:
        print("  ✅ PASS: Substrate consumed correctly")
    else:
        print(f"  ❌ FAIL: Substrate should be 9, but tokens={substrate.tokens}")
        sys.exit(1)
    
    if product.tokens == 1:
        print("  ✅ PASS: Product produced correctly")
    else:
        print(f"  ❌ FAIL: Product should be 1, but tokens={product.tokens}")
        sys.exit(1)
else:
    print(f"  ❌ FAIL: Transition should be able to fire, reason: {reason}")
    sys.exit(1)

# Test 3: Fire again - should still work (catalyst reusable)
print("\n" + "=" * 80)
print("TEST 3: Fire again - Catalyst should be reusable")
print("=" * 80)

can_fire, reason = behavior.can_fire()
print(f"\n  can_fire(): {can_fire}, reason: {reason}")

if can_fire:
    input_arcs = [arc_substrate, arc_enzyme]
    output_arcs = [arc_product]
    
    result = behavior.fire(input_arcs, output_arcs)
    print(f"\n  After second firing:")
    print(f"    Substrate tokens: {substrate.tokens} (should be 8)")
    print(f"    Enzyme tokens: {enzyme.tokens} (should be 1 - still NOT consumed)")
    print(f"    Product tokens: {product.tokens} (should be 2)")
    
    if enzyme.tokens == 1 and substrate.tokens == 8 and product.tokens == 2:
        print("  ✅ PASS: Catalyst reused successfully")
    else:
        print("  ❌ FAIL: Catalyst reuse failed")
        sys.exit(1)
else:
    print(f"  ❌ FAIL: Should be able to fire again, reason: {reason}")
    sys.exit(1)

# Test 4: Remove enzyme - should DISABLE transition
print("\n" + "=" * 80)
print("TEST 4: Remove enzyme (tokens=0) - Should be DISABLED")
print("=" * 80)

enzyme.tokens = 0
enabled = behavior.is_enabled()
print(f"\n  Enzyme tokens: {enzyme.tokens}")
print(f"  Substrate tokens: {substrate.tokens}")
print(f"  Transition enabled: {enabled}")

if not enabled:
    print("  ✅ PASS: Transition correctly disabled without catalyst")
else:
    print("  ❌ FAIL: Transition should be disabled when catalyst absent")
    sys.exit(1)

# Test 5: Restore enzyme - should ENABLE again
print("\n" + "=" * 80)
print("TEST 5: Restore enzyme (tokens=1) - Should be ENABLED again")
print("=" * 80)

enzyme.tokens = 1
enabled = behavior.is_enabled()
print(f"\n  Enzyme tokens: {enzyme.tokens}")
print(f"  Substrate tokens: {substrate.tokens}")
print(f"  Transition enabled: {enabled}")

if enabled:
    print("  ✅ PASS: Transition correctly re-enabled with catalyst restored")
else:
    print("  ❌ FAIL: Transition should be enabled when catalyst restored")
    sys.exit(1)

print("\n" + "=" * 80)
print("ALL TESTS PASSED!")
print("=" * 80)
print("""
✅ TestArc (catalyst) enablement works correctly:
  - Enables transitions when catalyst present (tokens >= weight)
  - Does NOT consume catalyst tokens on firing
  - Allows catalyst reuse (multiple firings)
  - Disables transitions when catalyst absent (tokens < weight)
  - Re-enables when catalyst restored

This confirms the fix resolves catalyst interference in simulation.
""")
print("=" * 80)
