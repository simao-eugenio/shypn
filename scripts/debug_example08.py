#!/usr/bin/env python3
"""Debug Example 08 enablement check."""

import sys
import json
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.continuous_behavior import ContinuousBehavior

# Load Example 08
model_path = '/home/simao/projetos/shypn/workspace/projects/Biochemical-Examples/08_Energy_Sensing_Motif/model.shy'

print("=" * 80)
print("EXAMPLE 08 DEBUG - Inhibitor Arc Enablement")
print("=" * 80)

# Load model
with open(model_path, 'r') as f:
    data = json.load(f)

doc = DocumentModel.from_dict(data)

print(f"\nPlaces:")
for p in doc.places:
    print(f"  {p.id} ({p.name}): tokens = {p.tokens}")

print(f"\nTransitions:")
for t in doc.transitions:
    print(f"  {t.id} ({t.name}): type = {t.transition_type}, rate = {t.rate}")

print(f"\nArcs:")
from shypn.netobjs.inhibitor_arc import InhibitorArc
for arc in doc.arcs:
    arc_type = "INHIBITOR" if isinstance(arc, InhibitorArc) else "normal"
    source_name = arc.source.name if hasattr(arc.source, 'name') else arc.source.id
    target_name = arc.target.name if hasattr(arc.target, 'name') else arc.target.id
    weight = arc.weight if hasattr(arc, 'weight') else 1
    print(f"  {arc.id}: {source_name} → {target_name} ({arc_type}, weight={weight})")

# Check T1 enablement
print("\n" + "=" * 80)
print("T1 (PFK-1) ENABLEMENT CHECK")
print("=" * 80)

t1 = next(t for t in doc.transitions if t.id == "T1")
behavior_t1 = ContinuousBehavior(t1, doc)

print(f"\nInput arcs to T1:")
input_arcs = behavior_t1.get_input_arcs()
for arc in input_arcs:
    arc_type = type(arc).__name__
    source_name = arc.source.name if hasattr(arc.source, 'name') else "?"
    print(f"  {arc.id}: {source_name} ({arc_type}, weight={arc.weight})")
    if isinstance(arc, InhibitorArc):
        print(f"    Source tokens: {arc.source.tokens}")
        print(f"    Threshold: {arc.weight}")
        print(f"    Should block: {arc.source.tokens >= arc.weight}")

enabled, reason = behavior_t1.can_fire()
print(f"\nT1 enabled: {enabled}")
print(f"Reason: {reason}")

if enabled:
    print("❌ ERROR: T1 should be DISABLED (ATP=3.0 >= 2.5)")
else:
    print("✅ CORRECT: T1 is disabled")

# Check T2 enablement
print("\n" + "=" * 80)
print("T2 (PK) ENABLEMENT CHECK")
print("=" * 80)

t2 = next(t for t in doc.transitions if t.id == "T2")
behavior_t2 = ContinuousBehavior(t2, doc)

print(f"\nInput arcs to T2:")
input_arcs = behavior_t2.get_input_arcs()
for arc in input_arcs:
    arc_type = type(arc).__name__
    source_name = arc.source.name if hasattr(arc.source, 'name') else "?"
    print(f"  {arc.id}: {source_name} ({arc_type}, weight={arc.weight})")
    if isinstance(arc, InhibitorArc):
        print(f"    Source tokens: {arc.source.tokens}")
        print(f"    Threshold: {arc.weight}")
        print(f"    Should block: {arc.source.tokens >= arc.weight}")

enabled, reason = behavior_t2.can_fire()
print(f"\nT2 enabled: {enabled}")
print(f"Reason: {reason}")

if enabled:
    print("❌ ERROR: T2 should be DISABLED (ATP=3.0 >= 2.0)")
else:
    print("✅ CORRECT: T2 is disabled")
