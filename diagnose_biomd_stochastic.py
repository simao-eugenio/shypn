#!/usr/bin/env python3
"""Diagnostic script for BIOMD0000000061 stochastic transitions."""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController
from shypn.engine.simulation.settings import SimulationSettings

print("="*80)
print("BIOMD0000000061 Stochastic Diagnostics")
print("="*80)

# Load the model
model_path = "/home/simao/projetos/shypn/workspace/projects/My_Project/models/BIOMD0000000061.shy"
print(f"\n📂 Loading: {model_path}")

try:
    document = DocumentModel.load_from_file(model_path)
    print(f"✅ Model loaded successfully")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    sys.exit(1)

# Analyze transitions
print(f"\n{'='*80}")
print("TRANSITION ANALYSIS")
print(f"{'='*80}")

all_transitions = list(document.transitions)
print(f"\nTotal transitions: {len(all_transitions)}")

by_type = {}
for t in all_transitions:
    ttype = t.transition_type
    by_type.setdefault(ttype, []).append(t)

print(f"\nBy type:")
for ttype, transitions in sorted(by_type.items()):
    print(f"  {ttype}: {len(transitions)}")

# Check stochastic transitions specifically
stochastic = by_type.get('stochastic', [])
print(f"\n{'-'*80}")
print(f"STOCHASTIC TRANSITIONS ({len(stochastic)})")
print(f"{'-'*80}")

for t in stochastic:
    rate = getattr(t, 'rate', None)
    is_source = getattr(t, 'is_source', False)
    is_sink = getattr(t, 'is_sink', False)
    
    # Count arcs
    in_arcs = [a for a in document.arcs if a.target == t]
    out_arcs = [a for a in document.arcs if a.source == t]
    
    print(f"\n{t.label} (ID: {t.id})")
    print(f"  Rate: {rate}")
    print(f"  Source: {is_source}, Sink: {is_sink}")
    print(f"  Input arcs: {len(in_arcs)}, Output arcs: {len(out_arcs)}")
    
    # Show connected places
    if in_arcs:
        for arc in in_arcs:
            place = arc.source
            print(f"    ← {place.label} (tokens={place.tokens})")
    if out_arcs:
        for arc in out_arcs:
            place = arc.target
            print(f"    → {place.label} (tokens={place.tokens})")

# Set up simulation
print(f"\n{'='*80}")
print("SIMULATION SETUP")
print(f"{'='*80}")

settings = SimulationSettings()
settings.duration = 5.0
settings.dt = 0.1
print(f"Duration: {settings.duration}s")
print(f"Time step: {settings.dt}s")
print(f"Use tau-leaping: {getattr(settings, 'use_tau_leaping', 'NOT SET')}")

controller = SimulationController(document, settings)
controller.reset()
print(f"✅ Controller initialized")

# Check behaviors for stochastic transitions
print(f"\n{'-'*80}")
print("BEHAVIOR ANALYSIS")
print(f"{'-'*80}")

for t in stochastic:
    behavior = controller._get_behavior(t)
    print(f"\n{t.label}:")
    print(f"  Behavior class: {type(behavior).__name__}")
    print(f"  Behavior.rate: {getattr(behavior, 'rate', 'NOT SET')}")
    print(f"  Has rate function: {getattr(behavior, 'has_rate_function', False)}")
    
    # Try to evaluate propensity
    try:
        propensity = behavior._evaluate_rate_at_enablement(controller.time)
        print(f"  Propensity: {propensity:.6f}")
        if propensity <= 0:
            print(f"  ⚠️  WARNING: Zero or negative propensity!")
    except Exception as e:
        print(f"  ❌ Error evaluating propensity: {e}")

# Run simulation
print(f"\n{'='*80}")
print("RUNNING SIMULATION")
print(f"{'='*80}")

print(f"\nInitial token counts:")
for p in list(document.places)[:5]:  # Show first 5 places
    print(f"  {p.label}: {p.tokens:.2f}")

print(f"\nRunning 50 steps...")
for step in range(50):
    success = controller.step()
    if not success:
        print(f"Simulation stopped at step {step}")
        break

print(f"\nFinal time: {controller.time:.3f}s")

# Check firing counts
print(f"\n{'-'*80}")
print("FIRING RESULTS")
print(f"{'-'*80}")

for t in stochastic:
    count = getattr(t, 'firing_count', 0)
    status = "✅" if count > 0 else "❌"
    print(f"{status} {t.label}: {count} firings")

print(f"\nFinal token counts:")
for p in list(document.places)[:5]:
    print(f"  {p.label}: {p.tokens:.2f}")

# Summary
print(f"\n{'='*80}")
print("SUMMARY")
print(f"{'='*80}")

total_firings = sum(getattr(t, 'firing_count', 0) for t in stochastic)
if total_firings == 0:
    print(f"❌ NO stochastic transitions fired!")
    print(f"\nPossible causes:")
    print(f"  1. Propensities are zero (check rates)")
    print(f"  2. Transitions not structurally enabled (missing input tokens)")
    print(f"  3. Tau-leaping not working properly")
else:
    print(f"✅ {total_firings} total stochastic firings occurred")
