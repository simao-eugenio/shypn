#!/usr/bin/env python3
"""
Isolated test to prove that T20 is being excluded from continuous integration
on most steps in the Bacillus model.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController
import json

def test_model(model_path, model_name, duration=0.5):
    """Test continuous integration behavior for a model"""
    
    print(f"\n{'='*80}")
    print(f"TESTING: {model_name}")
    print(f"{'='*80}\n")
    
    # Load model
    model = DocumentModel.load_from_file(model_path)
    
    # Restore tokens
    with open(model_path, 'r') as f:
        model_data = json.load(f)
    
    for place_data in model_data.get('places', []):
        place_id = place_data['id']
        for place in model.places:
            if place.id == place_id:
                place.marking = place_data.get('marking', 0)
                break
    
    # Track which transitions fire on each step
    import shypn.engine.simulation.controller as ctrl_module
    
    step_firing_log = []
    original_step = ctrl_module.SimulationController.step
    
    def patched_step(self, time_step=None):
        # Get firing counts before
        before_counts = {t.id: t.firing_count for t in self.model.transitions if t.transition_type == 'continuous'}
        
        # Do the step
        result = original_step(self, time_step)
        
        # Get firing counts after
        after_counts = {t.id: t.firing_count for t in self.model.transitions if t.transition_type == 'continuous'}
        
        # Record which transitions fired
        fired = [tid for tid in before_counts if after_counts[tid] > before_counts[tid]]
        step_firing_log.append({
            'time': self.time,
            'fired': fired,
            'all_continuous': list(before_counts.keys())
        })
        
        return result
    
    ctrl_module.SimulationController.step = patched_step
    
    # Run simulation
    controller = SimulationController(model)
    
    step_count = 0
    while controller.time < duration:
        controller.step()
        step_count += 1
    
    # Restore original
    ctrl_module.SimulationController.step = original_step
    
    # Analyze results
    print(f"Total steps: {step_count}")
    print(f"Continuous transitions: {len(step_firing_log[0]['all_continuous'])}")
    
    # Count firing frequency for each transition
    firing_freq = {}
    for trans_id in step_firing_log[0]['all_continuous']:
        fired_count = sum(1 for step in step_firing_log if trans_id in step['fired'])
        firing_freq[trans_id] = (fired_count, step_count, fired_count / step_count * 100)
    
    # Sort by firing frequency
    sorted_freq = sorted(firing_freq.items(), key=lambda x: x[1][2], reverse=True)
    
    print(f"\n{'Transition ID':<20} {'Fired Steps':<15} {'Total Steps':<15} {'Fire %':<10}")
    print("-"*70)
    for trans_id, (fired, total, pct) in sorted_freq:
        # Get transition name
        trans_name = trans_id
        for trans in model.transitions:
            if trans.id == trans_id:
                trans_name = trans.label or trans.name or trans_id
                break
        
        status = "✓" if pct > 90 else "⚠️" if pct > 50 else "🔴"
        print(f"{trans_name:<20} {fired:<15} {total:<15} {pct:>6.1f}%  {status}")
    
    # Check for SOURCE transitions with low firing rate
    print("\n" + "="*80)
    print("SOURCE TRANSITIONS ANALYSIS:")
    print("-"*80)
    
    source_transitions = [t for t in model.transitions if getattr(t, 'is_source', False)]
    if source_transitions:
        for trans in source_transitions:
            if trans.id in firing_freq:
                fired, total, pct = firing_freq[trans.id]
                trans_name = trans.label or trans.name or trans.id
                
                if pct < 90:
                    print(f"🔴 {trans_name} (SOURCE): Only fired on {pct:.1f}% of steps!")
                    print(f"   Expected: 100% (should fire every step)")
                    print(f"   Actual: {fired}/{total} steps")
                    
                    # Check final firing count
                    expected_firings = 2.273 * duration
                    actual_firings = trans.firing_count
                    print(f"   Expected firings ({duration}s): {expected_firings:.3f}")
                    print(f"   Actual firings: {actual_firings:.3f}")
                    print(f"   Ratio: {actual_firings / expected_firings:.1%}")
                else:
                    print(f"✓ {trans_name} (SOURCE): Fired on {pct:.1f}% of steps")
    else:
        print("No SOURCE transitions found")
    
    return firing_freq, step_count


if __name__ == '__main__':
    print("\n" + "="*80)
    print("ISOLATED TEST: Continuous Integration Skipping")
    print("="*80)
    print("\nHypothesis: T20 in Bacillus model is being excluded from continuous")
    print("integration on most steps, causing reduced firing rate.\n")
    
    # Test 1: Bacillus complex model
    bacillus_freq, bacillus_steps = test_model(
        'bacillus_sporulation_normal.shy',
        'Bacillus Complex Model',
        duration=0.5
    )
    
    # Test 2: Simple source transition test model
    simple_freq, simple_steps = test_model(
        'test_arc_source_transition.shy',
        'Simple Source Transition Test',
        duration=0.5
    )
    
    # Compare results
    print("\n" + "="*80)
    print("COMPARISON & CONCLUSION")
    print("="*80)
    
    # Find T20 in Bacillus
    t20_found = False
    for trans_id, (fired, total, pct) in bacillus_freq.items():
        if 'ATP_regen' in trans_id or trans_id == 'T20':
            t20_found = True
            print(f"\nBacillus T20 (ATP regeneration):")
            print(f"  Fired on {fired}/{total} steps = {pct:.1f}%")
            
            if pct < 50:
                print(f"  🔴 HYPOTHESIS CONFIRMED!")
                print(f"     T20 is being SKIPPED on {100-pct:.1f}% of steps")
                print(f"     This explains the 50% rate reduction observed.")
    
    if not t20_found:
        print("\n⚠️  Could not identify T20 in Bacillus model")
    
    # Check simple model
    print(f"\nSimple test model (source transition):")
    for trans_id, (fired, total, pct) in simple_freq.items():
        print(f"  {trans_id}: Fired on {fired}/{total} steps = {pct:.1f}%")
        
        if pct >= 90:
            print(f"  ✓ Source transition fires on EVERY step (as expected)")
        else:
            print(f"  🔴 Source transition also being skipped!")
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("-"*80)
    print("1. Investigate _resolve_continuous_conflicts() in controller.py")
    print("2. Check if conflict resolution is incorrectly excluding T20")
    print("3. Determine why T20 is treated differently than test model transition")
    print("="*80 + "\n")
