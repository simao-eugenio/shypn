#!/usr/bin/env python3
"""Run energy test models with conservation enforcement.

Tests conservation enforcement across different arc types and volume scenarios.
"""

import json
import logging
import sys
from pathlib import Path

# Fix GTK version conflict
import gi
gi.require_version('Gtk', '3.0')

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Suppress verbose output
    format='%(levelname)s:%(name)s:%(message)s'
)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.engine.simulation.controller import SimulationController


def run_test_model(model_path: Path) -> dict:
    """Run a single test model with conservation enforcement."""
    
    # Load model JSON
    with open(model_path) as f:
        model_data = json.load(f)
    
    # Create model canvas manager manually
    canvas_manager = ModelCanvasManager()
    
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
    
    # Load objects into canvas manager
    canvas_manager.load_objects(places=places, transitions=transitions, arcs=arcs)
    
    # Create controller
    controller = SimulationController(canvas_manager, verbose=False)
    
    # Configure simulation (10 seconds)
    controller.settings.duration = 10.0
    controller.settings.duration_unit = 's'
    controller.settings.dt = 0.01
    
    # Configure conservation enforcement
    controller.configure_conservation(
        name='energy_cycle',
        place_ids=['P1', 'P2', 'P3'],  # Use actual place IDs, not names
        expected_total=15.0
    )
    
    # Record initial state
    initial_total = sum(p.tokens for p in places)
    
    # Run simulation
    step_count = 0
    while controller.time < controller.settings.duration:
        success = controller.step()
        step_count += 1
        if not success:
            break
    
    # Check final state
    final_total = sum(p.tokens for p in places)
    
    # Get statistics
    t1_count = transitions[0].firing_count
    t2_count = transitions[1].firing_count
    stats = controller.conservation_enforcer.get_statistics()
    
    # Calculate error
    error = abs(final_total - initial_total)
    error_percent = (error / initial_total * 100) if initial_total > 0 else 0
    
    return {
        'model': model_path.stem,
        'initial_total': initial_total,
        'final_total': final_total,
        'error': error,
        'error_percent': error_percent,
        'steps': step_count,
        't1_firings': t1_count,
        't2_firings': t2_count,
        'imbalance': abs(t1_count - t2_count),
        'corrections': stats['total_corrections'],
        'max_violation': stats['max_violation_observed'],
        'passed': error_percent < 0.01  # 0.01% tolerance
    }


def main():
    test_dir = Path(__file__).parent / 'workspace' / 'projects' / 'My_Project' / 'energy_test'
    
    # Select representative test models
    test_models = [
        'atp_cycle_all_normal_adaptive.shy',
        'atp_cycle_all_normal_continuous.shy',
        'atp_cycle_all_normal_mixed.shy',
        'atp_cycle_signal_flow_output_adaptive.shy',
        'atp_cycle_signal_flow_output_continuous.shy',
        'atp_cycle_signal_flow_output_mixed.shy',
        'atp_cycle_signal_flow_input_adaptive.shy',
        'atp_cycle_signal_flow_input_continuous.shy',
        'atp_cycle_signal_flow_input_mixed.shy',
        'atp_cycle_signal_flow_both_adaptive.shy',
        'atp_cycle_signal_flow_both_continuous.shy',
        'atp_cycle_signal_flow_both_mixed.shy',
    ]
    
    print("=" * 100)
    print("  CONSERVATION ENFORCEMENT TEST SUITE")
    print("=" * 100)
    print()
    print(f"Testing {len(test_models)} model variants with conservation enforcement enabled")
    print()
    
    results = []
    for model_name in test_models:
        model_path = test_dir / model_name
        if not model_path.exists():
            print(f"⚠️  SKIP: {model_name} (not found)")
            continue
        
        print(f"Running: {model_name:50s} ... ", end='', flush=True)
        try:
            result = run_test_model(model_path)
            results.append(result)
            
            if result['passed']:
                print(f"✅ PASS (error: {result['error_percent']:.4f}%)")
            else:
                print(f"❌ FAIL (error: {result['error_percent']:.4f}%)")
        except Exception as e:
            print(f"💥 ERROR: {str(e)[:50]}")
    
    print()
    print("=" * 100)
    print("  DETAILED RESULTS")
    print("=" * 100)
    print()
    
    # Table header
    print(f"{'Model':<50s} {'Error %':>10s} {'Imbal':>8s} {'Corr':>8s} {'Status':>8s}")
    print("-" * 100)
    
    for r in results:
        status = "✅ PASS" if r['passed'] else "❌ FAIL"
        print(f"{r['model']:<50s} {r['error_percent']:>9.4f}% {r['imbalance']:>8.0f} {r['corrections']:>8d} {status:>8s}")
    
    print()
    print("=" * 100)
    print(f"Summary: {sum(1 for r in results if r['passed'])}/{len(results)} tests passed")
    print("=" * 100)
    
    # Exit with appropriate code
    all_passed = all(r['passed'] for r in results)
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
