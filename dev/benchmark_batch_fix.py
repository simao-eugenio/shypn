#!/usr/bin/env python3
"""Test batch performance fix - measure controller creation overhead.

Compares:
- OLD: Creating 100 controllers (one per replicate)
- NEW: Creating 1 controller, resetting state 100 times
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import time
from copy import deepcopy

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController


def benchmark_old_approach(model, n_replicates=100):
    """OLD approach: Create fresh controller for each replicate."""
    start = time.time()
    
    for i in range(n_replicates):
        # This is what the old code did
        controller = SimulationController(model, verbose=False, recording_interval=1)
        # Simulate minimal work
        pass
    
    elapsed = time.time() - start
    return elapsed


def benchmark_new_approach(model, n_replicates=100):
    """NEW approach: Create controller once, reuse."""
    start = time.time()
    
    # Create once (outside loop)
    controller = SimulationController(model, verbose=False, recording_interval=1)
    
    for i in range(n_replicates):
        # Only reset state (fast)
        controller.time = 0.0
        for place in model.places:
            place.tokens = place.initial_marking
    
    elapsed = time.time() - start
    return elapsed


if __name__ == "__main__":
    model_path = "/home/simao/projetos/shypn/workspace/projects/My_Project/drug_discovery/models/normal/macrocycle_transport_normal_nme_0_thermo.shy"
    
    print("Loading model...")
    model = DocumentModel.load_from_file(model_path)
    print(f"  Loaded: {len(model.places)} places, {len(model.transitions)} transitions, {len(model.arcs)} arcs")
    
    print("\nBenchmarking OLD approach (100 controller creations)...")
    time_old = benchmark_old_approach(model, n_replicates=100)
    print(f"  ⏱️  Time: {time_old:.2f}s")
    
    print("\nBenchmarking NEW approach (1 controller, 100 resets)...")
    time_new = benchmark_new_approach(model, n_replicates=100)
    print(f"  ⏱️  Time: {time_new:.2f}s")
    
    speedup = time_old / time_new
    print(f"\n{'='*60}")
    print(f"Speedup: {speedup:.1f}×")
    print(f"OLD: {time_old:.2f}s → NEW: {time_new:.2f}s")
    
    if speedup > 2.0:
        print(f"✅ EXCELLENT: {speedup:.1f}× speedup will eliminate the 2× slowdown!")
    elif speedup > 1.5:
        print(f"✅ GOOD: {speedup:.1f}× speedup will significantly improve batch performance")
    else:
        print(f"⚠️  MODEST: {speedup:.1f}× speedup may not fully eliminate the slowdown")
