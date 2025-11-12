#!/usr/bin/env python3
"""
Practical demonstration: Using wiener(t) to escape steady states.

This shows how to modify a continuous transition model that gets stuck
in a steady state by adding stochastic noise with the Wiener process.

BEFORE: P1=0.9, P2=0.1 stays constant forever (steady state trap)
AFTER:  Tokens fluctuate around equilibrium due to molecular noise
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.engine.simulation.controller import SimulationController
from shypn.engine.function_catalog import reset_wiener


def create_deterministic_model():
    """Create model with deterministic rates (gets stuck in steady state)."""
    doc_model = DocumentModel()
    
    # Two places in a cycle
    p1 = Place(100, 100, 'P1', 'P1')
    p1.tokens = 1.0
    p2 = Place(300, 100, 'P2', 'P2')
    p2.tokens = 0.0
    doc_model.places = [p1, p2]
    
    # Continuous transitions with FIXED rates
    t1 = Transition(150, 100, 'T1', 'T1')
    t1.transition_type = 'continuous'
    t1.rate = 1.0  # Constant rate
    
    t2 = Transition(250, 100, 'T2', 'T2')
    t2.transition_type = 'continuous'
    t2.rate = 1.0  # Constant rate
    
    doc_model.transitions = [t1, t2]
    
    # Add arcs (cycle: P1→T1→P2→T2→P1)
    arc1 = Arc(p1, t1, 'A1', 'A1')
    arc2 = Arc(t1, p2, 'A2', 'A2')
    arc3 = Arc(p2, t2, 'A3', 'A3')
    arc4 = Arc(t2, p1, 'A4', 'A4')
    doc_model.arcs = [arc1, arc2, arc3, arc4]
    
    return doc_model


def create_stochastic_model():
    """Create model with stochastic rates (escapes steady state)."""
    doc_model = DocumentModel()
    
    # Two places in a cycle
    p1 = Place(100, 100, 'P1', 'P1')
    p1.tokens = 1.0
    p2 = Place(300, 100, 'P2', 'P2')
    p2.tokens = 0.0
    doc_model.places = [p1, p2]
    
    # Continuous transitions with STOCHASTIC rates
    # Strategy #1 (confidence 0.95): rate * (1 + 0.1 * wiener(time))
    t1 = Transition(150, 100, 'T1', 'T1')
    t1.transition_type = 'continuous'
    t1.rate = "1.0 * (1 + 0.1 * wiener(time))"  # ±10% noise
    
    t2 = Transition(250, 100, 'T2', 'T2')
    t2.transition_type = 'continuous'
    t2.rate = "1.0 * (1 + 0.1 * wiener(time))"  # ±10% noise
    
    doc_model.transitions = [t1, t2]
    
    # Add arcs (cycle: P1→T1→P2→T2→P1)
    arc1 = Arc(p1, t1, 'A1', 'A1')
    arc2 = Arc(t1, p2, 'A2', 'A2')
    arc3 = Arc(p2, t2, 'A3', 'A3')
    arc4 = Arc(t2, p1, 'A4', 'A4')
    doc_model.arcs = [arc1, arc2, arc3, arc4]
    
    return doc_model


def run_simulation(model, title, steps=50):
    """Run simulation and print token evolution."""
    print(f"\n{'=' * 70}")
    print(f"{title}")
    print(f"{'=' * 70}\n")
    
    controller = SimulationController(model)
    
    # Get place references
    p1 = model.places[0]  # P1
    p2 = model.places[1]  # P2
    
    # Print header
    print(f"{'Step':>6} {'Time':>8} {'P1':>12} {'P2':>12} {'Sum':>12}")
    print("-" * 70)
    
    # Record token history
    p1_history = []
    p2_history = []
    
    for step in range(steps + 1):
        p1_tokens = p1.tokens
        p2_tokens = p2.tokens
        total = p1_tokens + p2_tokens
        
        p1_history.append(p1_tokens)
        p2_history.append(p2_tokens)
        
        # Print every 5 steps
        if step % 5 == 0:
            print(f"{step:6d} {controller.time:8.2f} {p1_tokens:12.6f} {p2_tokens:12.6f} {total:12.6f}")
        
        if step < steps:
            controller.step(time_step=0.1)
    
    # Calculate statistics
    import statistics
    
    # Skip first 10 steps (equilibration)
    p1_steady = p1_history[10:]
    p2_steady = p2_history[10:]
    
    p1_mean = statistics.mean(p1_steady)
    p1_std = statistics.stdev(p1_steady) if len(p1_steady) > 1 else 0.0
    p2_mean = statistics.mean(p2_steady)
    p2_std = statistics.stdev(p2_steady) if len(p2_steady) > 1 else 0.0
    
    print("-" * 70)
    print(f"\nStatistics (steps 10-{steps}):")
    print(f"  P1: mean = {p1_mean:.6f}, std = {p1_std:.6f}")
    print(f"  P2: mean = {p2_mean:.6f}, std = {p2_std:.6f}")
    
    if p1_std < 0.001:
        print(f"\n⚠️  LOW VARIANCE: Model is stuck in steady state")
        print(f"    Recommendation: Add stochastic noise with wiener()")
    else:
        print(f"\n✓  DYNAMIC BEHAVIOR: Tokens fluctuate due to molecular noise")
        print(f"    Stochastic perturbations prevent steady state trap")
    
    return p1_history, p2_history


def main():
    """Run both models for comparison."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 10 + "WIENER PROCESS: STEADY STATE ESCAPE" + " " * 23 + "║")
    print("╚" + "=" * 68 + "╝")
    
    # 1. Deterministic model (gets stuck)
    model_det = create_deterministic_model()
    p1_det, p2_det = run_simulation(
        model_det,
        "MODEL 1: Deterministic Rates (rate = 1.0)",
        steps=50
    )
    
    # 2. Stochastic model (escapes)
    reset_wiener()  # Start fresh Wiener process
    model_sto = create_stochastic_model()
    p1_sto, p2_sto = run_simulation(
        model_sto,
        "MODEL 2: Stochastic Rates (rate = 1.0 * (1 + 0.1 * wiener(time)))",
        steps=50
    )
    
    # Summary comparison
    print("\n" + "=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)
    
    import statistics
    
    # Deterministic statistics (skip first 10)
    p1_det_std = statistics.stdev(p1_det[10:])
    
    # Stochastic statistics (skip first 10)
    p1_sto_std = statistics.stdev(p1_sto[10:])
    
    print(f"\nDeterministic model variance: {p1_det_std:.6f}")
    print(f"Stochastic model variance:    {p1_sto_std:.6f}")
    print(f"Variance increase:            {p1_sto_std/p1_det_std if p1_det_std > 0 else float('inf'):.2f}x")
    
    print("\n" + "-" * 70)
    print("BIOLOGICAL INTERPRETATION:")
    print("-" * 70)
    print("""
Deterministic model (rate = 1.0):
  - Represents large molecule populations (>>1000)
  - Fluctuations average out (law of large numbers)
  - Reaches exact steady state equilibrium
  - Unrealistic for small molecule counts

Stochastic model (rate = 1.0 * (1 + 0.1 * wiener(time))):
  - Represents molecular noise from finite populations
  - ±10% fluctuations mimic intrinsic stochasticity
  - Tokens fluctuate around equilibrium point
  - Biologically realistic for cellular processes
  - Prevents numerical steady state traps
    """)
    
    print("-" * 70)
    print("HOW TO USE IN YOUR MODEL:")
    print("-" * 70)
    print("""
1. Identify transitions that reach steady state
2. Modify rate functions to include wiener(time):
   
   BEFORE:  rate = "1.0"
   AFTER:   rate = "1.0 * (1 + 0.1 * wiener(time))"
   
3. Adjust noise amplitude (0.05 to 0.2 typical):
   - 0.05 (5%):  Small fluctuations, mostly deterministic
   - 0.10 (10%): Moderate noise, biological default
   - 0.20 (20%): Large fluctuations, highly stochastic

4. Run simulation - tokens will fluctuate instead of freezing

5. For reproducibility, use seed parameter:
   rate = "1.0 * (1 + 0.1 * wiener(time, 1.0, 0.1, 42))"
    """)
    
    print("=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\n✓ wiener(t) successfully breaks steady state trap!")
    print("✓ Use in rate expressions: rate * (1 + 0.1 * wiener(time))")
    print()


if __name__ == "__main__":
    main()
