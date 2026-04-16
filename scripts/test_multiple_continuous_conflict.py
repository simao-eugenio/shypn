#!/usr/bin/env python3
"""
Test if multiple continuous transitions cause conflict resolution
to skip some transitions on certain steps.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController
import json

def create_multi_continuous_model(num_transitions=4):
    """Create a model with multiple independent continuous transitions"""
    
    places = []
    transitions = []
    arcs = []
    
    for i in range(num_transitions):
        # Input place
        places.append({
            "id": f"P{i*2+1}",
            "name": f"Input{i+1}",
            "label": f"Input{i+1}",
            "x": 100.0,
            "y": 100.0 + i*100,
            "radius": 30.0,
            "marking": 100.0,
            "initial_marking": 100.0,
            "fill_color": [0.8, 0.9, 1.0, 1.0],
            "border_color": [0.0, 0.0, 0.0, 1.0]
        })
        
        # Output place
        places.append({
            "id": f"P{i*2+2}",
            "name": f"Output{i+1}",
            "label": f"Output{i+1}",
            "x": 300.0,
            "y": 100.0 + i*100,
            "radius": 30.0,
            "marking": 0.0,
            "initial_marking": 0.0,
            "fill_color": [0.8, 1.0, 0.8, 1.0],
            "border_color": [0.0, 0.0, 0.0, 1.0]
        })
        
        # Transition
        transitions.append({
            "id": f"T{i+1}",
            "name": f"T{i+1}",
            "label": f"Continuous{i+1}",
            "x": 200.0,
            "y": 100.0 + i*100,
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
            "rate_function": f"2.5 * Input{i+1} / (10 + Input{i+1})"
        })
        
        # Input arc
        arcs.append({
            "id": f"A{i*2+1}",
            "source_id": f"P{i*2+1}",
            "target_id": f"T{i+1}",
            "weight": 1.0,
            "arc_type": "normal",
            "points": []
        })
        
        # Output arc
        arcs.append({
            "id": f"A{i*2+2}",
            "source_id": f"T{i+1}",
            "target_id": f"P{i*2+2}",
            "weight": 1.0,
            "arc_type": "normal",
            "points": []
        })
    
    model_data = {
        "version": "2.0",
        "metadata": {},
        "view_state": {"zoom": 1.0, "pan_x": 0.0, "pan_y": 0.0},
        "places": places,
        "transitions": transitions,
        "arcs": arcs,
        "modules": []
    }
    
    return model_data


def test_multiple_continuous(num_transitions):
    """Test firing behavior with multiple continuous transitions"""
    
    print(f"\n{'='*80}")
    print(f"TEST: {num_transitions} Independent Continuous Transitions")
    print(f"{'='*80}\n")
    
    # Create model
    model_data = create_multi_continuous_model(num_transitions)
    
    # Save temporary model
    temp_file = f'test_multi_cont_{num_transitions}.shy'
    with open(temp_file, 'w') as f:
        json.dump(model_data, f)
    
    # Load model
    model = DocumentModel.load_from_file(temp_file)
    
    # Restore tokens
    for place_data in model_data['places']:
        for place in model.places:
            if place.id == place_data['id']:
                place.marking = place_data['marking']
                break
    
    # Track firing by transition
    import shypn.engine.simulation.controller as ctrl_module
    
    firing_log = {}  # trans_id -> list of (step, time) when it fired
    step_count = [0]
    
    original_step = ctrl_module.SimulationController.step
    
    def patched_step(self, time_step=None):
        step_count[0] += 1
        
        # Track before counts
        before = {t.id: t.firing_count for t in self.model.transitions}
        
        # Do step
        result = original_step(self, time_step)
        
        # Check who fired
        for trans in self.model.transitions:
            if trans.firing_count > before[trans.id]:
                if trans.id not in firing_log:
                    firing_log[trans.id] = []
                firing_log[trans.id].append((step_count[0], self.time))
        
        return result
    
    ctrl_module.SimulationController.step = patched_step
    
    # Run simulation
    controller = SimulationController(model)
    
    duration = 0.5
    while controller.time < duration:
        controller.step()
    
    # Restore
    ctrl_module.SimulationController.step = original_step
    
    # Analyze
    total_steps = step_count[0]
    print(f"Total steps: {total_steps}")
    print(f"Duration: {duration}s")
    print()
    
    print(f"{'Transition':<15} {'Fired Steps':<15} {'Fire %':<10} {'Firing Count':<15} {'Expected':<12} {'Ratio'}")
    print("-"*90)
    
    all_fire_every_step = True
    
    for i in range(1, num_transitions + 1):
        trans_id = f"T{i}"
        trans = None
        for t in model.transitions:
            if t.id == trans_id:
                trans = t
                break
        
        fired_steps = len(firing_log.get(trans_id, []))
        fire_pct = (fired_steps / total_steps * 100) if total_steps > 0 else 0
        firing_count = trans.firing_count if trans else 0
        expected = 2.273 * duration
        ratio = (firing_count / expected * 100) if expected > 0 else 0
        
        status = "✓" if fire_pct > 90 else "⚠️" if fire_pct > 50 else "🔴"
        
        print(f"{trans_id:<15} {fired_steps:>6}/{total_steps:<7} {fire_pct:>6.1f}% {status}  {firing_count:>12.3f}   {expected:>10.3f}   {ratio:>6.1f}%")
        
        if fire_pct < 90:
            all_fire_every_step = False
    
    print()
    
    # Show which transitions fired together
    print("CONCURRENT FIRING PATTERNS:")
    print("-"*80)
    
    # For each step, show which transitions fired
    step_patterns = {}
    for step in range(1, total_steps + 1):
        fired = []
        for trans_id, events in firing_log.items():
            if any(s == step for s, _ in events):
                fired.append(trans_id)
        
        pattern = tuple(sorted(fired))
        if pattern not in step_patterns:
            step_patterns[pattern] = 0
        step_patterns[pattern] += 1
    
    for pattern, count in sorted(step_patterns.items(), key=lambda x: x[1], reverse=True):
        if not pattern:
            pattern_str = "(none)"
        else:
            pattern_str = ", ".join(pattern)
        print(f"  {pattern_str:<40} {count:>3} steps ({count/total_steps*100:>5.1f}%)")
    
    print("\n" + "="*80)
    
    if all_fire_every_step:
        print("✓ ALL transitions fire on EVERY step")
    else:
        print("🔴 Some transitions are SKIPPED on certain steps!")
        print("   This indicates conflict resolution is alternating/prioritizing transitions")
    
    # Cleanup
    try:
        os.remove(temp_file)
    except:
        pass
    
    return {
        'total_steps': total_steps,
        'num_transitions': num_transitions,
        'all_fire_every_step': all_fire_every_step,
        'firing_log': firing_log
    }


if __name__ == '__main__':
    print("\n" + "="*80)
    print("ISOLATED TEST: Multiple Continuous Transitions Conflict")
    print("="*80)
    print("\nHypothesis: When multiple continuous transitions exist,")
    print("_resolve_continuous_conflicts() alternates between them,")
    print("causing each to fire on only a fraction of steps.\n")
    
    # Test with increasing numbers of continuous transitions
    for num in [2, 4]:
        results = test_multiple_continuous(num)
        
        if not results['all_fire_every_step']:
            print(f"\n🔴 With {num} transitions: CONFLICT DETECTED")
            print(f"   Not all transitions fire on every step")
            print(f"   This explains the reduced firing rate in Bacillus model!")
            break
    else:
        print(f"\n✓ No conflicts detected")
        print(f"  All continuous transitions fire on every step")
    
    print("\n" + "="*80)
    print("CONCLUSION:")
    print("-"*80)
    print("The Bacillus model has 4 continuous SOURCE transitions:")
    print("  - Source_ATP_regen (T20)")
    print("  - Source_GTP_regen")
    print("  - Source_cell_density")
    print("  - Source_nutrient_depletion")
    print()
    print("If _resolve_continuous_conflicts() is alternating between them,")
    print("this would cause each to fire on only ~25% of steps (for 4 transitions).")
    print("This matches the observed 50-60% rate reduction.")
    print("="*80 + "\n")
