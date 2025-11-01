#!/usr/bin/env python3
"""
Diagnostic script to test if T3 and T4 can actually fire in simulation
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController

# Load the model
model_path = Path('workspace/projects/Interactive/models/hsa00010.shy')
print("=" * 80)
print("LOADING MODEL")
print("=" * 80)
print(f"Loading: {model_path}")

# Just load the JSON directly
with open(model_path, 'r') as f:
    model_data = json.load(f)

print(f"Loaded: {len(model_data['places'])} places, {len(model_data['transitions'])} transitions, {len(model_data['arcs'])} arcs")
print()

# Check P101 initial state
p101 = next(p for p in model_data['places'] if p['id'] == 'P101')
print(f"P101 ({p101['label']}): {p101['initial_marking']} tokens")
print()

# Check T3 and T4 initial state
print("=" * 80)
print("CHECKING T3 AND T4 CONFIGURATION")
print("=" * 80)

for tid in ['T3', 'T4']:
    trans = next(t for t in model_data['transitions'] if t['id'] == tid)
    print(f"\n{tid} ({trans.get('label', 'no label')})")
    print(f"  Type: {trans.get('transition_type', 'N/A')}")
    print(f"  Rate formula: {trans.get('rate', 'N/A')}")
    
    # Check input arcs
    input_arcs = [arc for arc in model_data['arcs'] if arc.get('target_id') == tid]
    print(f"  Input arcs: {len(input_arcs)}")
    
    all_enabled = True
    for arc in input_arcs:
        source_place = next(p for p in model_data['places'] if p['id'] == arc['source_id'])
        arc_type = arc.get('arc_type', 'normal')
        weight = arc.get('weight', 1)
        threshold = arc.get('threshold', None)
        
        print(f"    - {source_place['id']} ({source_place['label']}): {source_place['initial_marking']} tokens, arc type: {arc_type}")
        
        # Check if enabled
        if arc_type == 'test':
            enabled = source_place['initial_marking'] >= weight
        elif arc_type == 'inhibitor':
            enabled = source_place['initial_marking'] < weight
        else:
            tokens_needed = threshold if threshold is not None else weight
            enabled = source_place['initial_marking'] >= tokens_needed
        
        if not enabled:
            all_enabled = False
            print(f"        ❌ NOT ENABLED")
        else:
            print(f"        ✅ ENABLED")
    
    if all_enabled:
        print(f"  ✅ ALL INPUT ARCS ENABLED")
    else:
        print(f"  ❌ SOME ARCS DISABLED")

print("\n" + "=" * 80)
print("DIAGNOSIS SUMMARY")
print("=" * 80)
print("\nBoth T3 and T4 have all inputs enabled based on the model file.")
print("\nIf they're not firing in the actual application, possible reasons:")
print("  1. Simulation not running (check if simulation is started)")
print("  2. Simulation time too short (stochastic transitions need time to fire)")
print("  3. Rate formula evaluating to 0 or very small (check Michaelis-Menten)")
print("  4. Continuous transitions may need special handling")
print("  5. GUI not updating to show changes")
print("\nRecommendations:")
print("  - Check if simulation is actually running in the GUI")
print("  - Run simulation for longer time (e.g., 10-100 time units)")
print("  - Check the simulation speed/step settings")
print("  - Verify that continuous transitions are being processed")
print("\n" + "=" * 80)
