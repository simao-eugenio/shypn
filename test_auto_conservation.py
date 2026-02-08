#!/usr/bin/env python3
"""
Test auto-detection of conservation groups.
Verifies that conservation enforcement is enabled by default.
"""
import json
import sys
from pathlib import Path

# Fix GTK version conflict
import gi
gi.require_version('Gtk', '3.0')

sys.path.insert(0, 'src')

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.engine.simulation.controller import SimulationController

def test_auto_conservation():
    """Test that auto-conservation is enabled by default."""
    print("=" * 80)
    print("Testing Auto-Conservation Detection (Enabled by Default)")
    print("=" * 80)
    
    # Load existing test model
    model_path = Path('workspace/projects/My_Project/energy_test/atp_cycle_all_normal_adaptive.shy')
    print(f"\nLoading model: {model_path}")
    
    # Load model JSON
    with open(model_path) as f:
        model_data = json.load(f)
    
    # Create model canvas manager
    model = ModelCanvasManager()
    
    # Load places
    places = []
    for p_data in model_data.get('places', []):
        place = Place.from_dict(p_data)
        places.append(place)
    places_dict = {p.id: p for p in places}
    
    # Load transitions
    transitions = []
    for t_data in model_data.get('transitions', []):
        trans = Transition.from_dict(t_data)
        transitions.append(trans)
    transitions_dict = {t.id: t for t in transitions}
    
    # Load arcs
    arcs = []
    for a_data in model_data['arcs']:
        arc = Arc.from_dict(a_data, places_dict, transitions_dict)
        arcs.append(arc)
    
    # Load objects
    model.load_objects(places=places, transitions=transitions, arcs=arcs)
    
    initial_total = sum(p.tokens for p in model.places)
    print(f"Model: {len(model.places)} places, {len(model.transitions)} transitions")
    print(f"Initial total tokens: {initial_total:.3f}")
    
    # Create controller (conservation should be auto-enabled)
    controller = SimulationController(model, verbose=False)
    
    print(f"\nAuto-conservation enabled: {controller.auto_conservation_enabled}")
    print(f"Conservation groups (before run): {len(controller.conservation_enforcer.conservation_groups)}")
    
    # Configure simulation - NOTE: NOT manually configuring conservation!
    controller.settings.duration = 100.0
    controller.settings.dt = 0.01
    
    # Run simulation (should trigger auto-detection in run() method)
    print("\nRunning simulation (100s) WITHOUT manual conservation configuration...")
    print("(Auto-detection should configure it automatically)")
    
    step = 0
    while controller.time < controller.settings.duration:
        # Call step() the first time - this triggers run() internally on first call
        if step == 0:
            # First step: Check if auto-detection configured groups
            pass
        
        if not controller.step():
            break
        step += 1
        
        # Check after first step if groups were auto-detected
        if step == 1:
            print(f"\nAfter first step:")
            print(f"  Conservation groups configured: {len(controller.conservation_enforcer.conservation_groups)}")
            if controller.conservation_enforcer.conservation_groups:
                for name, group in controller.conservation_enforcer.conservation_groups.items():
                    print(f"    - {name}: {len(group.place_ids)} places, expected={group.expected_total:.3f}")
        
        if step > 12000:  # Safety limit
            break
    
    print(f"\nCompleted {step} steps in {controller.time:.3f}s")
    
    # Check results
    final_total = sum(p.tokens for p in model.places)
    error = abs(final_total - initial_total)
    error_percent = (error / initial_total * 100) if initial_total > 0 else 0
    
    print(f"\nFinal total tokens: {final_total:.6f}")
    print(f"Error: {error:.6f} ({error_percent:.4f}%)")
    
    # Get statistics
    stats = controller.conservation_enforcer.get_statistics()
    print(f"\nConservation statistics:")
    print(f"  Total corrections: {stats['total_corrections']}")
    print(f"  Max violation observed: {stats['max_violation_observed']:.6f}")
    print(f"  Number of groups: {stats['num_groups']}")
    
    # Test result
    if len(controller.conservation_enforcer.conservation_groups) ==  0:
        print(f"\n❌ FAIL: No conservation groups were auto-detected!")
        return False
    elif error_percent < 0.01:
        print(f"\n✅ PASS: Auto-detection worked and conservation maintained (error < 0.01%)")
        return True
    else:
        print(f"\n❌ FAIL: Conservation violated (error = {error_percent:.4f}%)")
        return False

if __name__ == '__main__':
    success = test_auto_conservation()
    sys.exit(0 if success else 1)
