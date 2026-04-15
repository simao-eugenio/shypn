#!/usr/bin/env python3
"""
Test token accounting across different scenarios.

This script validates that the simulation engine maintains token conservation
across all transition types and firing patterns.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from shypn.engine.accounting import TokenAccountingAuditor
from shypn.data.pathway_document import PathwayDocument
from shypn.engine.simulation.controller import SimulationController

def test_source_sink_accounting():
    """Test 1: Source and sink transitions."""
    print("\n" + "="*70)
    print("TEST 1: Source/Sink Accounting")
    print("="*70)
    
    # Create model: Source -> Place -> Sink
    doc = PathwayDocument()
    
    # Create place
    place = doc.add_place(x=100, y=100, marking=1000)
    place.id = 'P1'
    
    # Create source transition (produces tokens)
    source = doc.add_transition(x=50, y=100, transition_type='stochastic')
    source.id = 'Source'
    source.properties['is_source'] = True
    source.rate = 10.0
    
    # Create sink transition (consumes tokens)
    sink = doc.add_transition(x=150, y=100, transition_type='stochastic')
    sink.id = 'Sink'
    sink.properties['is_sink'] = True
    sink.rate = 5.0
    
    # Create arcs
    arc_produce = doc.add_arc(source, place, weight=5.0)
    arc_consume = doc.add_arc(place, sink, weight=3.0)
    
    # Setup simulation
    controller = SimulationController(doc)
    auditor = TokenAccountingAuditor(doc, strict_mode=False)
    auditor.enable()
    
    # Monkey-patch controller to use auditor
    original_fire = controller._fire_transition
    
    def fire_with_audit(transition):
        auditor.snapshot_before_fire(transition, controller.time)
        result = original_fire(transition)
        
        # Extract consumed/produced from result
        consumed = {}
        produced = {}
        if hasattr(transition, '_last_fire_consumed'):
            consumed = transition._last_fire_consumed
        if hasattr(transition, '_last_fire_produced'):
            produced = transition._last_fire_produced
            
        auditor.snapshot_after_fire(transition, controller.time, consumed, produced)
        return result
        
    controller._fire_transition = fire_with_audit
    
    # Run simulation
    print(f"\nInitial tokens: P1 = {place.tokens}")
    controller.run(duration=10.0, time_step=0.1)
    print(f"Final tokens: P1 = {place.tokens}")
    
    # Generate report
    auditor.print_report()
    
    report = auditor.generate_report()
    
    if report['leaks_detected']:
        print("❌ FAILED: Token leaks detected!")
        return False
    else:
        print("✅ PASSED: No token leaks")
        return True


def test_normal_transitions():
    """Test 2: Normal transitions (should conserve tokens)."""
    print("\n" + "="*70)
    print("TEST 2: Normal Transition Accounting")
    print("="*70)
    
    # Create model: P1 -> T -> P2
    doc = PathwayDocument()
    
    p1 = doc.add_place(x=50, y=100, marking=1000)
    p1.id = 'P1'
    p2 = doc.add_place(x=150, y=100, marking=0)
    p2.id = 'P2'
    
    trans = doc.add_transition(x=100, y=100, transition_type='stochastic')
    trans.id = 'T1'
    trans.rate = 5.0
    
    arc_in = doc.add_arc(p1, trans, weight=2.0)
    arc_out = doc.add_arc(trans, p2, weight=2.0)  # Should be same weight!
    
    # Setup simulation
    controller = SimulationController(doc)
    auditor = TokenAccountingAuditor(doc, strict_mode=True)  # Strict mode!
    auditor.enable()
    
    # Track token changes
    initial_total = p1.tokens + p2.tokens
    print(f"\nInitial: P1={p1.tokens}, P2={p2.tokens}, Total={initial_total}")
    
    try:
        controller.run(duration=10.0, time_step=0.1)
        final_total = p1.tokens + p2.tokens
        print(f"Final: P1={p1.tokens}, P2={p2.tokens}, Total={final_total}")
        
        auditor.print_report()
        
        # Check global conservation
        if abs(final_total - initial_total) > 1e-6:
            print(f"❌ FAILED: Total tokens changed by {final_total - initial_total}")
            return False
        else:
            print("✅ PASSED: Total tokens conserved")
            return True
            
    except RuntimeError as e:
        print(f"❌ FAILED: Conservation violation caught: {e}")
        auditor.print_report()
        return False


def test_continuous_flow():
    """Test 3: Continuous transitions."""
    print("\n" + "="*70)
    print("TEST 3: Continuous Flow Accounting")
    print("="*70)
    
    # Create model with continuous transition
    doc = PathwayDocument()
    
    p1 = doc.add_place(x=50, y=100, marking=1000)
    p1.id = 'P1'
    p2 = doc.add_place(x=150, y=100, marking=0)
    p2.id = 'P2'
    
    trans = doc.add_transition(x=100, y=100, transition_type='continuous')
    trans.id = 'Flow'
    trans.rate = 'P1 * 0.1'  # Flow proportional to P1
    
    arc_in = doc.add_arc(p1, trans, weight=1.0)
    arc_out = doc.add_arc(trans, p2, weight=1.0)
    
    # Setup simulation
    controller = SimulationController(doc)
    auditor = TokenAccountingAuditor(doc, strict_mode=False)
    auditor.enable()
    
    initial_total = p1.tokens + p2.tokens
    print(f"\nInitial: P1={p1.tokens}, P2={p2.tokens}, Total={initial_total}")
    
    controller.run(duration=10.0, time_step=0.1)
    
    final_total = p1.tokens + p2.tokens
    print(f"Final: P1={p1.tokens:.2f}, P2={p2.tokens:.2f}, Total={final_total:.2f}")
    
    auditor.print_report()
    
    # Continuous should conserve tokens
    leak = abs(final_total - initial_total)
    if leak > 0.1:  # Allow small numerical error
        print(f"❌ FAILED: Token leak of {leak:.6f}")
        return False
    else:
        print(f"✅ PASSED: Leak within tolerance ({leak:.6f})")
        return True


def test_mixed_transitions():
    """Test 4: Mixed transition types."""
    print("\n" + "="*70)
    print("TEST 4: Mixed Transition Types")
    print("="*70)
    
    # Create complex model with multiple transition types
    doc = PathwayDocument()
    
    # Places
    p1 = doc.add_place(x=50, y=100, marking=500)
    p1.id = 'P1'
    p2 = doc.add_place(x=150, y=100, marking=500)
    p2.id = 'P2'
    p3 = doc.add_place(x=100, y=200, marking=0)
    p3.id = 'P3'
    
    # Stochastic transition
    t1 = doc.add_transition(x=100, y=100, transition_type='stochastic')
    t1.id = 'Stoch'
    t1.rate = 2.0
    doc.add_arc(p1, t1, weight=1.0)
    doc.add_arc(t1, p3, weight=1.0)
    
    # Continuous transition
    t2 = doc.add_transition(x=100, y=150, transition_type='continuous')
    t2.id = 'Cont'
    t2.rate = 'P2 * 0.05'
    doc.add_arc(p2, t2, weight=1.0)
    doc.add_arc(t2, p3, weight=1.0)
    
    # Setup simulation
    controller = SimulationController(doc)
    auditor = TokenAccountingAuditor(doc, strict_mode=False)
    auditor.enable()
    
    initial_total = p1.tokens + p2.tokens + p3.tokens
    print(f"\nInitial: P1={p1.tokens}, P2={p2.tokens}, P3={p3.tokens}, Total={initial_total}")
    
    controller.run(duration=20.0, time_step=0.1)
    
    final_total = p1.tokens + p2.tokens + p3.tokens
    print(f"Final: P1={p1.tokens:.2f}, P2={p2.tokens:.2f}, P3={p3.tokens:.2f}, Total={final_total:.2f}")
    
    auditor.print_report()
    
    leak = abs(final_total - initial_total)
    if leak > 1.0:  # Allow some numerical error with mixed types
        print(f"❌ FAILED: Significant token leak of {leak:.6f}")
        return False
    else:
        print(f"✅ PASSED: Leak within tolerance ({leak:.6f})")
        return True


def main():
    """Run all accounting tests."""
    print("\n" + "="*70)
    print("TOKEN ACCOUNTING TEST SUITE")
    print("="*70)
    
    tests = [
        ("Source/Sink Accounting", test_source_sink_accounting),
        ("Normal Transitions", test_normal_transitions),
        ("Continuous Flow", test_continuous_flow),
        ("Mixed Transitions", test_mixed_transitions)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ {name} CRASHED: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed_count}/{total_count} passed")
    
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED - TOKEN ACCOUNTING VERIFIED")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED - TOKEN LEAKS DETECTED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
