#!/usr/bin/env python3
"""
Diagnostic script for source/sink issues.
This will help identify what's happening with your source/sink model.
"""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.model import PetriNetModel
from shypn.engine.simulation.controller import SimulationController

print("="*80)
print("SOURCE/SINK DIAGNOSTIC TEST")
print("="*80)

# Create a simple source model:
# P1(0) ← T1(source) → P2(0)
# Expected: When T1 fires, P2 gets tokens WITHOUT P1 being consumed

print("\n1. Creating model...")
model = PetriNetModel()

# Create places
p1 = Place(x=100, y=100, id='P1', name='P1', label='Input Place')
p1.set_tokens(5)  # Give it some tokens
model.add_place(p1)

p2 = Place(x=300, y=100, id='P2', name='P2', label='Output Place')
p2.set_tokens(0)  # Start with 0
model.add_place(p2)

# Create source transition
t1 = Transition(x=200, y=100, id='T1', name='T1', label='Source Transition')
t1.transition_type = 'immediate'
t1.is_source = True  # MARK AS SOURCE
t1.is_sink = False
model.add_transition(t1)

print(f"   Created transition T1:")
print(f"     - transition_type: {t1.transition_type}")
print(f"     - is_source: {t1.is_source}")
print(f"     - is_sink: {t1.is_sink}")

# Create arcs
# P1 → T1 (input arc - should NOT consume tokens since T1 is source)
arc1 = Arc(source=p1, target=t1, id='A1', weight=1)
arc1.kind = 'normal'
model.add_arc(arc1)

# T1 → P2 (output arc - should produce tokens)
arc2 = Arc(source=t1, target=p2, id='A2', weight=3)
arc2.kind = 'normal'
model.add_arc(arc2)

print(f"\n   Created arcs:")
print(f"     - A1: P1 → T1 (weight=1)")
print(f"     - A2: T1 → P2 (weight=3)")

print(f"\n2. Initial marking:")
print(f"   P1: {p1.tokens} tokens")
print(f"   P2: {p2.tokens} tokens")

# Create simulation controller
print(f"\n3. Creating simulation controller...")
controller = SimulationController(model)

# Check if transition is enabled
print(f"\n4. Checking if T1 is enabled...")
enabled = controller._find_enabled_transitions()
print(f"   Enabled transitions: {[t.name for t in enabled]}")

if t1 in enabled:
    print(f"   ✅ T1 is enabled (as expected for source)")
    
    # Get behavior and check enablement reason
    behavior = controller._get_behavior(t1)
    can_fire, reason = behavior.can_fire()
    print(f"   Can fire: {can_fire}, Reason: {reason}")
    
    # Fire the transition
    print(f"\n5. Firing T1...")
    controller._fire_transition(t1)
    
    print(f"\n6. After firing:")
    print(f"   P1: {p1.tokens} tokens (expected: 5 - should NOT have changed)")
    print(f"   P2: {p2.tokens} tokens (expected: 3 - should have received tokens)")
    
    # Verify results
    print(f"\n7. Verification:")
    if p1.tokens == 5:
        print(f"   ✅ P1 unchanged (5 tokens) - Source behavior working!")
    else:
        print(f"   ❌ P1 changed from 5 to {p1.tokens} - Source behavior NOT working!")
    
    if p2.tokens == 3:
        print(f"   ✅ P2 received 3 tokens - Production working!")
    else:
        print(f"   ❌ P2 has {p2.tokens} tokens (expected 3) - Production NOT working!")
else:
    print(f"   ❌ T1 is NOT enabled - Something is wrong!")
    print(f"   This is unexpected for a source transition.")

# Now test with sink
print(f"\n" + "="*80)
print("SINK TRANSITION TEST")
print("="*80)

# Create a simple sink model:
# P3(5) → T2(sink)
# Expected: When T2 fires, P3 loses tokens but nothing is produced

print(f"\n1. Creating sink transition...")
p3 = Place(x=100, y=200, id='P3', name='P3', label='Input Place 2')
p3.set_tokens(5)
model.add_place(p3)

t2 = Transition(x=200, y=200, id='T2', name='T2', label='Sink Transition')
t2.transition_type = 'immediate'
t2.is_source = False
t2.is_sink = True  # MARK AS SINK
model.add_transition(t2)

print(f"   Created transition T2:")
print(f"     - transition_type: {t2.transition_type}")
print(f"     - is_source: {t2.is_source}")
print(f"     - is_sink: {t2.is_sink}")

# P3 → T2 (should consume tokens)
arc3 = Arc(source=p3, target=t2, id='A3', weight=2)
arc3.kind = 'normal'
model.add_arc(arc3)

print(f"\n   Created arc:")
print(f"     - A3: P3 → T2 (weight=2)")

print(f"\n2. Initial marking:")
print(f"   P3: {p3.tokens} tokens")

# Check if T2 is enabled
print(f"\n3. Checking if T2 is enabled...")
enabled = controller._find_enabled_transitions()
t2_enabled = t2 in enabled
print(f"   T2 enabled: {t2_enabled}")

if t2_enabled:
    print(f"   ✅ T2 is enabled")
    
    # Fire the transition
    print(f"\n4. Firing T2...")
    controller._fire_transition(t2)
    
    print(f"\n5. After firing:")
    print(f"   P3: {p3.tokens} tokens (expected: 3 = 5-2)")
    
    # Verify results
    print(f"\n6. Verification:")
    if p3.tokens == 3:
        print(f"   ✅ P3 lost 2 tokens (now 3) - Consumption working!")
    else:
        print(f"   ❌ P3 has {p3.tokens} tokens (expected 3) - Consumption NOT working!")
else:
    print(f"   ❌ T2 is NOT enabled - Should be enabled if P3 has ≥2 tokens")

print(f"\n" + "="*80)
print("DIAGNOSIS COMPLETE")
print("="*80)
print(f"\nIf all tests passed (✅), then source/sink is working correctly in the engine.")
print(f"If tests failed (❌), there's a bug in the implementation.")
print(f"\nIf engine works but your model doesn't, the issue is likely:")
print(f"  1. Transitions not marked as source/sink in the UI")
print(f"  2. Model not being loaded/saved correctly")
print(f"  3. Simulation not using the controller properly")
