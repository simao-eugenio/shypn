#!/usr/bin/env python3
"""Diagnostic script for Bacillus T20 (ATP regeneration) behavior.

This script runs a short simulation and analyzes T20's actual firing rate
to determine why it might differ from the expected rate.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController
import json

print("="*80)
print("BACILLUS T20 DIAGNOSTIC")
print("="*80)

# Load model
model_path = 'bacillus_sporulation_normal.shy'
print(f"\nLoading: {model_path}")
doc = DocumentModel.load_from_file(model_path)

# Restore tokens from JSON
with open(model_path, 'r') as f:
    model_data = json.load(f)

for place_data in model_data['places']:
    place = next((p for p in doc.places if p.id == place_data['id']), None)
    if place:
        marking = place_data.get('marking', place_data.get('initial_marking', 0.0))
        place.set_tokens(marking)

# Find T20 and related places
t20 = next((t for t in doc.transitions if t.id == 'T20'), None)
atp_pool = next((p for p in doc.places if p.name == 'ATP_pool'), None)
adp_pool = next((p for p in doc.places if p.name == 'ADP_pool'), None)
nutrients = next((p for p in doc.places if p.name == 'Nutrients'), None)

if not t20:
    print("ERROR: T20 not found!")
    sys.exit(1)

print(f"\n{'='*80}")
print("INITIAL STATE")
print(f"{'='*80}")
print(f"T20 (Source_ATP_regen):")
print(f"  Rate function: {t20.rate_function}")
print(f"  Is source: {getattr(t20, 'is_source', False)}")
print(f"  Type: {t20.transition_type}")

print(f"\nPlaces:")
print(f"  ATP_pool: {atp_pool.tokens:.2f} mM")
print(f"  ADP_pool: {adp_pool.tokens:.2f} mM")
print(f"  Nutrients: {nutrients.tokens:.2f} mM")

# Calculate expected rate
expected_rate = 2.5 * nutrients.tokens / (10 + nutrients.tokens)
print(f"\nExpected rate: {expected_rate:.3f} firings/s")

# Check inhibitor threshold
inhibitor_threshold = 4800 + 0.5 * adp_pool.tokens
print(f"Inhibitor threshold: {inhibitor_threshold:.2f}")
print(f"Inhibitor active (blocks): {atp_pool.tokens >= inhibitor_threshold}")

# Run short simulation
print(f"\n{'='*80}")
print("RUNNING SIMULATION (10 seconds)")
print(f"{'='*80}")

controller = SimulationController(doc, verbose=False, recording_interval=100)
controller.settings.time_step = 0.001

# Start data collection
if controller.data_collector:
    controller.data_collector.start_collection()
    controller.data_collector.record_state(controller.time)

# Run simulation
num_steps = int(10.0 / 0.001)
for i in range(num_steps):
    controller.step(time_step=0.001)
    if i % 1000 == 0 and controller.data_collector:
        controller.data_collector.record_state(controller.time)

if controller.data_collector:
    controller.data_collector.record_state(controller.time)

print(f"Simulation complete: {controller.time:.3f}s")

# Analyze results
print(f"\n{'='*80}")
print("RESULTS")
print(f"{'='*80}")

t20_after = next((t for t in controller.model.transitions if t.id == 'T20'), None)
if t20_after:
    firing_count = getattr(t20_after, 'firing_count', 0)
    observed_rate = firing_count / 10.0
    
    print(f"T20 firing count: {firing_count:.3f}")
    print(f"T20 firing rate: {observed_rate:.3f} firings/s")
    print(f"Expected rate: {expected_rate:.3f} firings/s")
    print(f"Ratio: {observed_rate / expected_rate:.3f}")
    
    print(f"\nFinal place values:")
    atp_final = next((p for p in controller.model.places if p.name == 'ATP_pool'), None)
    adp_final = next((p for p in controller.model.places if p.name == 'ADP_pool'), None)
    nutrients_final = next((p for p in controller.model.places if p.name == 'Nutrients'), None)
    
    print(f"  ATP_pool: {atp_final.tokens:.2f} mM (change: {atp_final.tokens - atp_pool.tokens:+.2f})")
    print(f"  ADP_pool: {adp_final.tokens:.2f} mM (change: {adp_final.tokens - adp_pool.tokens:+.2f})")
    print(f"  Nutrients: {nutrients_final.tokens:.2f} mM (change: {nutrients_final.tokens - nutrients.tokens:+.2f})")
    
    # Check test arcs
    print(f"\n{'='*80}")
    print("TEST ARC ANALYSIS")
    print(f"{'='*80}")
    
    test_arcs = []
    for arc in controller.model.arcs:
        if hasattr(arc, 'target') and arc.target == t20_after:
            if hasattr(arc, 'arc_type') and arc.arc_type == 'test':
                test_arcs.append(arc)
    
    if test_arcs:
        print(f"Found {len(test_arcs)} test arc(s) to T20:")
        for arc in test_arcs:
            source_place = next((p for p in controller.model.places if p.id == arc.source_id), None)
            print(f"\n  {arc.id}: {source_place.name if source_place else arc.source_id} → T20")
            print(f"    Weight: {arc.weight}")
            print(f"    Consumes: {arc.consumes_tokens() if hasattr(arc, 'consumes_tokens') else 'N/A'}")
            print(f"    Arc type: {arc.arc_type if hasattr(arc, 'arc_type') else 'unknown'}")
            if source_place:
                print(f"    Source tokens: {source_place.tokens:.2f}")
    else:
        print("No test arcs found to T20")
    
    # Diagnosis
    print(f"\n{'='*80}")
    print("DIAGNOSIS")
    print(f"{'='*80}")
    
    if abs(observed_rate / expected_rate - 1.0) < 0.1:
        print("✅ RATE OK: T20 firing rate matches expected")
    elif abs(observed_rate / expected_rate - 0.5) < 0.1:
        print("❌ RATE 50%: T20 firing rate is half of expected")
        print("\nPossible causes:")
        print("  - Check if there are consumption arcs (not test arcs) limiting flow")
        print("  - Check if T20 is actually treated as a source transition")
        print("  - Check for other transitions consuming ATP/ADP affecting the rate")
    else:
        print(f"⚠️  RATE ANOMALY: Ratio {observed_rate/expected_rate:.3f} unexpected")
    
    if atp_final.tokens > 10000:
        print(f"\n❌ ATP EXPLOSION: ATP at {atp_final.tokens:.0f} mM (should be ~5000)")
    elif atp_final.tokens < 2000:
        print(f"\n❌ ATP CRASH: ATP at {atp_final.tokens:.0f} mM (should be ~5000)")

print("\n" + "="*80)
