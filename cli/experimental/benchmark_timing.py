#!/usr/bin/env python3
"""Benchmark Timing - Measure and compare execution times"""
import _fix_imports  # Add src to path
import argparse, sys, json, time
from pathlib import Path
from shypn.engine.simulation.replicate_runner import ReplicateRunner
from _sbml_loader import load_sbml_model


def benchmark_algorithm(model, algorithm_name, use_tau_leaping, n_replicates, duration):
    """Benchmark a single algorithm."""
    runner = ReplicateRunner(model)
    
    start_time = time.time()
    results = runner.run_replicates(
        n=n_replicates,
        use_tau_leaping=use_tau_leaping,
        duration=duration,
        verbose=False
    )
    end_time = time.time()
    
    elapsed = end_time - start_time
    per_replicate = elapsed / n_replicates
    
    return {
        'algorithm': algorithm_name,
        'n_replicates': n_replicates,
        'total_time': float(elapsed),
        'time_per_replicate': float(per_replicate),
        'successful': sum(1 for r in results if 'error' not in r)
    }

def main():
    parser = argparse.ArgumentParser(description='Benchmark simulation timing')
    parser.add_argument('model', help='SBML model file')
    parser.add_argument('-n', '--replicates', type=int, default=100)
    parser.add_argument('-d', '--duration', type=float, default=100.0)
    parser.add_argument('--compare', action='store_true', help='Compare both algorithms')
    parser.add_argument('-o', '--output', default='benchmark_results')
    args = parser.parse_args()
    
    try:
        model_path = Path(args.model)
        if not model_path.exists():
            sys.exit(f"ERROR: Model not found: {model_path}")
        
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Loading {model_path.name}...")
        model = load_sbml_model(model_path)
        print(f"  Model: {len(model.places)} places, {len(model.transitions)} transitions")
        
        results = {}
        
        # Benchmark τ-leaping
        print(f"\nBenchmarking τ-leaping ({args.replicates} replicates)...")
        results['tau_leaping'] = benchmark_algorithm(model, 'τ-leaping', True, args.replicates, args.duration)
        print(f"  Time: {results['tau_leaping']['total_time']:.2f}s "
              f"({results['tau_leaping']['time_per_replicate']*1000:.1f}ms per replicate)")
        
        if args.compare:
            # Benchmark Gillespie
            print(f"\nBenchmarking Gillespie SSA ({args.replicates} replicates)...")
            results['gillespie'] = benchmark_algorithm(model, 'Gillespie', False, args.replicates, args.duration)
            print(f"  Time: {results['gillespie']['total_time']:.2f}s "
                  f"({results['gillespie']['time_per_replicate']*1000:.1f}ms per replicate)")
            
            # Compute speedup
            speedup = results['gillespie']['total_time'] / results['tau_leaping']['total_time']
            results['speedup'] = float(speedup)
            
            print(f"\n{'='*60}")
            print(f"Speedup: {speedup:.2f}x (τ-leaping is {speedup:.2f}x faster)")
            print(f"{'='*60}")
        
        # Export results
        results_file = output_dir / 'benchmark_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ Results saved to: {results_file}")
        
    except Exception as e:
        sys.exit(f"ERROR: {e}")

if __name__ == '__main__':
    main()
