#!/usr/bin/env python3
"""Test the imported Glycolysis model."""

import sys
sys.path.insert(0, 'src')

from shypn.data.canvas.document_model import DocumentModel

print("=" * 70)
print("GLYCOLYSIS MODEL TEST")
print("=" * 70)
print()

# Load the model
filepath = 'workspace/Test_flow/model/Glycolysis_Gluconeogenesis.shy'
print(f"Loading: {filepath}")
doc = DocumentModel.load_from_file(filepath)

print(f"✓ Loaded successfully")
print()

# Model Statistics
print("MODEL STATISTICS:")
print(f"  Places: {len(doc.places)}")
print(f"  Transitions: {len(doc.transitions)}")
print(f"  Arcs: {len(doc.arcs)}")
print()

# Check Guards
print("GUARD VERIFICATION:")
guards = [t.guard for t in doc.transitions]
guard_set = set(guards)
print(f"  Unique guard values: {guard_set}")

if guard_set == {1}:
    print("  ✅ All guards = 1 (scientifically correct)")
elif None in guard_set:
    print("  ❌ ERROR: Some guards are None!")
    none_count = guards.count(None)
    print(f"     {none_count}/{len(guards)} transitions have None guards")
else:
    print(f"  ⚠️  Mixed guard values: {guard_set}")
print()

# Check Initial Marking
print("INITIAL MARKING:")
total_tokens = sum(p.tokens for p in doc.places)
print(f"  Total tokens: {total_tokens}")

if total_tokens == 0:
    print("  ⚠️  No initial marking - model needs tokens to simulate")
    print("     (This is expected for KEGG imports saved before auto-marking)")
else:
    places_with_tokens = [(p.name, p.label, p.tokens) for p in doc.places if p.tokens > 0]
    print(f"  Places with tokens: {len(places_with_tokens)}")
    for name, label, tokens in places_with_tokens[:5]:
        print(f"    {name} ({label}): {tokens} tokens")
print()

# Check Kinetic Parameters
print("KINETIC PARAMETERS:")
transitions_with_rate_func = [t for t in doc.transitions 
                              if hasattr(t, 'properties') and t.properties 
                              and 'rate_function' in t.properties]

print(f"  Transitions with rate functions: {len(transitions_with_rate_func)}/{len(doc.transitions)}")

if len(transitions_with_rate_func) == len(doc.transitions):
    print("  ✅ All transitions have kinetic parameters")
else:
    print(f"  ⚠️  {len(doc.transitions) - len(transitions_with_rate_func)} transitions missing rate functions")

# Sample rate functions
print()
print("SAMPLE RATE FUNCTIONS:")
for t in doc.transitions[:5]:
    rate_func = t.properties.get('rate_function', 'N/A') if hasattr(t, 'properties') and t.properties else 'N/A'
    print(f"  {t.name} ({t.label}):")
    print(f"    Type: {t.transition_type}")
    print(f"    Guard: {t.guard}")
    print(f"    Rate function: {rate_func}")
print()

# Check Arc Connections
print("CONNECTIVITY:")
input_arcs = [arc for arc in doc.arcs if any(arc.target == t for t in doc.transitions)]
output_arcs = [arc for arc in doc.arcs if any(arc.source == t for t in doc.transitions)]
print(f"  Input arcs (Place→Transition): {len(input_arcs)}")
print(f"  Output arcs (Transition→Place): {len(output_arcs)}")

# Check for disconnected elements
disconnected_places = []
for place in doc.places:
    has_input = any(arc.target == place for arc in doc.arcs)
    has_output = any(arc.source == place for arc in doc.arcs)
    if not has_input and not has_output:
        disconnected_places.append(place)

if disconnected_places:
    print(f"  ⚠️  {len(disconnected_places)} disconnected places:")
    for p in disconnected_places[:3]:
        print(f"    {p.name} ({p.label})")
else:
    print(f"  ✅ All places connected")
print()

# Bipartite Check
print("BIPARTITE PROPERTY:")
place_to_place = []
trans_to_trans = []

for arc in doc.arcs:
    from shypn.netobjs import Place, Transition
    if isinstance(arc.source, Place) and isinstance(arc.target, Place):
        place_to_place.append(arc)
    elif isinstance(arc.source, Transition) and isinstance(arc.target, Transition):
        trans_to_trans.append(arc)

if not place_to_place and not trans_to_trans:
    print("  ✅ Valid bipartite graph (Place↔Transition only)")
else:
    if place_to_place:
        print(f"  ❌ {len(place_to_place)} Place→Place arcs found!")
    if trans_to_trans:
        print(f"  ❌ {len(trans_to_trans)} Transition→Transition arcs found!")
print()

# Overall Assessment
print("=" * 70)
print("OVERALL ASSESSMENT:")
print("=" * 70)

issues = []
if guard_set != {1}:
    issues.append("Guards not all equal to 1")
if total_tokens == 0:
    issues.append("No initial marking (needs tokens for simulation)")
if len(transitions_with_rate_func) < len(doc.transitions):
    issues.append(f"Only {len(transitions_with_rate_func)}/{len(doc.transitions)} transitions have rate functions")
if place_to_place or trans_to_trans:
    issues.append("Bipartite property violated")

if not issues:
    print("✅ MODEL IS VALID AND READY FOR SIMULATION")
    print()
    print("Notes:")
    print("  - All guards correctly set to 1")
    print("  - All transitions have kinetic parameters") 
    print("  - Structure is bipartite")
    if total_tokens == 0:
        print("  - Add initial tokens to places before simulating")
else:
    print("⚠️  MODEL HAS ISSUES:")
    for issue in issues:
        print(f"  - {issue}")
    print()
    print("Recommendations:")
    if total_tokens == 0:
        print("  1. Add initial marking (tokens) to substrate places")
    print("  2. Verify model structure before simulation")

print()
print("=" * 70)
