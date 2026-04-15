#!/usr/bin/env python3
"""Test script to verify test arc weight bug fix.

This tests that test arcs (read arcs) do NOT affect transition rates
when their weight is not 1.0.

Expected behavior:
- Test arcs should only check token availability (enablement)
- Test arc weight should NOT scale the effective transition rate
- Only normal/consuming arcs should limit flow based on available tokens

Bug symptoms:
- Test arc with weight=0.5 causes rate to be ~0.5x expected
- Test arc with weight=2.0 would cause rate to be ~2x expected

This is because max_flow calculation divides by arc.weight, which
incorrectly affects test arcs.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.file.netobj_persistency import NetObjPersistency
from shypn.engine.simulation.controller import SimulationController

print("="*80)
print("TEST: Test Arc Weight Bug")
print("="*80)
print()

# Load Bacillus model
model_path = 'workspace/projects/My_Project/thermodynamics/bacillus_sporulation_normal.shy'
print(f"Loading model: {model_path}")
model = NetObjPersistency.load(model_path)

# Find T20 and its arcs
t20 = next((t for t in model.transitions if t.id == 'T20'), None)
if not t20:
    print("ERROR: T20 not found!")
    sys.exit(1)

print(f"Found transition T20: {t20.name}")
print(f"  Rate function: {t20.rate_function}")
print(f"  Is source: {getattr(t20, 'is_source', False)}")
print()

# Find all arcs connected to T20
input_arcs = [arc for arc in model.arcs if hasattr(arc, 'target') and arc.target == t20]
output_arcs = [arc for arc in model.arcs if hasattr(arc, 'source') and arc.source == t20]

print(f"Input arcs to T20: {len(input_arcs)}")
for arc in input_arcs:
    arc_type = arc.arc_type if hasattr(arc, 'arc_type') else 'unknown'
    consumes = arc.consumes_tokens() if hasattr(arc, 'consumes_tokens') else 'N/A'
    source_name = arc.source.name if hasattr(arc.source, 'name') else arc.source_id
    print(f"  {arc.id}: {source_name} → T20")
    print(f"    Type: {arc_type}, Weight: {arc.weight}, Consumes: {consumes}")

print()
print(f"Output arcs from T20: {len(output_arcs)}")
for arc in output_arcs:
    target_name = arc.target.name if hasattr(arc.target, 'name') else arc.target_id
    print(f"  {arc.id}: T20 → {target_name}, Weight: {arc.weight}")

print()
print("-"*80)
print("Running simulation (1 second, watch for [ARC_DEBUG] output)...")
print("-"*80)
print()

# Run simulation with debug output
controller = SimulationController(model, method='continuous', time_step=0.001)
controller.simulate(duration=1.0)

print()
print("="*80)
print("ANALYSIS")
print("="*80)

# Get ATP regeneration transition
if hasattr(controller, 'model'):
    t20 = next((t for t in controller.model.transitions if t.id == 'T20'), None)
    if t20:
        firing_count = getattr(t20, 'firing_count', 0)
        print(f"T20 firing count: {firing_count:.3f}")
        print(f"T20 firing rate: {firing_count / 1.0:.3f} firings/s")
        print()
        
        # Expected rate
        nutrients = next((p for p in controller.model.places if p.name == 'Nutrients'), None)
        if nutrients:
            expected_rate = 2.5 * nutrients.tokens / (10 + nutrients.tokens)
            print(f"Expected rate: {expected_rate:.3f} firings/s")
            print(f"Ratio (observed/expected): {(firing_count / 1.0) / expected_rate:.3f}")
            print()
            
            if abs((firing_count / 1.0) / expected_rate - 1.0) < 0.1:
                print("✓ PASS: Rate is within 10% of expected")
            else:
                print("✗ FAIL: Rate differs significantly from expected")
                print()
                print("This indicates test arc weight is affecting the rate!")

print()
print("Test complete.")
