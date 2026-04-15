#!/usr/bin/env python3
"""Diagnose weight=0 signal_flow arc bug.

Creates minimal P1→T1→P2 network where:
- P1 is signal place with weight=0 arc
- Traces token flow during simulation
"""

import sys
sys.path.insert(0, 'src')

from shypn.core.BiologicalPetriNet import BiologicalPetriNet
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.signal_flow_arc import SignalFlowArc
from shypn.netobjs.arc import Arc
from shypn.engine.continuous_behavior import ContinuousBehavior

# Create minimal model
model = BiologicalPetriNet()

# Places
p1 = Place(x=100, y=100, id="P1", name="P1_Signal", label="Signal")
p1.is_signal_place = True
p1.set_tokens(100.0)  # Start with 100 tokens
p1.set_initial_marking(100.0)

p2 = Place(x=300, y=100, id="P2", name="P2_Product", label="Product")
p2.set_tokens(0.0)
p2.set_initial_marking(0.0)

# Transition  
t1 = Transition(x=200, y=100, id="T1", name="T1_Convert", label="Convert")
t1.transition_type = "continuous"
t1.rate_function = "1.0"  # Constant rate

# Arcs
# A1: P1 → T1 (signal_flow, weight=0)
a1 = SignalFlowArc(source=p1, target=t1, id="A1", name="A1", weight=0.0)

# A2: T1 → P2 (normal, weight=1)
a2 = Arc(source=t1, target=p2, id="A2", name="A2", weight=1.0)

# Add to model
model.add_place(p1)
model.add_place(p2)
model.add_transition(t1)
model.add_arc(a1)
model.add_arc(a2)

print("=" * 80)
print("WEIGHT=0 SIGNAL_FLOW ARC BUG DIAGNOSIS")
print("=" * 80)
print()
print("Model Structure:")
print(f"  P1 (signal, {p1.tokens} tokens) → T1 (rate=1.0) → P2 ({p2.tokens} tokens)")
print(f"  Arc A1: P1→T1, type={a1.arc_type}, weight={a1.weight}, consumes={a1.consumes_tokens()}")
print(f"  Arc A2: T1→P2, type={a2.arc_type}, weight={a2.weight}")
print()

# Create behavior
behavior = ContinuousBehavior(t1, model)

# Get arcs
input_arcs = behavior.get_input_arcs()
output_arcs = behavior.get_output_arcs()

print("Arc Classification:")
print(f"  Input arcs: {[f'{a.id} ({a.source.name}→{a.target.name}, w={a.weight})' for a in input_arcs]}")
print(f"  Output arcs: {[f'{a.id} ({a.source.name}→{a.target.name}, w={a.weight})' for a in output_arcs]}")
print()

# Check enablement
can_fire, reason = behavior.can_fire()
print(f"Can fire: {can_fire} ({reason})")
print()

# Simulate one time step
print("Simulating dt=1.0 second...")
print(f"  Before: P1={p1.tokens:.6f}, P2={p2.tokens:.6f}")

success, details = behavior.integrate_step(dt=1.0, input_arcs=input_arcs, output_arcs=output_arcs)

print(f"  After:  P1={p1.tokens:.6f}, P2={p2.tokens:.6f}")
print()

if success:
    print("Firing Details:")
    print(f"  Success: {success}")
    print(f"  Consumed: {details.get('consumed', {})}")
    print(f"  Produced: {details.get('produced', {})}")
    print(f"  Rate: {details.get('rate', 0.0)}")
    print(f"  Actual rate: {details.get('actual_rate', 0.0)}")
    print()

# Check changes
p1_change = p1.tokens - 100.0
p2_change = p2.tokens - 0.0

print("Token Changes:")
print(f"  P1: {p1_change:+.6f} (expected: 0.0)")
print(f"  P2: {p2_change:+.6f} (expected: +1.0)")
print()

# Verify conservation
total_before = 100.0 + 0.0
total_after = p1.tokens + p2.tokens
print(f"Conservation Check:")
print(f"  Total before: {total_before:.6f}")
print(f"  Total after:  {total_after:.6f}")
print(f"  Change: {total_after - total_before:+.6f}")
print()

# Check if P1 was incorrectly modified
if abs(p1_change) > 1e-10:
    print("⚠️  BUG DETECTED: P1 (signal place with weight=0) was modified!")
    print(f"   Expected: P1 should remain at 100.0 (read-only)")
    print(f"   Actual: P1 changed by {p1_change:+.6f}")
    print()
    print("Root cause analysis:")
    print("  - Signal_flow arcs with weight=0 should be READ-ONLY")
    print("  - Phase 2 (consumption) correctly skips them (weight*flow = 0)")
    print("  - Phase 3 (production) may be producing back to them")
    print()
else:
    print("✓ P1 correctly unchanged (read-only signal place)")
    print()

if abs(p2_change - 1.0) > 1e-6:
    print(f"⚠️  WARNING: P2 change ({p2_change:.6f}) != expected (1.0)")
else:
    print("✓ P2 correctly received 1.0 token")

print()
print("=" * 80)
