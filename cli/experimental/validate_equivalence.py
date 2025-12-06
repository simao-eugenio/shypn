#!/usr/bin/env python3
"""Validate Equivalence - Compare tau-leaping vs Gillespie SSA"""
import _fix_imports  # Add src to path
import argparse, sys, json
from pathlib import Path
import numpy as np
from shypn.engine.simulation.replicate_runner import ReplicateRunner
from _sbml_loader import load_sbml_model


def compare_algorithms(model, n_replicates, duration, verbose=False):
    """Compare tau-leaping and Gillespie on same model."""
    runner = ReplicateRunner(model)
    
    if verbose:
        print("Running with τ-leaping...")
    results_tau = runner.run_replicates(n=n_replicates, use_tau_leaping=True, 
                                       duration=duration, verbose=False)
    stats_tau = runner.compute_statistics(results_tau)
    
    if verbose:
        print("Running with Gillespie SSA...")
    results_ssa = runner.run_replicates(n=n_replicates, use_tau_leaping=False,
                                       duration=duration, seed_base=10000, verbose=False)
    stats_ssa = runner.compute_statistics(results_ssa)
    
    # Compare final means
    comparison = {}
    for species_id in stats_tau['species_statistics'].keys():
        if species_id not in stats_ssa['species_statistics']:
            continue
        
        tau_mean = stats_tau['species_statistics'][species_id]['mean'][-1]
        ssa_mean = stats_ssa['species_statistics'][species_id]['mean'][-1]
        
        rel_diff = abs(tau_mean - ssa_mean) / abs(ssa_mean) if ssa_mean != 0 else 0.0
        
        comparison[species_id] = {
            'tau_mean': float(tau_mean),
            'ssa_mean': float(ssa_mean),
            'rel_diff': float(rel_diff),
            'equivalent': rel_diff < 0.05  # 5% tolerance
        }
    
    n_equivalent = sum(1 for c in comparison.values() if c['equivalent'])
    equivalence_rate = n_equivalent / len(comparison) if comparison else 0.0
    
    return {
        'comparison': comparison,
        'n_species': len(comparison),
        'n_equivalent': n_equivalent,
        'equivalence_rate': float(equivalence_rate)
    }

def main():
    parser = argparse.ArgumentParser(description='Validate algorithm equivalence')
    parser.add_argument('model', help='SBML model file')
    parser.add_argument('-n', '--replicates', type=int, default=100)
    parser.add_argument('-d', '--duration', type=float, default=100.0)
    parser.add_argument('-o', '--output', default='validation_results')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    
    try:
        model_path = Path(args.model)
        if not model_path.exists():
            sys.exit(f"ERROR: Model not found: {model_path}")
        
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Loading {model_path.name}...")
        model = load_sbml_model(model_path)
        
        print(f"Comparing algorithms ({args.replicates} replicates each)...")
        results = compare_algorithms(model, args.replicates, args.duration, args.verbose)
        
        # Export results
        results_file = output_dir / 'validation_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print(f"\n{'='*60}")
        print("Validation Results")
        print(f"{'='*60}")
        print(f"Species analyzed: {results['n_species']}")
        print(f"Equivalent: {results['n_equivalent']} ({100*results['equivalence_rate']:.1f}%)")
        
        print(f"\nFirst 5 species:")
        for species_id, comp in list(results['comparison'].items())[:5]:
            status = "✓" if comp['equivalent'] else "✗"
            print(f"  {status} {species_id}: τ={comp['tau_mean']:.2f}, SSA={comp['ssa_mean']:.2f}, "
                  f"diff={100*comp['rel_diff']:.1f}%")
        
        print(f"\n✓ Results saved to: {results_file}")
        
        if results['equivalence_rate'] >= 0.95:
            print("\n✅ VALIDATION PASSED: Algorithms are equivalent (≥95%)")
        else:
            print(f"\n⚠️  VALIDATION WARNING: Only {100*results['equivalence_rate']:.1f}% equivalent")
        
    except Exception as e:
        sys.exit(f"ERROR: {e}")

if __name__ == '__main__':
    main()
