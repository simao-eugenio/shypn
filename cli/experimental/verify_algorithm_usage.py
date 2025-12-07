#!/usr/bin/env python3
"""Verify which algorithm is actually being used."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from _fix_imports import *
from _sbml_loader import load_sbml_model
from shypn.engine.simulation.replicate_runner import ReplicateRunner
import time


def verify_algorithm_usage(sbml_path: str, duration: float = 100.0):
    """Verify which algorithm is actually used."""
    print(f"Loading model: {sbml_path}")
    model = load_sbml_model(sbml_path)
    
    # Count transition types
    types = {}
    for t in model.transitions:
        ttype = t.transition_type
        types[ttype] = types.get(ttype, 0) + 1
    
    print(f"\nTransition Types:")
    for ttype, count in sorted(types.items()):
        print(f"  {ttype}: {count}")
    
    print(f"\n{'='*60}")
    print("CRITICAL FINDING:")
    if types.get('stochastic', 0) == 0:
        print("❌ NO STOCHASTIC TRANSITIONS!")
        print("   → τ-leaping will NEVER be used")
        print("   → Both use_tau_leaping=True and False will use same algorithm")
        print("   → This explains why 'speedup' is ~1.0x (same algorithm!)")
        print("\nROOT CAUSE:")
        print("  - SBML models have reversible reactions")
        print("  - PathwayConverter detects reversible formulas")
        print("  - Converts stochastic → continuous (correct for reversible)")
        print("  - Result: Pure continuous model, no stochastic transitions")
        print("\nIMPLICATIONS:")
        print("  - Our τ-leaping validation is NOT testing τ-leaping!")
        print("  - We're comparing Gillespie SSA vs Gillespie SSA")
        print("  - Need models with irreversible stochastic reactions")
    else:
        print(f"✓ Model has {types.get('stochastic', 0)} stochastic transitions")
        print("  → τ-leaping CAN be used (if transitions are enabled)")
    print(f"{'='*60}\n")
    
    # Run quick test to confirm
    print("Running validation with 10 replicates for better timing...")
    runner = ReplicateRunner(model)
    
    print("  Testing use_tau_leaping=True...")
    start = time.time()
    runner.run_replicates(n=10, use_tau_leaping=True, duration=duration, verbose=False)
    time_tau = time.time() - start
    
    print("  Testing use_tau_leaping=False...")
    start = time.time()
    runner.run_replicates(n=10, use_tau_leaping=False, duration=duration, verbose=False)
    time_ssa = time.time() - start
    
    speedup = time_ssa / time_tau if time_tau > 0 else 0.0
    
    print(f"\nResults (10 replicates):")
    print(f"  use_tau_leaping=True:  {time_tau:.3f}s ({time_tau/10*1000:.1f}ms per replicate)")
    print(f"  use_tau_leaping=False: {time_ssa:.3f}s ({time_ssa/10*1000:.1f}ms per replicate)")
    print(f"  Speedup: {speedup:.2f}x")
    
    if abs(speedup - 1.0) < 0.2:
        print(f"\n❌ CONFIRMED: Speedup ≈ 1.0x ({speedup:.2f}x)")
        print("   → Both settings use SAME algorithm")
        print("   → τ-leaping is NOT being tested!")
    elif speedup < 0.8:
        print(f"\n❌ CONFIRMED: τ-leaping SLOWER ({speedup:.2f}x)")
        print("   → τ-leaping overhead dominates")
        print("   → Need to investigate implementation")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Verify which algorithm is actually used'
    )
    parser.add_argument(
        'sbml_file',
        help='Path to SBML file'
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
    
    verify_algorithm_usage(args.sbml_file, args.duration)
