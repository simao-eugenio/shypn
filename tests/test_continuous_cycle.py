#!/usr/bin/env python3
"""Test continuous transitions in a cycle to check for hang/freeze."""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=" * 80)
print("CONTINUOUS TRANSITION CYCLE TEST")
print("=" * 80)
print()

print("This test verifies that continuous transitions in a cycle don't hang.")
print("Model: P1 → T1(continuous) → P2 → T2(continuous) → P1 (cycle)")
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
    p1.tokens = 1.0
    p2 = Place(300, 100, 'P2', 'P2')
    p2.tokens = 0.0
    doc_model.places = [p1, p2]
    
    # Add transitions (both continuous with rate=1.0)
    t1 = Transition(150, 100, 'T1', 'T1')
    t1.transition_type = 'continuous'
    t1.rate = 1.0
    
    t2 = Transition(250, 100, 'T2', 'T2')
    t2.transition_type = 'continuous'
    t2.rate = 1.0
    
    doc_model.transitions = [t1, t2]
    
    # Add arcs (cycle: P1→T1→P2→T2→P1)
    a1 = Arc(p1, t1, 'A1', 'A1')
    a2 = Arc(t1, p2, 'A2', 'A2')
    a3 = Arc(p2, t2, 'A3', 'A3')
    a4 = Arc(t2, p1, 'A4', 'A4')
    doc_model.arcs = [a1, a2, a3, a4]
    
    print("✓ Model created with continuous cycle")
    print(f"  T1: continuous, rate={t1.rate}")
    print(f"  T2: continuous, rate={t2.rate}")
    print()
    
    # Create simulation controller
    controller = SimulationController(doc_model)
    
    print("Running 10 simulation steps with dt=0.1...")
    print("(Checking if continuous transitions cause hang)")
    print()
    
    print(f"Initial state: P1={p1.tokens:.3f}, P2={p2.tokens:.3f}")
    print()
    
    import time
    start_time = time.time()
    
    for i in range(10):
        step_start = time.time()
        
        # Show enabled transitions before step
        enabled = []
        for t in [t1, t2]:
            behavior = controller._get_behavior(t)
            can_fire, reason = behavior.can_fire()
            if can_fire:
                enabled.append(t.id)
        
        success = controller.step(time_step=0.1)
        
        step_duration = time.time() - step_start
        
        print(f"Step {i+1}:")
        print(f"  Enabled: {enabled}")
        print(f"  Time: {controller.time:.2f}s")
        print(f"  Tokens: P1={p1.tokens:.3f}, P2={p2.tokens:.3f}")
        print(f"  Success: {success}")
        print(f"  Step duration: {step_duration*1000:.1f}ms")
        
        # Warn if step takes too long
        if step_duration > 0.5:
            print(f"  ⚠️  WARNING: Step took {step_duration:.2f}s - possible performance issue!")
        
        print()
        
        if not success:
            print("  (Simulation stopped)")
            break
    
    total_duration = time.time() - start_time
    
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()
    print(f"✓ Completed {i+1} steps in {total_duration:.2f}s")
    print(f"✓ Average step time: {(total_duration/(i+1))*1000:.1f}ms")
    print()
    
    if total_duration > 5.0:
        print("❌ PERFORMANCE ISSUE: Simulation took too long!")
        print("   This suggests a hang or performance problem with continuous transitions.")
    else:
        print("✓ NO HANG DETECTED: Continuous transitions work correctly!")
    print()

except Exception as e:
    print(f"✗ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
