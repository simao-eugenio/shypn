#!/usr/bin/env python3
"""Inspect actual τ values by patching the engine to capture statistics."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from _fix_imports import *
from _sbml_loader import load_sbml_model
from shypn.engine.simulation.controller import SimulationController
from shypn.engine.simulation.settings import SimulationSettings


def inspect_tau_values(sbml_path: str, duration: float = 100.0, time_step: float = 0.1):
    """Run simulation and inspect tau values by accessing engine directly.
    
    Args:
        sbml_path: Path to SBML file
        duration: Simulation duration
        time_step: Time step for output
    """
    print(f"Loading model: {sbml_path}")
    model = load_sbml_model(sbml_path)
    
    # Check for stochastic transitions
    stochastic_transitions = [t for t in model.transitions if t.transition_type == 'stochastic']
    print(f"Model has {len(model.transitions)} transitions, {len(stochastic_transitions)} stochastic")
    if len(stochastic_transitions) == 0:
        print("ERROR: No stochastic transitions - τ-leaping won't be used!")
        return
    
    print(f"\nRunning τ-leaping simulation (duration={duration})...")
    
    # Create controller
    controller = SimulationController(model)
    
    # Configure settings for tau-leaping
    controller.settings.enable_parallel_stochastic = False
    controller.settings.use_tau_leaping = True
    controller.settings.tau_leaping_epsilon = 0.03
    
    print(f"Settings configured:")
    print(f"  use_tau_leaping: {controller.settings.use_tau_leaping}")
    print(f"  epsilon: {controller.settings.tau_leaping_epsilon}")
    
    # Calculate max_steps
    max_steps = int(duration / time_step)
    
    # Run simulation
    controller.data_collector.start_collection()
    controller.run(time_step=time_step, max_steps=max_steps)
    data = controller.data_collector.get_data()
    
    print(f"After simulation:")
    print(f"  Has _tau_leaping_engine: {hasattr(controller, '_tau_leaping_engine')}")
    
    # Access tau_leaping engine
    tau_engine = None
    if hasattr(controller, '_tau_leaping_engine'):
        tau_engine = controller._tau_leaping_engine
    
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
        
        # Get number of output steps from data
        num_steps = len(data.get('time', []))
        print(f"\nEfficiency Metrics:")
        print(f"Output steps: {num_steps}")
        print(f"Leaps per output step: {total_leaps / num_steps:.2f}" if num_steps > 0 else "N/A")
        
        # Diagnosis
        print("\n=== Performance Diagnosis ===")
        mean_tau = stats.get('mean_tau', 0)
        if mean_tau < 0.01:
            print(f"❌ PROBLEM: Mean τ is very small ({mean_tau:.6f})")
            print("   → Leap sizes are too conservative")
            print("   → Formula: τ = ε / max(propensity)")
            print(f"   → With ε={controller.settings.tau_leaping_epsilon}, max propensity ≈ {controller.settings.tau_leaping_epsilon / mean_tau:.1f}")
            print("\n   RECOMMENDATIONS:")
            print("   1. Increase epsilon (e.g., 0.05 or 0.10) - allows larger relative changes")
            print("   2. Increase max_tau (currently 1.0) - removes upper bound constraint")
            print("   3. Review critical_threshold (currently 10.0) - may force too many SSA fallbacks")
        elif mean_tau < 0.1:
            print(f"⚠️  WARNING: Mean τ is small ({mean_tau:.6f})")
            print("   → May benefit from larger epsilon or max_tau")
        else:
            print(f"✓ Mean τ looks reasonable ({mean_tau:.6f})")
        
        if total_leaps > 0:
            avg_firings = total_firings / total_leaps
            if avg_firings < 2:
                print(f"\n❌ PROBLEM: Few firings per leap ({avg_firings:.2f})")
                print("   → Not taking advantage of leap approximation")
                print("   → Overhead (dependency detection, leap calculation) dominates")
                print("   → This explains why τ-leaping is slower than Gillespie!")
            elif avg_firings < 5:
                print(f"\n⚠️  WARNING: Moderate firings per leap ({avg_firings:.2f})")
                print("   → Could be more efficient with larger leaps")
            else:
                print(f"\n✓ Good firings per leap ({avg_firings:.2f})")
                print("   → τ-leaping should show speedup benefits")
    else:
        print("\n⚠️  Could not extract statistics from engine")
        print(f"   Has _engines: {hasattr(controller, '_engines')}")
        if hasattr(controller, '_engines'):
            print(f"   Engine keys: {list(controller._engines.keys())}")
        print("\n   Trying to find TauLeapingEngine instances...")
        from shypn.engine.simulation.tau_leaping.tau_leaping_engine import TauLeapingEngine
        for name, obj in controller.__dict__.items():
            if isinstance(obj, TauLeapingEngine):
                print(f"   Found: {name}")
    
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
        help='Time step (default: 0.1)'
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.sbml_file):
        print(f"Error: File not found: {args.sbml_file}")
        sys.exit(1)
    
    inspect_tau_values(args.sbml_file, args.duration, args.time_step)
