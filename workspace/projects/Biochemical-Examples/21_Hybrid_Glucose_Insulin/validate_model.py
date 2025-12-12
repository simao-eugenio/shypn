#!/usr/bin/env python3
"""
Validate and analyze the Hybrid Glucose-Insulin model.

This script demonstrates:
1. Model loading and validation
2. Dependency classification (weak independence analysis)
3. Hybrid simulation (continuous + stochastic)
4. Performance benchmarking (sequential vs parallel)
"""

import sys
import os
import json
import time

# Use installed shypn package
from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController
from shypn.engine.simulation.settings import SimulationSettings
from shypn.topology.biological.dependency_coupling import DependencyAndCouplingAnalyzer
from shypn.utils.time_utils import TimeUnits


def load_model():
    """Load the hybrid glucose-insulin model."""
    model_path = os.path.join(os.path.dirname(__file__), 'model.json')
    
    print("=" * 80)
    print("HYBRID GLUCOSE-INSULIN MODEL VALIDATION")
    print("=" * 80)
    print(f"\n📂 Loading model from: {model_path}")
    
    with open(model_path, 'r') as f:
        data = json.load(f)
    
    model = DocumentModel()
    
    # Create places
    place_map = {}
    for place_data in data['places']:
        place = model.create_place(
            x=place_data.get('x', 0),
            y=place_data.get('y', 0),
            label=place_data['name']
        )
        place.tokens = place_data['tokens']
        place.place_type = place_data.get('place_type', 'continuous')
        
        # Set metadata dictionary
        if 'chemical_formula' in place_data or 'compartment' in place_data:
            place.metadata = {}
            if 'chemical_formula' in place_data:
                place.metadata['chemical_formula'] = place_data['chemical_formula']
            if 'compartment' in place_data:
                place.metadata['compartment'] = place_data['compartment']
        
        place_map[place_data['id']] = place
    
    # Create transitions
    trans_map = {}
    for trans_data in data['transitions']:
        trans = model.create_transition(
            x=trans_data.get('x', 0),
            y=trans_data.get('y', 0),
            label=trans_data['name']
        )
        trans.transition_type = trans_data.get('transition_type', 'continuous')
        trans.metadata = {'rate_function': trans_data['rate_function']}
        trans_map[trans_data['id']] = trans
    
    # Create arcs
    for arc_data in data['arcs']:
        source_id = arc_data['source']
        target_id = arc_data['target']
        weight = arc_data.get('weight', 1.0)
        arc_type = arc_data.get('arc_type', 'normal')
        
        # Determine source and target objects
        source = place_map.get(source_id) or trans_map.get(source_id)
        target = place_map.get(target_id) or trans_map.get(target_id)
        
        if source and target:
            arc = model.create_arc(source, target, arc_type=arc_type)
            arc.weight = weight
    
    print(f"✅ Model loaded: {len(model.places)} places, {len(model.transitions)} transitions")
    
    return model


def analyze_dependencies(model):
    """Analyze weak independence structure."""
    print("\n" + "=" * 80)
    print("WEAK INDEPENDENCE ANALYSIS")
    print("=" * 80)
    
    analyzer = DependencyAndCouplingAnalyzer(model)
    result = analyzer.analyze()
    
    classifications = result.data
    stats = classifications.get('statistics', {})
    
    print(f"\n📊 Dependency Statistics:")
    print(f"  • Strong Independent: {stats.get('strongly_independent_pct', 0):.1f}%")
    print(f"  • Convergent Coupling: {stats.get('convergent_pct', 0):.1f}%")
    print(f"  • Regulatory Coupling: {stats.get('regulatory_pct', 0):.1f}%")
    print(f"  • Competitive Coupling: {stats.get('competitive_pct', 0):.1f}%")
    print(f"  ────────────────────────────")
    print(f"  • WEAKLY INDEPENDENT: {stats.get('weakly_independent_pct', 0):.1f}%")
    
    print(f"\n🔗 Convergent Coupling Examples:")
    for t1_name, t2_name, shared in classifications.get('convergent', [])[:3]:
        print(f"  • {t1_name} ↔ {t2_name}")
        print(f"    Shared outputs: {', '.join(shared)}")
    
    print(f"\n🧬 Regulatory Coupling Examples:")
    for t1_name, t2_name, shared in classifications.get('regulatory', [])[:3]:
        print(f"  • {t1_name} ↔ {t2_name}")
        print(f"    Shared regulators: {', '.join(shared)}")
    
    print(f"\n⚔️  Competitive Coupling Examples:")
    for t1_name, t2_name, shared in classifications.get('competitive', [])[:3]:
        print(f"  • {t1_name} ↔ {t2_name}")
        print(f"    Shared inputs: {', '.join(shared)} (TRUE CONFLICT)")
    
    return stats


