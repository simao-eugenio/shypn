#!/usr/bin/env python3
"""Check manually created transitions in BIOMD0000000068."""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController
from shypn.engine.simulation.settings import SimulationSettings

model_path = "/home/simao/projetos/shypn/workspace/projects/My_Project/models/BIOMD0000000068.shy"
document = DocumentModel.load_from_file(model_path)

print("="*80)
print("TRANSITION TYPE ANALYSIS")
print("="*80)

# Analyze all transitions
print(f"\nAll transitions in model:")
for t in document.transitions:
    ttype = t.transition_type
    rate = getattr(t, 'rate', None)
    is_source = getattr(t, 'is_source', False)
    is_sink = getattr(t, 'is_sink', False)
    
    # Count arcs
    in_arcs = [a for a in document.arcs if a.target == t]
    out_arcs = [a for a in document.arcs if a.source == t]
    
    marker = ""
    if len(in_arcs) == 1 and len(out_arcs) == 1 and not is_source and not is_sink:
        marker = " ← MANUAL P-T-P?"
    
    print(f"  {t.label} (ID: {t.id}): type={ttype}, rate={rate}, source={is_source}, sink={is_sink}, in={len(in_arcs)}, out={len(out_arcs)}{marker}")

# Run simulation
print(f"\n{'='*80}")
print("SIMULATION TEST")
print(f"{'='*80}")

settings = SimulationSettings()
settings.duration = 5.0
settings.dt = 0.1

controller = SimulationController(document, settings)
controller.reset()

print(f"\nRunning 50 steps...")
for step in range(50):
    try:
        controller.step()
    except Exception as e:
        print(f"Error at step {step}: {e}")
        break

print(f"\nFiring results:")
for t in document.transitions:
    count = getattr(t, 'firing_count', 0)
    ttype = t.transition_type
    status = "✅" if count > 0 else "❌"
    
    # Check if this might be a manual P-T-P
    in_arcs = [a for a in document.arcs if a.target == t]
    out_arcs = [a for a in document.arcs if a.source == t]
    is_manual = (len(in_arcs) == 1 and len(out_arcs) == 1 and 
                 not getattr(t, 'is_source', False) and 
                 not getattr(t, 'is_sink', False))
    
    marker = " [MANUAL?]" if is_manual else ""
    print(f"  {status} {t.label} ({ttype}): {count} firings{marker}")

# Check for continuous vs stochastic firing patterns
continuous = [t for t in document.transitions if t.transition_type == 'continuous']
stochastic = [t for t in document.transitions if t.transition_type == 'stochastic']

continuous_fired = sum(1 for t in continuous if getattr(t, 'firing_count', 0) > 0)
stochastic_fired = sum(1 for t in stochastic if getattr(t, 'firing_count', 0) > 0)

print(f"\n{'='*80}")
print(f"SUMMARY")
print(f"{'='*80}")
print(f"Continuous transitions: {len(continuous)} total, {continuous_fired} fired")
print(f"Stochastic transitions: {len(stochastic)} total, {stochastic_fired} fired")

if continuous_fired == 0 and stochastic_fired > 0:
    print("\n⚠️  ISSUE CONFIRMED: Only stochastic transitions fire, continuous don't fire!")
    print("\nPossible causes:")
    print("  1. Continuous transitions have zero/negative rates")
    print("  2. Continuous transitions missing input tokens")
    print("  3. Continuous transitions blocked by guards")
    print("  4. Simulation settings favor stochastic over continuous")
