#!/usr/bin/env python3
"""Print τ-leaping statistics after simulation."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from _fix_imports import *
from _sbml_loader import load_sbml_model


def run_and_print_stats(sbml_path: str, duration: float = 100.0):
    """Run τ-leaping simulation and print statistics."""
    print(f"Loading model: {sbml_path}")
    model = load_sbml_model(sbml_path)
    
    # Create controller
    from shypn.engine.simulation.controller import SimulationController
    controller = SimulationController(model)
    
    # Configure for tau-leaping
    controller.settings.use_tau_leaping = True
    controller.settings.tau_leaping_epsilon = 0.03
    controller.settings.enable_parallel_stochastic = False
    
    print(f"\nRunning τ-leaping simulation (duration={duration})...")
    
    # Run simulation
    time_step = 0.1
    max_steps = int(duration / time_step)
    
    controller.data_collector.start_collection()
    controller.run(time_step=time_step, max_steps=max_steps)
    
    # Access engine and print statistics
    if hasattr(controller, '_tau_leaping_engine'):
        controller._tau_leaping_engine.print_statistics()
    else:
        print("\n❌ τ-leaping engine was not created!")
        print("   Possible reasons:")
        print("   - No stochastic transitions in model")
        print("   - Stochastic transitions never enabled (insufficient tokens)")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Print τ-leaping statistics after simulation'
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
    
    run_and_print_stats(args.sbml_file, args.duration)
