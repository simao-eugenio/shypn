#!/usr/bin/env python3
"""Inspect actual τ values selected during simulation.

This tool runs a simulation with τ-leaping and extracts statistics about
the leap sizes being selected, to understand if they're too conservative.
"""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from _fix_imports import *
from _sbml_loader import load_sbml_model
from shypn.engine.simulation.controller import SimulationController


def inspect_tau_values(sbml_path: str, duration: float = 100.0, time_step: float = 0.1):
    """Run simulation and inspect tau values.
    
    Args:
        sbml_path: Path to SBML file
        duration: Simulation duration
        time_step: Time step for output
    """
    # Enable INFO logging to see leap selector messages
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s:%(name)s:%(message)s'
    )
    
    print(f"Loading model: {sbml_path}")
    model = load_sbml_model(sbml_path)
    
    print(f"\nRunning τ-leaping simulation (duration={duration})...")
    controller = SimulationController(model)
    
    # Set random seed
    import random
    import numpy as np
    random.seed(42)
    np.random.seed(42)
    
    max_steps = int(duration / time_step)
    data = controller.run(
        time_step=time_step,
        max_steps=max_steps,
        algorithm='tau_leaping',
        algorithm_params={
            'epsilon': 0.03,
            'max_tau': 1.0,
            'critical_threshold': 10.0,
            'use_parallel': False
        }
    )
    
    # Extract statistics from tau_leaping_engine
    engine = controller._engines.get('tau_leaping')
    if engine and hasattr(engine, 'statistics'):
        stats = engine.statistics
        print("\n=== τ-Leaping Statistics ===")
        print(f"Total leaps: {stats.get('total_leaps', 0)}")
        print(f"Total firings: {stats.get('total_firings', 0)}")
        print(f"Mean τ: {stats.get('mean_tau', 0):.6f}")
        print(f"Exact SSA fallbacks: {stats.get('exact_ssa_fallbacks', 0)}")
        
        if stats.get('total_leaps', 0) > 0:
            avg_firings_per_leap = stats.get('total_firings', 0) / stats.get('total_leaps', 1)
            print(f"Average firings per leap: {avg_firings_per_leap:.2f}")
        
        # Calculate efficiency metrics
        num_steps = len(data.get('time', []))
        print(f"\nEfficiency Metrics:")
        print(f"Output steps: {num_steps}")
        print(f"Leaps per output step: {stats.get('total_leaps', 0) / num_steps:.2f}")
        print(f"Time per leap: {duration / stats.get('total_leaps', 1):.6f}")
        
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
        
        if avg_firings_per_leap < 2:
            print(f"❌ PROBLEM: Few firings per leap ({avg_firings_per_leap:.2f})")
            print("   → Not taking advantage of leap approximation")
            print("   → Overhead of dependency detection dominates")
        elif avg_firings_per_leap < 5:
            print(f"⚠️  WARNING: Moderate firings per leap ({avg_firings_per_leap:.2f})")
            print("   → Could be more efficient")
        else:
            print(f"✓ Good firings per leap ({avg_firings_per_leap:.2f})")
    else:
        print("\n⚠️  Could not extract statistics from engine")
    
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
    parser.add_argument(
        '-t', '--time-step',
        type=float,
        default=0.1,
        help='Output time step (default: 0.1)'
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.sbml_file):
        print(f"Error: File not found: {args.sbml_file}")
        sys.exit(1)
    
    inspect_tau_values(args.sbml_file, args.duration, args.time_step)
