#!/usr/bin/env python3
"""Test script to verify test arc weight bug hypothesis.

This tests two scenarios:
1. Normal transition with test arc (weight=0.5)
2. Source transition with test arc (weight=0.5)

Expected behavior:
- Test arcs should NOT affect transition rates
- Both models should show rate ≈ 2.27 firings/s

Bug symptoms (if exists):
- Test arc weight=0.5 causes rate to be ~1.14 firings/s (50% of expected)

Models:
- test_arc_normal_transition.shy: Normal continuous transition
- test_arc_source_transition.shy: Source transition (like T20 in Bacillus)
"""

import sys
import os

# Add src to path (from thermodynamics folder: ../../../.. gets to repo root, then src)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController

def test_model(model_path, model_name):
    """Test a single model and report results."""
    print("="*80)
    print(f"Testing: {model_name}")
    print("="*80)
    
    # Load model
    print(f"Loading: {model_path}")
    doc = DocumentModel.load_from_file(model_path)
    
    # WORKAROUND: DocumentModel doesn't seem to load tokens correctly
    # Set them manually from the file
    import json
    with open(model_path, 'r') as f:
        model_data = json.load(f)
    
    # Restore tokens from JSON (use 'marking' field, not 'tokens')
    for place_data in model_data['places']:
        place = next((p for p in doc.places if p.id == place_data['id']), None)
        if place:
            marking = place_data.get('marking', place_data.get('initial_marking', 0.0))
            place.set_tokens(marking)
    
    # Display model configuration
    t1 = doc.transitions[0]
    print(f"\nTransition: {t1.name}")
    print(f"  Type: {t1.transition_type}")
    print(f"  Is source: {getattr(t1, 'is_source', False)}")
    print(f"  Rate function: {t1.rate_function}")
    
    test_place = doc.places[0]
    print(f"\nTest Place: {test_place.name}")
    print(f"  Initial tokens: {test_place.tokens} mM")
    print(f"  Place ID: {test_place.id}")
    print(f"  Place type: {type(test_place)}")
    
    # Debug: check all attributes
    if test_place.tokens == 0:
        print(f"  WARNING: Tokens are 0! Checking attributes...")
        for attr in dir(test_place):
            if not attr.startswith('_') and 'token' in attr.lower():
                print(f"    {attr}: {getattr(test_place, attr, 'N/A')}")
    
    # Find test arc
    test_arc = None
    for arc in doc.arcs:
        if hasattr(arc, 'arc_type') and arc.arc_type == 'test':
            test_arc = arc
            break
    
    if test_arc:
        print(f"\nTest Arc: {test_arc.id}")
        print(f"  Type: {test_arc.arc_type}")
        print(f"  Weight: {test_arc.weight}")
        print(f"  Consumes: {test_arc.consumes_tokens() if hasattr(test_arc, 'consumes_tokens') else 'N/A'}")
    
    # Calculate expected rate
    expected_rate = 2.5 * test_place.tokens / (10 + test_place.tokens)
    print(f"\nExpected rate: {expected_rate:.3f} firings/s")
    print(f"If bug exists (weight=0.5 scales rate): {expected_rate * 0.5:.3f} firings/s")
    
    # Run simulation
    print("\n" + "-"*80)
    print("Running simulation (10 seconds, 0.001 time step)...")
    print("-"*80)
    
    controller = SimulationController(doc, verbose=False, recording_interval=100)
    
    # Set time step in settings
    time_step = 0.001
    controller.settings.time_step = time_step
    
    # Debug: check if transition can fire
    t1_behavior = controller._get_behavior(t1)
    can_fire, reason = t1_behavior.can_fire()
    print(f"Before simulation: Transition can_fire={can_fire}, reason={reason}")
    
    # Start data collection
    if controller.data_collector:
        controller.data_collector.start_collection()
        controller.data_collector.record_state(controller.time)
    
    # Run simulation manually (not using GUI event loop)
    num_steps = int(10.0 / time_step)
    for i in range(num_steps):
        controller.step(time_step=time_step)
        # Record data every 100 steps
        if i % 100 == 0 and controller.data_collector:
            controller.data_collector.record_state(controller.time)
    
    # Final data recording
    if controller.data_collector:
        controller.data_collector.record_state(controller.time)
    
    print(f"After simulation: Time={controller.time:.3f}s, Steps={num_steps}")
    
    # Analyze results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    
    # Get transition from controller's model
    t1_after = next((t for t in controller.model.transitions if t.id == 'T1'), None)
    if t1_after:
        firing_count = getattr(t1_after, 'firing_count', 0)
        observed_rate = firing_count / 10.0
        
        print(f"Total firings: {firing_count:.3f}")
        print(f"Observed rate: {observed_rate:.3f} firings/s")
        print(f"Expected rate: {expected_rate:.3f} firings/s")
        print(f"Ratio (observed/expected): {observed_rate / expected_rate:.3f}")
        print()
        
        # Determine if bug exists
        if abs(observed_rate / expected_rate - 0.5) < 0.1:
            print("❌ BUG DETECTED: Rate is ~50% of expected!")
            print("   Test arc weight=0.5 is incorrectly scaling the transition rate.")
            return False
        elif abs(observed_rate / expected_rate - 1.0) < 0.1:
            print("✅ PASS: Rate matches expected (within 10%)")
            print("   Test arc weight does NOT affect transition rate.")
            return True
        else:
            print(f"⚠️  UNEXPECTED: Ratio {observed_rate/expected_rate:.3f} doesn't match known patterns")
            print("   Further investigation needed.")
            return None
    else:
        print("ERROR: Could not find transition T1 after simulation")
        return None
    
    print()

def main():
    """Run tests on both models."""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "TEST ARC WEIGHT BUG VERIFICATION" + " "*26 + "║")
    print("╚" + "="*78 + "╝")
    print()
    
    # Test 1: Normal transition
    result1 = test_model(
        'test_arc_normal_transition.shy',
        'Normal Transition (is_source=False)'
    )
    
    print("\n")
    
    # Test 2: Source transition
    result2 = test_model(
        'test_arc_source_transition.shy',
        'Source Transition (is_source=True, like T20)'
    )
    
    # Summary
    print("\n")
    print("="*80)
    print("SUMMARY")
    print("="*80)
    
    if result1 is True and result2 is True:
        print("✅ ALL TESTS PASSED")
        print("   Test arc weights do NOT affect transition rates.")
        print("   The code is working correctly.")
    elif result1 is False or result2 is False:
        print("❌ BUG CONFIRMED")
        print("   Test arc weights ARE incorrectly affecting transition rates.")
        if result1 is False and result2 is True:
            print("   Bug affects NORMAL transitions only (not source transitions).")
        elif result1 is True and result2 is False:
            print("   Bug affects SOURCE transitions only (surprising!).")
        else:
            print("   Bug affects BOTH normal and source transitions.")
    else:
        print("⚠️  INCONCLUSIVE")
        print("   Results don't match expected patterns.")
    
    print()
    print("Next steps:")
    if result1 is False or result2 is False:
        print("  1. Fix the bug in continuous_behavior.py")
        print("  2. Re-run tests to verify fix")
        print("  3. Test with Bacillus model")
    else:
        print("  1. Investigate alternative causes for the 50% rate reduction in Bacillus")
        print("  2. Check if T20 is actually treated as a source at runtime")
        print("  3. Verify the hypothesis with Bacillus model directly")
    
    print()

if __name__ == '__main__':
    main()
