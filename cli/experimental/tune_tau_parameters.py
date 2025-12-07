#!/usr/bin/env python3
"""Test different τ-leaping parameter configurations to find optimal settings."""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from _fix_imports import *
from _sbml_loader import load_sbml_model
from shypn.engine.simulation.replicate_runner import ReplicateRunner


def test_parameters(sbml_path: str, n_replicates: int = 10, duration: float = 100.0):
    """Test different parameter configurations."""
    print(f"Loading model: {sbml_path}")
    model = load_sbml_model(sbml_path)
    
    print(f"\n{'='*70}")
    print("PARAMETER TUNING EXPERIMENT")
    print(f"Model: {sbml_path.split('/')[-1]}")
    print(f"Replicates: {n_replicates}, Duration: {duration}")
    print(f"{'='*70}\n")
    
    # Baseline: Gillespie SSA
    print("Baseline: Gillespie SSA (use_tau_leaping=False)")
    runner = ReplicateRunner(model)
    start = time.time()
    runner.run_replicates(n=n_replicates, use_tau_leaping=False, duration=duration, verbose=False)
    time_baseline = time.time() - start
    print(f"  Time: {time_baseline:.3f}s ({time_baseline/n_replicates*1000:.1f}ms per replicate)\n")
    
    # Test different parameter combinations
    configs = [
        {'epsilon': 0.03, 'max_tau': 1.0, 'name': 'Default (conservative)'},
        {'epsilon': 0.05, 'max_tau': 1.0, 'name': 'Epsilon 0.05'},
        {'epsilon': 0.10, 'max_tau': 1.0, 'name': 'Epsilon 0.10'},
        {'epsilon': 0.03, 'max_tau': 5.0, 'name': 'Max tau 5.0'},
        {'epsilon': 0.03, 'max_tau': 10.0, 'name': 'Max tau 10.0'},
        {'epsilon': 0.05, 'max_tau': 5.0, 'name': 'Epsilon 0.05 + Max tau 5.0'},
        {'epsilon': 0.10, 'max_tau': 5.0, 'name': 'Epsilon 0.10 + Max tau 5.0'},
        {'epsilon': 0.10, 'max_tau': 10.0, 'name': 'Epsilon 0.10 + Max tau 10.0'},
    ]
    
    results = []
    
    for config in configs:
        print(f"Testing: {config['name']}")
        print(f"  epsilon={config['epsilon']}, max_tau={config['max_tau']}")
        
        # Note: ReplicateRunner doesn't expose epsilon/max_tau parameters yet
        # We need to modify the runner or access controller settings directly
        # For now, this shows the experimental design
        
        # This would work if epsilon parameter was exposed:
        # start = time.time()
        # runner.run_replicates(
        #     n=n_replicates,
        #     use_tau_leaping=True,
        #     epsilon=config['epsilon'],
        #     duration=duration,
        #     verbose=False
        # )
        # elapsed = time.time() - start
        
        # Placeholder - need to implement parameter passing
        print(f"  ⚠️  Parameter tuning not yet implemented in ReplicateRunner API")
        print(f"  Need to add epsilon/max_tau/critical_threshold parameters\n")
        
        # results.append({
        #     'config': config['name'],
        #     'epsilon': config['epsilon'],
        #     'max_tau': config['max_tau'],
        #     'time': elapsed,
        #     'speedup': time_baseline / elapsed
        # })
    
    print(f"\n{'='*70}")
    print("IMPLEMENTATION REQUIRED:")
    print("  1. Expose epsilon, max_tau, critical_threshold in ReplicateRunner")
    print("  2. Pass parameters to controller.settings")
    print("  3. Re-run this experiment to find optimal parameters")
    print(f"{'='*70}\n")
    
    print("HYPOTHESIS:")
    print("  Larger epsilon (0.05-0.10) should allow larger τ values")
    print("  → More firings per leap")
    print("  → Reduced overhead ratio")
    print("  → Better speedup (hopefully >1.0x)")
    
    # if results:
    #     print(f"\n{'='*70}")
    #     print("RESULTS SUMMARY:")
    #     print(f"{'='*70}")
    #     print(f"{'Configuration':<35} {'Time':>10} {'Speedup':>10}")
    #     print(f"{'-'*70}")
    #     print(f"{'Baseline (Gillespie SSA)':<35} {time_baseline:>9.3f}s {'1.00x':>10}")
    #     for r in results:
    #         print(f"{r['config']:<35} {r['time']:>9.3f}s {r['speedup']:>9.2f}x")
    #     
    #     # Find best
    #     best = max(results, key=lambda x: x['speedup'])
    #     print(f"\nBEST CONFIGURATION: {best['config']}")
    #     print(f"  Speedup: {best['speedup']:.2f}x")
    #     print(f"  epsilon={best['epsilon']}, max_tau={best['max_tau']}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Test τ-leaping parameter configurations'
    )
    parser.add_argument(
        'sbml_file',
        help='Path to SBML file'
    )
    parser.add_argument(
        '-n', '--replicates',
        type=int,
        default=10,
        help='Number of replicates (default: 10)'
    )
    parser.add_argument(
        '-d', '--duration',
        type=float,
        default=100.0,
        help='Simulation duration (default: 100.0)'
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.sbml_file):
        print(f"Error: File not found: {args.sbml_file}")
        sys.exit(1)
    
    test_parameters(args.sbml_file, args.replicates, args.duration)
