#!/usr/bin/env python3
"""Diagnose why hsa00010.shy with catalysts doesn't fire all transitions."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs.test_arc import TestArc

# Load the model
model_path = "workspace/projects/Interactive/models/hsa00010.shy"
print(f"Loading model: {model_path}")
print("=" * 70)

doc = DocumentModel.load_from_file(model_path)

print(f"\nModel loaded:")
print(f"  Places: {len(doc.places)}")
print(f"  Transitions: {len(doc.transitions)}")
print(f"  Arcs: {len(doc.arcs)}")

# Count arc types
arc_types = {}
test_arcs = []
for arc in doc.arcs:
    arc_type = type(arc).__name__
    arc_types[arc_type] = arc_types.get(arc_type, 0) + 1
    if isinstance(arc, TestArc):
        test_arcs.append(arc)

print(f"\nArc types (Python classes):")
for atype, count in sorted(arc_types.items()):
    print(f"  {atype}: {count}")

print(f"\nTest arcs found: {len(test_arcs)}")

if len(test_arcs) == 0:
    print("\n❌ PROBLEM: No TestArc objects found!")
    print("   The arcs are marked as arc_type='test' but loaded as Arc objects")
    print("   This means test arcs are consuming tokens like normal arcs!")
else:
    print(f"\n✅ Test arcs properly loaded as TestArc objects")

# Check enzyme places
enzyme_places = []
for arc in test_arcs:
    if arc.source not in enzyme_places:
        enzyme_places.append(arc.source)

print(f"\nEnzyme places (sources of test arcs): {len(enzyme_places)}")
if enzyme_places:
    print("\nFirst 5 enzyme places:")
    for i, place in enumerate(enzyme_places[:5]):
        print(f"  {place.id} ({place.label}): tokens={place.tokens}, initial={place.initial_marking}")
        # Check if enzyme has tokens
        if place.tokens == 0:
            print(f"    ⚠️  WARNING: Enzyme has NO tokens!")

# Check transitions with test arcs
transitions_with_catalysts = set()
for arc in test_arcs:
    transitions_with_catalysts.add(arc.target)

print(f"\nTransitions with catalyst test arcs: {len(transitions_with_catalysts)}")

# Check if these transitions have substrate arcs too
print("\nChecking transition enablement (first 5):")
for i, transition in enumerate(list(transitions_with_catalysts)[:5]):
    print(f"\n  Transition {transition.id} ({transition.label}):")
    
    # Get all input arcs
    input_arcs = [arc for arc in doc.arcs if arc.target == transition]
    print(f"    Input arcs: {len(input_arcs)}")
    
    test_count = 0
    normal_count = 0
    for arc in input_arcs:
        if isinstance(arc, TestArc):
            test_count += 1
            print(f"      - Test arc from {arc.source.id}: tokens={arc.source.tokens}, weight={arc.weight}, enabled={arc.source.tokens >= arc.weight}")
        else:
            normal_count += 1
            print(f"      - Normal arc from {arc.source.id}: tokens={arc.source.tokens}, weight={arc.weight}, enabled={arc.source.tokens >= arc.weight}")
    
    print(f"    Summary: {test_count} test arcs, {normal_count} normal arcs")
    
    # Check overall enablement
    all_enabled = all(arc.source.tokens >= arc.weight for arc in input_arcs)
    print(f"    Overall enabled: {all_enabled}")

# Check if arc.consumes_tokens() works
print("\n" + "=" * 70)
print("Testing consumes_tokens() method:")
if test_arcs:
    test_arc = test_arcs[0]
    print(f"  Test arc {test_arc.id}: consumes_tokens() = {test_arc.consumes_tokens()}")
    if test_arc.consumes_tokens():
        print("  ❌ PROBLEM: Test arc says it consumes tokens!")
    else:
        print("  ✅ Test arc correctly reports it doesn't consume")

# Final diagnosis
print("\n" + "=" * 70)
print("DIAGNOSIS:")
print("=" * 70)

if len(test_arcs) == 0:
    print("\n❌ CRITICAL BUG: Test arcs not loaded as TestArc class!")
    print("   - File has arc_type='test' but Arc.from_dict() creates Arc objects")
    print("   - This causes catalysts to be CONSUMED like substrates")
    print("   - Transitions will not fire once enzyme tokens are depleted")
    print("\nFIX: Check Arc.from_dict() to ensure it creates TestArc for arc_type='test'")
elif any(place.tokens == 0 for place in enzyme_places):
    print("\n❌ PROBLEM: Some enzyme places have zero tokens!")
    print("   - Enzymes should start with tokens (usually initial_marking=1)")
    print("   - Check model initialization")
else:
    print("\n✅ Test arcs loaded correctly and enzymes have tokens")
    print("   If transitions still don't fire, check:")
    print("   - Substrate places have tokens")
    print("   - Rate functions are valid")
    print("   - Simulation controller handles test arcs correctly")
