#!/usr/bin/env python3
"""Test source transition structural enablement."""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController
from shypn.engine.simulation.settings import SimulationSettings

model_path = "/home/simao/projetos/shypn/workspace/projects/My_Project/models/BIOMD0000000068.shy"
document = DocumentModel.load_from_file(model_path)

settings = SimulationSettings()
controller = SimulationController(document, settings)
controller.reset()

print("="*80)
print("SOURCE TRANSITION STRUCTURAL ENABLEMENT TEST")
print("="*80)

# Find source transitions
source_transitions = [t for t in document.transitions if getattr(t, 'is_source', False)]

for t in source_transitions:
    print(f"\n{t.label} (ID: {t.id}):")
    print(f"  is_source: {getattr(t, 'is_source', False)}")
    print(f"  rate: {getattr(t, 'rate', None)}")
    
    behavior = controller._get_behavior(t)
    input_arcs = behavior.get_input_arcs()
    print(f"  Input arcs: {len(input_arcs)}")
    
    # Simulate the structural enablement check from controller.py line 920-936
    structurally_enabled = True
    for arc in input_arcs:
        # Skip test/inhibitor arcs
        if hasattr(arc, 'consumes_tokens') and not arc.consumes_tokens():
            continue
        source_place = arc.source
        if source_place and source_place.tokens < arc.weight:
            structurally_enabled = False
            break
    
    print(f"  Structurally enabled: {structurally_enabled}")
    
    # Check can_fire()
    can_fire, reason = behavior.can_fire()
    print(f"  can_fire(): {can_fire} (reason: {reason})")
    
    # Check propensity
    try:
        propensity = behavior._evaluate_rate_at_enablement(controller.time)
        print(f"  Propensity: {propensity}")
    except Exception as e:
        print(f"  Propensity error: {e}")

print(f"\n{'='*80}")
print("CONCLUSION")
print(f"{'='*80}")
print("""
Source transitions:
  - Have NO input arcs
  - Are structurally enabled (no arcs to check)
  - But can_fire() returns False because no scheduled_fire_time
  - Tau-leaping should enable them based on structural check alone
  - If tau-leaping doesn't run, they never fire!
""")
