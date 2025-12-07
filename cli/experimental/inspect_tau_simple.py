#!/usr/bin/env python3
"""Inspect actual τ values selected during simulation - simpler version."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from _fix_imports import *
from _sbml_loader import load_sbml_model
from shypn.engine.simulation.replicate_runner import ReplicateRunner


def inspect_tau_values(sbml_path: str, duration: float = 100.0):
    """Run simulation and inspect tau values.
    
    Args:
        sbml_path: Path to SBML file
        duration: Simulation duration
    """
    print(f"Loading model: {sbml_path}")
    model = load_sbml_model(sbml_path)
    
    print(f"\nRunning τ-leaping simulation (duration={duration})...")
    runner = ReplicateRunner(model)
    
    # Run with τ-leaping
    results = runner.run_replicates(
        n=1,
        use_tau_leaping=True,
        duration=duration,
        verbose=False
    )
    
    # Access the controller from the runner
    # The controller has the tau_leaping engine with stats
    controller = runner.controller
    
    # Try to find the tau_leaping engine
    tau_engine = None
    if hasattr(controller, '_engines'):
        tau_engine = controller._engines.get('tau_leaping')
    
    if tau_engine and hasattr(tau_engine, 'stats'):
        stats = tau_engine.stats
        print("\n=== τ-Leaping Statistics ===")
        print(f"Total leaps: {stats.get('total_leaps', 0)}")
        print(f"Total firings: {stats.get('total_firings', 0)}")
        print(f"Mean τ: {stats.get('mean_tau', 0):.6f}")
        print(f"Exact SSA fallbacks: {stats.get('exact_ssa_fallbacks', 0)}")
        
        total_leaps = stats.get('total_leaps', 0)
        total_firings = stats.get('total_firings', 0)
        
        if total_leaps > 0:
            avg_firings_per_leap = total_firings / total_leaps
            print(f"Average firings per leap: {avg_firings_per_leap:.2f}")
            print(f"Time per leap: {duration / total_leaps:.6f}")
        
        # Calculate efficiency metrics
        print(f"\nEfficiency Metrics:")
        print(f"Simulation duration: {duration}")
        
        # Diagnosis
        print("\n=== Performance Diagnosis ===")
        mean_tau = stats.get('mean_tau', 0)
        if mean_tau < 0.01:
            print(f"❌ PROBLEM: Mean τ is very small ({mean_tau:.6f})")
            print("   → Leap sizes are too conservative")
            print("   → Consider increasing epsilon or max_tau")
        elif mean_tau < 0.1:
            print(f"⚠️  WARNING: Mean τ is small ({mean_tau:.6f})")
            print("   → May benefit from larger epsilon or max_tau")
        else:
            print(f"✓ Mean τ looks reasonable ({mean_tau:.6f})")
        
        if total_leaps > 0 and avg_firings_per_leap < 2:
            print(f"❌ PROBLEM: Few firings per leap ({avg_firings_per_leap:.2f})")
            print("   → Not taking advantage of leap approximation")
            print("   → Overhead of dependency detection dominates")
        elif total_leaps > 0 and avg_firings_per_leap < 5:
            print(f"⚠️  WARNING: Moderate firings per leap ({avg_firings_per_leap:.2f})")
            print("   → Could be more efficient")
        elif total_leaps > 0:
            print(f"✓ Good firings per leap ({avg_firings_per_leap:.2f})")
    else:
        print("\n⚠️  Could not extract statistics from engine")
        print(f"   Controller has _engines: {hasattr(controller, '_engines')}")
        if hasattr(controller, '_engines'):
            print(f"   Engines: {list(controller._engines.keys())}")
    
    print("\n✓ Inspection complete")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Inspect τ values selected during τ-leaping simulation'
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
    
    inspect_tau_values(args.sbml_file, args.duration)
