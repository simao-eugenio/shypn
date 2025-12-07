#!/usr/bin/env python3
"""Test τ-leaping with simple model to verify statistics collection."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from _fix_imports import *
from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController


def create_simple_model():
    """Create a simple A → B model."""
    model = DocumentModel()
    
    # Create places
    A = model.create_place(name='A', tokens=100)
    B = model.create_place(name='B', tokens=0)
    
    # Create transition
    t = model.create_transition(name='A_to_B', transition_type='stochastic')
    
    # Create arcs
    model.create_arc(source=A, target=t, weight=1)
    model.create_arc(source=t, target=B, weight=1)
    
    # Set rate
    from shypn.core.transition_behavior import StochasticBehavior
    behavior = StochasticBehavior(rate=1.0)
    t.behavior = behavior
    
    return model


def test_tau_leaping():
    """Test τ-leaping on simple model and extract statistics."""
    print("Creating simple A → B model...")
    model = create_simple_model()
    
    print("  A: 100 tokens")
    print("  B: 0 tokens")
    print("  Rate: 1.0")
    
    print("\nRunning τ-leaping simulation...")
    controller = SimulationController(model)
    
    # Configure for tau-leaping
    controller.settings.use_tau_leaping = True
    controller.settings.tau_leaping_epsilon = 0.03
    controller.settings.enable_parallel_stochastic = False
    
    # Run simulation
    duration = 10.0
    time_step = 0.1
    max_steps = int(duration / time_step)
    
    controller.data_collector.start_collection()
    controller.run(time_step=time_step, max_steps=max_steps)
    data = controller.data_collector.get_data()
    
    print(f"\nSimulation complete:")
    print(f"  Duration: {duration}")
    print(f"  Time steps: {len(data.get('time', []))}")
    print(f"  Has _tau_leaping_engine: {hasattr(controller, '_tau_leaping_engine')}")
    
    # Extract statistics
    if hasattr(controller, '_tau_leaping_engine'):
        engine = controller._tau_leaping_engine
        stats = engine.stats
        
        print("\n=== τ-Leaping Statistics ===")
        print(f"Total leaps: {stats['total_leaps']}")
        print(f"Total firings: {stats['total_firings']}")
        print(f"Mean τ: {stats['mean_tau']:.6f}")
        print(f"Exact SSA fallbacks: {stats['exact_ssa_fallbacks']}")
        
        if stats['total_leaps'] > 0:
            avg_firings = stats['total_firings'] / stats['total_leaps']
            print(f"Average firings per leap: {avg_firings:.2f}")
            
            print("\n=== Analysis ===")
            if stats['mean_tau'] < 0.01:
                print(f"❌ Mean τ is very small ({stats['mean_tau']:.6f})")
                print("   → τ = ε / max_propensity")
                print(f"   → With ε=0.03, this means max_propensity ≈ {0.03 / stats['mean_tau']:.1f}")
            else:
                print(f"✓ Mean τ: {stats['mean_tau']:.6f}")
            
            if avg_firings < 2:
                print(f"❌ Few firings per leap ({avg_firings:.2f})")
                print("   → Overhead dominates, τ-leaping slower than Gillespie")
            elif avg_firings < 5:
                print(f"⚠️  Moderate firings per leap ({avg_firings:.2f})")
            else:
                print(f"✓ Good firings per leap ({avg_firings:.2f})")
    else:
        print("\n❌ τ-leaping engine not created!")
        print("   This means stochastic transitions were never enabled during simulation")


if __name__ == '__main__':
    test_tau_leaping()