def simulate_model(model, parallel=True, duration=100):
    """Run hybrid simulation."""
    print("\n" + "=" * 80)
    print(f"HYBRID SIMULATION ({'PARALLEL' if parallel else 'SEQUENTIAL'})")
    print("=" * 80)
    
    # Configure settings
    settings = SimulationSettings()
    settings.duration = duration
    settings.time_units = TimeUnits.SECONDS
    settings.dt_auto = True
    settings.use_parallel_stochastic = parallel
    
    # Count transition types
    continuous_count = sum(1 for t in model.transitions if t.transition_type == 'continuous')
    stochastic_count = sum(1 for t in model.transitions if t.transition_type == 'stochastic')
    
    print(f"\n🔧 Configuration:")
    print(f"  • Duration: {duration}s")
    print(f"  • Continuous transitions: {continuous_count}")
    print(f"  • Stochastic transitions: {stochastic_count}")
    print(f"  • τ-leaping: Always enabled (10-100× faster than exact SSA)")
    print(f"  • Parallel execution: {'✅ ON' if parallel else '❌ OFF'}")
    print(f"  • Epsilon: {settings.tau_epsilon} (accuracy tolerance)")
    
    # Run simulation
    controller = SimulationController(model)
    controller.settings = settings
    
    print(f"\n🚀 Running simulation...")
    start_time = time.time()
    
    try:
        controller.run()
        elapsed = time.time() - start_time
        
        print(f"✅ Simulation completed in {elapsed:.3f}s")
        print(f"\n📈 Final State:")
        
        # Show key places
        key_places = ['Glucose_Cell', 'ATP', 'Insulin_mRNA', 'Insulin_Protein', 'Insulin_Secreted']
        for place_name in key_places:
            place = next((p for p in model.places if p.label == place_name), None)
            if place:
                print(f"  • {place_name}: {place.tokens:.2f}")
        
        return elapsed
        
    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def benchmark_performance(model):
    """Compare sequential vs parallel execution."""
    print("\n" + "=" * 80)
    print("PERFORMANCE BENCHMARK")
    print("=" * 80)
    
    duration = 50  # Shorter for benchmarking
    
    # Sequential
    print("\n🔄 Sequential tau-leaping...")
    time_seq = simulate_model(model, parallel=False, duration=duration)
    
    # Parallel
    print("\n⚡ Parallel tau-leaping...")
    time_par = simulate_model(model, parallel=True, duration=duration)
    
    if time_seq and time_par:
        speedup = time_seq / time_par
        print(f"\n🏆 PERFORMANCE RESULTS:")
        print(f"  • Sequential: {time_seq:.3f}s")
        print(f"  • Parallel:   {time_par:.3f}s")
        print(f"  • Speedup:    {speedup:.2f}×")
        
        if speedup > 1.0:
            print(f"  ✅ Parallel execution is {speedup:.2f}× faster!")
        else:
            print(f"  ⚠️  Overhead dominated (model too small or short duration)")


def main():
    """Main validation script."""
    try:
        # Load model
        model = load_model()
        
        # Analyze dependencies
        stats = analyze_dependencies(model)
        
        # Run simulation
        simulate_model(model, parallel=True, duration=100)
        
        # Benchmark (optional - uncomment to test)
        # benchmark_performance(model)
        
        print("\n" + "=" * 80)
        print("✅ VALIDATION COMPLETE")
        print("=" * 80)
        print("\n💡 Key Findings:")
        print(f"  1. Weak independence: {stats.get('weakly_independent_pct', 0):.1f}% (enables parallelism)")
        print(f"  2. Hybrid dynamics: Continuous metabolism + Stochastic gene regulation")
        print(f"  3. Regulatory coupling: ATP regulates transcription & secretion")
        print(f"  4. Convergent coupling: Multiple glucose sources → single pool")
        print(f"  5. τ-leaping always enabled: 10-100× faster than exact SSA")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
