#!/usr/bin/env python3
"""Quick test to verify T20 fires on every step after the fix."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController
import json

# Load model
os.chdir('/home/simao/projetos/shypn/workspace/projects/My_Project/thermodynamics')
model = DocumentModel.load_from_file('bacillus_sporulation_normal.shy')

# Restore tokens
with open('bacillus_sporulation_normal.shy', 'r') as f:
    model_data = json.load(f)

for place_data in model_data.get('places', []):
    place_id = place_data['id']
    for place in model.places:
        if place.id == place_id:
            place.marking = place_data.get('marking', 0)
            break

# Get initial ATP
atp_place = None
for place in model.places:
    if place.name == 'ATP_pool':
        atp_place = place
        break

if not atp_place:
    print("ERROR: ATP_pool place not found")
    sys.exit(1)

# Get T20 transition
t20 = None
for trans in model.transitions:
    if trans.id == 'T20':
        t20 = trans
        break

if not t20:
    print("ERROR: T20 transition not found")
    sys.exit(1)

print("="*80)
print("Testing Conflict Resolution Fix")
print("="*80)
print(f"\nInitial ATP: {atp_place.marking:.2f} mM")
print(f"T20 ID: {t20.id}")
print(f"T20 Rate: {t20.rate if hasattr(t20, 'rate') else 'N/A'}")

# Track T20 firing
controller = SimulationController(model)

# Check T20 firing over 10 steps
print(f"\nMonitoring T20 over 10 simulation steps:")
print("-"*80)

for step in range(10):
    # Record ATP before
    atp_before = atp_place.marking
    
    # Get T20's firing count before
    firing_before = getattr(t20, 'firing_count', 0)
    
    # Step
    controller.step()
    
    # Record ATP after
    atp_after = atp_place.marking
    
    # Get T20's firing count after
    firing_after = getattr(t20, 'firing_count', 0)
    
    # Calculate change
    atp_delta = atp_after - atp_before
    firing_delta = firing_after - firing_before
    
    print(f"Step {step+1}: t={controller.time:.3f}s | ATP: {atp_before:7.2f} → {atp_after:7.2f} ({atp_delta:+7.2f}) | "
          f"T20 fired: {firing_delta:.3f}")

print("\n" + "="*80)
print("ANALYSIS")
print("="*80)

# Final ATP
print(f"\nFinal ATP after 10 steps: {atp_place.marking:.2f} mM")

# Check if T20 fired every step
if hasattr(t20, 'firing_count'):
    print(f"T20 firing count: {t20.firing_count:.3f}")
    expected_firings = t20.rate * controller.time if hasattr(t20, 'rate') else 0
    print(f"Expected firings: {expected_firings:.3f}")
    
    if t20.firing_count > 0:
        firing_rate_pct = (t20.firing_count / expected_firings) * 100 if expected_firings > 0 else 0
        print(f"Firing rate: {firing_rate_pct:.1f}%")
        
        if firing_rate_pct > 95:
            print(f"\n✓ SUCCESS: T20 firing at {firing_rate_pct:.1f}% (expected ~100%)")
        else:
            print(f"\n✗ FAILURE: T20 only firing at {firing_rate_pct:.1f}% (expected ~100%)")
    else:
        print(f"\n✗ FAILURE: T20 never fired")
else:
    print("\nNo firing_count attribute found on T20")
