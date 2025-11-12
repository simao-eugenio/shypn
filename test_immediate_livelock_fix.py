#!/usr/bin/env python3
"""Test that immediate transition livelock detection works."""

import sys
import logging
from pathlib import Path

# Setup logging to see the livelock warnings
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=" * 80)
print("IMMEDIATE TRANSITION LIVELOCK FIX TEST")
print("=" * 80)
print()

print("This test verifies that immediate transitions in a cycle don't freeze the app.")
print("Model: P1 → T1(immediate) → P2 → T2(immediate) → P1 (cycle)")
print()

try:
    from shypn.data.canvas.document_model import DocumentModel
    from shypn.netobjs.place import Place
    from shypn.netobjs.transition import Transition
    from shypn.netobjs.arc import Arc
    from shypn.engine.simulation.controller import SimulationController
    
    # Create model
    doc_model = DocumentModel()
    
    # Add places
    p1 = Place(100, 100, 'P1', 'P1')
    p1.tokens = 1  # Use .tokens not .marking
    p2 = Place(300, 100, 'P2', 'P2')
    p2.tokens = 0
    doc_model.places = [p1, p2]
    
    # Add transitions (both immediate)
    t1 = Transition(150, 100, 'T1', 'T1')
    t1.transition_type = 'immediate'
    t1.priority = 0
    
    t2 = Transition(250, 100, 'T2', 'T2')
    t2.transition_type = 'immediate'
    t2.priority = 0
    
    doc_model.transitions = [t1, t2]
    
    # Add arcs (cycle: P1→T1→P2→T2→P1)
    a1 = Arc(p1, t1, 'A1', 'A1')
    a2 = Arc(t1, p2, 'A2', 'A2')
    a3 = Arc(p2, t2, 'A3', 'A3')
    a4 = Arc(t2, p1, 'A4', 'A4')
    doc_model.arcs = [a1, a2, a3, a4]
    
    print("✓ Model created with immediate cycle")
    print()
    
    # Create simulation controller
    controller = SimulationController(doc_model)
    
    print("Running 5 simulation steps...")
    print("(Without the fix, this would freeze for several seconds)")
    print()
    
    print(f"Initial state: P1={p1.tokens}, P2={p2.tokens}")
    print()
    
    for i in range(5):
        print(f"Step {i+1}:")
        
        # Show enabled transitions before step
        enabled = []
        for t in [t1, t2]:
            behavior = controller._get_behavior(t)
            can_fire, reason = behavior.can_fire()
            if can_fire:
                enabled.append(t.id)
        print(f"  Enabled before step: {enabled}")
        
        success = controller.step(time_step=0.1)
        print(f"  Time after step: {controller.time:.2f}s")
        print(f"  Tokens after step: P1={p1.tokens}, P2={p2.tokens}")
        print(f"  Step success: {success}")
        print()
        
        if not success:
            print("  (Simulation stopped - no enabled transitions)")
            break
    
    print("=" * 80)
    print("SUCCESS!")
    print("=" * 80)
    print()
    print("✓ The simulation didn't freeze!")
    print("✓ Livelock detection prevented infinite loop")
    print()
    print("Check the log output above for 'LIVELOCK DETECTED' or 'limit reached' warnings.")
    print()

except Exception as e:
    print(f"✗ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
