#!/usr/bin/env python3
"""Deep dive into why transitions don't fire in BIOMD0000000068."""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController
from shypn.engine.simulation.settings import SimulationSettings

model_path = "/home/simao/projetos/shypn/workspace/projects/My_Project/models/BIOMD0000000068.shy"
document = DocumentModel.load_from_file(model_path)

print("="*80)
print("TOKEN AVAILABILITY ANALYSIS")
print("="*80)

# Check all places
print("\nAll places and their tokens:")
for p in document.places:
    print(f"  {p.label}: {p.tokens:.2f} tokens")

print(f"\n{'='*80}")
print("ENABLEMENT CHECK")
print(f"{'='*80}")

settings = SimulationSettings()
settings.duration = 5.0
settings.dt = 0.1

controller = SimulationController(document, settings)
controller.reset()

print("\nChecking each transition:")
for t in document.transitions:
    behavior = controller._get_behavior(t)
    
    # Get connected places
    in_arcs = [a for a in document.arcs if a.target == t]
    out_arcs = [a for a in document.arcs if a.source == t]
    
    print(f"\n{t.label} ({t.transition_type}):")
    
    # Check input places
    if in_arcs:
        print(f"  Input places:")
        for arc in in_arcs:
            place = arc.source
            print(f"    {place.label}: {place.tokens:.2f} tokens (need {arc.weight})")
            if place.tokens < arc.weight:
                print(f"      ⚠️  BLOCKED: Not enough tokens!")
            if place.tokens <= 0:
                print(f"      ❌ EMPTY: Zero tokens!")
    else:
        print(f"  Input places: None (source transition)")
    
    # Check rate/propensity for stochastic
    if t.transition_type == 'stochastic':
        try:
            propensity = behavior._evaluate_rate_at_enablement(controller.time)
            print(f"  Propensity: {propensity:.6f}")
            if propensity <= 0:
                print(f"    ❌ ZERO PROPENSITY: Won't fire!")
                
                # Try to explain why
                if hasattr(behavior, 'rate_function_expr') and behavior.rate_function_expr:
                    print(f"    Formula: {behavior.rate_function_expr[:80]}")
                    # Check if any input place has zero tokens
                    zero_inputs = [arc.source.label for arc in in_arcs if arc.source.tokens == 0]
                    if zero_inputs:
                        print(f"    Reason: Input place(s) with zero tokens: {', '.join(zero_inputs)}")
        except Exception as e:
            print(f"  Error evaluating propensity: {e}")
    
    # Check if enabled
    can_fire = controller._is_transition_enabled(t)
    print(f"  Enabled: {can_fire}")

print(f"\n{'='*80}")
print("ROOT CAUSE")
print(f"{'='*80}")

print("""
The issue: Most places start with ZERO tokens!

BIOMD0000000068 models amino acid biosynthesis:
  - Homoserine (0 tokens) → needs to be supplied by Source_Hser
  - But Source_Hser also has rate=0.0 (sink/source transitions not properly initialized)
  - Only Sink_Phi works because Inorganic phosphate starts with 10000 tokens

Solutions:
  1. Fix source transition rates (Source_Hser rate should be > 0)
  2. Set initial tokens on intermediate metabolites
  3. Change transition types to continuous for better behavior
""")
