#!/usr/bin/env python3
"""Extract τ-leaping statistics by patching the engine."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from _fix_imports import *
from _sbml_loader import load_sbml_model
from shypn.engine.simulation.tau_leaping.tau_leaping_engine import TauLeapingEngine

# Global statistics collection
tau_statistics = {
    'tau_values': [],
    'firings': [],
    'propensities': []
}

# Monkey-patch the execute_step method to collect statistics
_original_execute_step = TauLeapingEngine.execute_step

def patched_execute_step(self, controller):
    """Patched execute_step that collects tau values."""
    # Call original
    result = _original_execute_step(self, controller)
    
    # Collect statistics
    tau_statistics['tau_values'].append(self.stats.get('mean_tau', 0))
    tau_statistics['firings'].append(self.stats.get('total_firings', 0))
    
    return result

TauLeapingEngine.execute_step = patched_execute_step


def run_with_statistics(sbml_path: str, n_replicates: int = 1, duration: float = 100.0):
    """Run simulation and collect statistics."""
    from shypn.engine.simulation.replicate_runner import ReplicateRunner
    
    print(f"Loading model: {sbml_path}")
    model = load_sbml_model(sbml_path)
    
    print(f"\nRunning {n_replicates} replicates with τ-leaping...")
    runner = ReplicateRunner(model)
    
    # Run with tau-leaping
    results = runner.run_replicates(
        n=n_replicates,
        use_tau_leaping=True,
        duration=duration,
        verbose=True
    )
    
    print(f"\n=== Statistics Collection ===")
    print(f"Collected {len(tau_statistics['tau_values'])} data points")
    
    if tau_statistics['tau_values']:
        import numpy as np
        tau_vals = [t for t in tau_statistics['tau_values'] if t > 0]
        
        if tau_vals:
            print(f"\nτ Value Statistics:")
            print(f"  Mean: {np.mean(tau_vals):.6f}")
            print(f"  Median: {np.median(tau_vals):.6f}")
            print(f"  Min: {np.min(tau_vals):.6f}")
            print(f"  Max: {np.max(tau_vals):.6f}")
            print(f"  Std: {np.std(tau_vals):.6f}")
            
            # Diagnosis
            mean_tau = np.mean(tau_vals)
            if mean_tau < 0.01:
                print(f"\n❌ PROBLEM: Mean τ is very small ({mean_tau:.6f})")
                print("   Conservative formula: τ = ε / max_propensity")
                print(f"   With ε=0.03, max_propensity ≈ {0.03 / mean_tau:.1f}")
                print("\n   ROOT CAUSE: τ-leaping overhead dominates")
                print("   - Dependency detection")
                print("   - Leap calculation")
                print("   - Poisson sampling")
                print("\n   SOLUTION: Need larger τ values")
                print("   - Increase epsilon (0.05, 0.10)")
                print("   - Increase max_tau (5.0, 10.0)")
                print("   - Enable parallel execution")
            elif mean_tau < 0.1:
                print(f"\n⚠️  WARNING: Mean τ is small ({mean_tau:.6f})")
            else:
                print(f"\n✓ Mean τ looks good ({mean_tau:.6f})")
    else:
        print("\n❌ No statistics collected - τ-leaping may not have been used!")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Extract τ-leaping statistics using patched engine'
    )
    parser.add_argument(
        'sbml_file',
        help='Path to SBML file'
    )
    parser.add_argument(
        '-n', '--replicates',
        type=int,
        default=1,
        help='Number of replicates (default: 1)'
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
    
    run_with_statistics(args.sbml_file, args.replicates, args.duration)
