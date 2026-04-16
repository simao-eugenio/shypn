#!/usr/bin/env python3
"""
Test if stochastic transitions interfere with continuous transition firing.

This test creates a model with both continuous and stochastic transitions
to determine if the scheduler/simulator preferentially schedules one type
over another, causing continuous transitions to be skipped.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController
import json

def test_mixed_transitions():
    """Test continuous firing with mixed transition types"""
    
    print("="*80)
    print("TEST: Mixed Continuous and Stochastic Transitions")
    print("="*80)
    print("\nModel Structure:")
    print("  - T_Continuous: continuous transition (rate = 2.5*P/(10+P) ≈ 2.27)")
    print("  - T_Stochastic: stochastic transition (rate = 5.0)")
    print()
    
    # Load model
    model = DocumentModel.load_from_file('test_mixed_transitions.shy')
    
    # Restore tokens
    with open('test_mixed_transitions.shy', 'r') as f:
        model_data = json.load(f)
    
    for place_data in model_data.get('places', []):
        place_id = place_data['id']
        for place in model.places:
            if place.id == place_id:
                place.marking = place_data.get('marking', 0)
                break
    
    # Patch to track firing by step and type
    import shypn.engine.simulation.controller as ctrl_module
    
    firing_log = []
    original_step = ctrl_module.SimulationController.step
    
    def patched_step(self, time_step=None):
        # Track what fires in this step
        step_info = {
            'time': self.time,
            'continuous_fired': [],
            'stochastic_fired': [],
            'before_counts': {}
        }
        
        # Get counts before
        for trans in self.model.transitions:
            step_info['before_counts'][trans.id] = trans.firing_count
        
        # Do the step
        result = original_step(self, time_step)
        
        # Check what fired
        for trans in self.model.transitions:
            if trans.firing_count > step_info['before_counts'][trans.id]:
                if trans.transition_type == 'continuous':
                    step_info['continuous_fired'].append(trans.id)
                elif trans.transition_type == 'stochastic':
                    step_info['stochastic_fired'].append(trans.id)
        
        firing_log.append(step_info)
        return result
    
    ctrl_module.SimulationController.step = patched_step
    
    # Run simulation
    controller = SimulationController(model)
    
    duration = 1.0
    step_count = 0
    
    print(f"Running {duration}s simulation...\n")
    while controller.time < duration:
        controller.step()
        step_count += 1
    
    # Restore original
    ctrl_module.SimulationController.step = original_step
    
    # Analyze results
    print(f"Total steps: {step_count}")
    print(f"Duration: {duration}s")
    print()
    
    # Count firing patterns
    continuous_only = 0
    stochastic_only = 0
    both = 0
    neither = 0
    
    for step in firing_log:
        has_cont = len(step['continuous_fired']) > 0
        has_stoch = len(step['stochastic_fired']) > 0
        
        if has_cont and has_stoch:
            both += 1
        elif has_cont:
            continuous_only += 1
        elif has_stoch:
            stochastic_only += 1
        else:
            neither += 1
    
    print("FIRING PATTERNS PER STEP:")
    print("-"*80)
    print(f"Both types fired:         {both:>4} steps ({both/step_count*100:>5.1f}%)")
    print(f"Continuous only:          {continuous_only:>4} steps ({continuous_only/step_count*100:>5.1f}%)")
    print(f"Stochastic only:          {stochastic_only:>4} steps ({stochastic_only/step_count*100:>5.1f}%)")
    print(f"Neither fired:            {neither:>4} steps ({neither/step_count*100:>5.1f}%)")
    print()
    
    # Get transition statistics
    t_cont = None
    t_stoch = None
    for trans in model.transitions:
        if trans.id == 'T1':  # Continuous
            t_cont = trans
        elif trans.id == 'T2':  # Stochastic
            t_stoch = trans
    
    # Count how many steps each fired
    cont_fired_steps = sum(1 for step in firing_log if 'T1' in step['continuous_fired'])
    stoch_fired_steps = sum(1 for step in firing_log if 'T2' in step['stochastic_fired'])
    
    print("TRANSITION STATISTICS:")
    print("-"*80)
    print(f"\nContinuous Transition (T_Continuous):")
    print(f"  Fired on steps:       {cont_fired_steps}/{step_count} ({cont_fired_steps/step_count*100:.1f}%)")
    print(f"  Total firing count:   {t_cont.firing_count:.3f}")
    print(f"  Expected (2.27*{duration}s): {2.273*duration:.3f}")
    print(f"  Ratio:                {t_cont.firing_count/(2.273*duration):.1%}")
    
    if cont_fired_steps < step_count * 0.9:
        print(f"  🔴 CONTINUOUS SKIPPED on {step_count - cont_fired_steps} steps!")
    else:
        print(f"  ✓ Continuous fires on nearly every step")
    
    print(f"\nStochastic Transition (T_Stochastic):")
    print(f"  Fired on steps:       {stoch_fired_steps}/{step_count} ({stoch_fired_steps/step_count*100:.1f}%)")
    print(f"  Total firings:        {int(t_stoch.firing_count)}")
    print(f"  Expected (rate=5.0):  ~5 firings in {duration}s")
    print(f"  Ratio:                {t_stoch.firing_count/5.0:.1%}")
    
    # Show first 20 steps in detail
    print(f"\n\nFIRST 20 STEPS DETAIL:")
    print("-"*80)
    print(f"{'Step':<6} {'Time':<10} {'Continuous':<15} {'Stochastic':<15}")
    print("-"*80)
    
    for i, step in enumerate(firing_log[:20]):
        cont_status = "FIRED" if step['continuous_fired'] else "---"
        stoch_status = "FIRED" if step['stochastic_fired'] else "---"
        print(f"{i+1:<6} {step['time']:<10.6f} {cont_status:<15} {stoch_status:<15}")
    
    if len(firing_log) > 20:
        print(f"... ({len(firing_log)-20} more steps)")
    
    # Conclusion
    print("\n" + "="*80)
    print("CONCLUSION:")
    print("="*80)
    
    if cont_fired_steps < step_count * 0.9:
        print(f"🔴 INTERFERENCE DETECTED!")
        print(f"   Continuous transition is being SKIPPED on {step_count - cont_fired_steps}/{step_count} steps")
        print(f"   Even though it should fire on EVERY step")
        
        if stochastic_only > 0:
            print(f"\n   Stochastic-only steps: {stochastic_only}")
            print(f"   This suggests stochastic transitions are blocking continuous execution")
        
        if both > continuous_only:
            print(f"\n   Both types fire together more often ({both}) than continuous alone ({continuous_only})")
            print(f"   This suggests alternating/scheduling interference")
    else:
        print(f"✓ NO INTERFERENCE")
        print(f"  Continuous transition fires on {cont_fired_steps/step_count*100:.1f}% of steps (as expected)")
        print(f"  Stochastic transitions do not interfere with continuous execution")
    
    return {
        'step_count': step_count,
        'cont_fired_steps': cont_fired_steps,
        'stoch_fired_steps': stoch_fired_steps,
        'both': both,
        'continuous_only': continuous_only,
        'stochastic_only': stochastic_only,
        'neither': neither,
        'cont_firing_count': t_cont.firing_count,
        'stoch_firing_count': t_stoch.firing_count
    }


def compare_with_continuous_only():
    """Run same test but with only continuous transition"""
    
    print("\n\n" + "="*80)
    print("CONTROL TEST: Continuous Transition Only")
    print("="*80)
    
    # Create a model with only continuous transition
    model_data = {
        "version": "2.0",
        "metadata": {},
        "view_state": {"zoom": 1.0, "pan_x": 0.0, "pan_y": 0.0},
        "places": [
            {
                "id": "P1",
                "name": "TestPlace",
                "label": "TestPlace",
                "x": 100.0,
                "y": 100.0,
                "radius": 30.0,
                "marking": 100.0,
                "initial_marking": 100.0,
                "fill_color": [0.8, 0.9, 1.0, 1.0],
                "border_color": [0.0, 0.0, 0.0, 1.0]
            },
            {
                "id": "P2",
                "name": "ResultPlace",
                "label": "ResultPlace",
                "x": 300.0,
                "y": 100.0,
                "radius": 30.0,
                "marking": 0.0,
                "initial_marking": 0.0,
                "fill_color": [0.8, 1.0, 0.8, 1.0],
                "border_color": [0.0, 0.0, 0.0, 1.0]
            }
        ],
        "transitions": [
            {
                "id": "T1",
                "name": "T1",
                "label": "ContinuousOnly",
                "x": 200.0,
                "y": 100.0,
                "width": 40.0,
                "height": 10.0,
                "horizontal": True,
                "enabled": True,
                "fill_color": [0.2, 0.6, 1.0, 1.0],
                "border_color": [0.0, 0.0, 0.0, 1.0],
                "border_width": 2.0,
                "transition_type": "continuous",
                "priority": 0,
                "firing_policy": "race",
                "is_source": False,
                "is_sink": False,
                "rate_function": "2.5 * TestPlace / (10 + TestPlace)"
            }
        ],
        "arcs": [
            {
                "id": "A1",
                "source_id": "P1",
                "target_id": "T1",
                "weight": 1.0,
                "arc_type": "normal",
                "points": []
            },
            {
                "id": "A2",
                "source_id": "T1",
                "target_id": "P2",
                "weight": 1.0,
                "arc_type": "normal",
                "points": []
            }
        ],
        "modules": []
    }
    
    # Save temporary model
    with open('test_continuous_only_temp.shy', 'w') as f:
        json.dump(model_data, f)
    
    # Load and run
    model = DocumentModel.load_from_file('test_continuous_only_temp.shy')
    
    for place_data in model_data['places']:
        for place in model.places:
            if place.id == place_data['id']:
                place.marking = place_data['marking']
                break
    
    # Track firing
    import shypn.engine.simulation.controller as ctrl_module
    
    step_count = 0
    fired_count = 0
    original_step = ctrl_module.SimulationController.step
    
    def patched_step(self, time_step=None):
        nonlocal step_count, fired_count
        step_count += 1
        
        t1 = self.model.transitions[0]
        before = t1.firing_count
        
        result = original_step(self, time_step)
        
        if t1.firing_count > before:
            fired_count += 1
        
        return result
    
    ctrl_module.SimulationController.step = patched_step
    
    controller = SimulationController(model)
    
    duration = 1.0
    while controller.time < duration:
        controller.step()
    
    ctrl_module.SimulationController.step = original_step
    
    t1 = model.transitions[0]
    
    print(f"\nContinuous-only model:")
    print(f"  Total steps:          {step_count}")
    print(f"  Fired on steps:       {fired_count}/{step_count} ({fired_count/step_count*100:.1f}%)")
    print(f"  Total firing count:   {t1.firing_count:.3f}")
    print(f"  Expected (2.27*1s):   {2.273*duration:.3f}")
    print(f"  Ratio:                {t1.firing_count/(2.273*duration):.1%}")
    
    if fired_count == step_count:
        print(f"  ✓ Fires on EVERY step (as expected)")
    else:
        print(f"  🔴 Skipped on {step_count - fired_count} steps!")
    
    # Cleanup
    import os
    try:
        os.remove('test_continuous_only_temp.shy')
    except:
        pass
    
    return {
        'step_count': step_count,
        'fired_count': fired_count,
        'firing_count': t1.firing_count
    }


if __name__ == '__main__':
    # Test 1: Mixed transitions
    mixed_results = test_mixed_transitions()
    
    # Test 2: Continuous only (control)
    control_results = compare_with_continuous_only()
    
    # Final comparison
    print("\n\n" + "="*80)
    print("FINAL ANALYSIS: Scheduler Interference")
    print("="*80)
    
    mixed_fire_rate = mixed_results['cont_fired_steps'] / mixed_results['step_count']
    control_fire_rate = control_results['fired_count'] / control_results['step_count']
    
    print(f"\nContinuous transition firing rate:")
    print(f"  With stochastic transitions:    {mixed_fire_rate*100:.1f}%")
    print(f"  Without stochastic (control):   {control_fire_rate*100:.1f}%")
    print(f"  Difference:                     {(mixed_fire_rate - control_fire_rate)*100:+.1f}%")
    
    if abs(mixed_fire_rate - control_fire_rate) > 0.1:
        print(f"\n🔴 SCHEDULER INTERFERENCE CONFIRMED!")
        print(f"   Stochastic transitions are interfering with continuous execution")
        print(f"   Continuous transitions are being skipped when stochastic are present")
    else:
        print(f"\n✓ NO SCHEDULER INTERFERENCE")
        print(f"  Continuous transitions fire consistently regardless of stochastic presence")
    
    print("\n" + "="*80)
