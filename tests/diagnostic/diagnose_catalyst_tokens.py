#!/usr/bin/env python3
"""
Final Investigation: Why Catalysts Interfere with Simulation

Evidence:
1. Model WITHOUT catalysts: Simulation works
2. Model WITH catalysts: Simulation has issues
3. Test arcs ARE present and properly formatted
4. Catalysts have 0 tokens initially

Hypothesis: The simulation is checking catalyst token counts even though
they're connected via test arcs (non-consuming).
"""

import json
from pathlib import Path
from collections import defaultdict

print("=" * 80)
print("FINAL INVESTIGATION: CATALYST SIMULATION INTERFERENCE")
print("=" * 80)

# Load model WITH catalysts
file_with_catalysts = Path('/home/simao/projetos/shypn/workspace/projects/models/hsa00010.shy')

with open(file_with_catalysts) as f:
    data_with = json.load(f)

# Load model WITHOUT catalysts
file_without_catalysts = Path('/home/simao/projetos/shypn/workspace/projects/Interactive/models/hsa00010.shy')

with open(file_without_catalysts) as f:
    data_without = json.load(f)

print("\n📊 Model Comparison:")
print("-" * 80)
print(f"{'':30} Without Catalysts  With Catalysts")
print(f"{'Places:':<30} {len(data_without['places']):>16}  {len(data_with['places']):>14}")
print(f"{'Transitions:':<30} {len(data_without['transitions']):>16}  {len(data_with['transitions']):>14}")
print(f"{'Arcs:':<30} {len(data_without['arcs']):>16}  {len(data_with['arcs']):>14}")

# Count by arc type
without_arc_types = {}
for arc in data_without['arcs']:
    arc_type = arc.get('arc_type', 'normal')
    without_arc_types[arc_type] = without_arc_types.get(arc_type, 0) + 1

with_arc_types = {}
for arc in data_with['arcs']:
    arc_type = arc.get('arc_type', 'normal')
    with_arc_types[arc_type] = with_arc_types.get(arc_type, 0) + 1

print(f"\n{'Arc Types:':<30}")
for arc_type in sorted(set(without_arc_types.keys()) | set(with_arc_types.keys())):
    without_count = without_arc_types.get(arc_type, 0)
    with_count = with_arc_types.get(arc_type, 0)
    print(f"  {arc_type:<28} {without_count:>16}  {with_count:>14}")

# ============================================================================
# Check Transition Enablement
# ============================================================================

print("\n\n" + "=" * 80)
print("TRANSITION ENABLEMENT ANALYSIS")
print("=" * 80)

def analyze_transition_enablement(data, label):
    print(f"\n{label}:")
    print("-" * 80)
    
    # Build lookup tables
    places_by_id = {p['id']: p for p in data['places']}
    transitions_by_id = {t['id']: t for t in data['transitions']}
    
    # Group arcs by target (transition)
    input_arcs_by_transition = defaultdict(list)
    
    for arc in data['arcs']:
        if arc.get('target_type') == 'transition':
            transition_id = arc.get('target_id')
            input_arcs_by_transition[transition_id].append(arc)
    
    # Check each transition
    enabled_count = 0
    disabled_count = 0
    disabled_by_catalyst = 0
    
    for trans_id, transition in transitions_by_id.items():
        input_arcs = input_arcs_by_transition.get(trans_id, [])
        
        if not input_arcs:
            # Source transition
            enabled_count += 1
            continue
        
        # Check if all input arcs are satisfied
        enabled = True
        blocked_by = []
        
        for arc in input_arcs:
            arc_type = arc.get('arc_type', 'normal')
            source_id = arc.get('source_id')
            place = places_by_id.get(source_id)
            
            if not place:
                continue
            
            tokens = place.get('tokens', 0)
            weight = arc.get('weight', 1)
            is_catalyst = place.get('is_catalyst', False)
            
            if arc_type == 'test':
                # Test arcs: only check presence (tokens >= 1)
                if tokens < 1:
                    enabled = False
                    blocked_by.append(f"{source_id} (test, {tokens} < 1, catalyst={is_catalyst})")
            elif arc_type == 'normal':
                # Normal arcs: check sufficient tokens
                if tokens < weight:
                    enabled = False
                    blocked_by.append(f"{source_id} (normal, {tokens} < {weight}, catalyst={is_catalyst})")
        
        if enabled:
            enabled_count += 1
        else:
            disabled_count += 1
            # Check if disabled by a catalyst
            if any('catalyst=True' in b for b in blocked_by):
                disabled_by_catalyst += 1
    
    print(f"  Transitions: {len(transitions_by_id)}")
    print(f"  Enabled: {enabled_count}")
    print(f"  Disabled: {disabled_count}")
    if disabled_by_catalyst > 0:
        print(f"  ⚠️  Disabled by catalyst: {disabled_by_catalyst}")

analyze_transition_enablement(data_without, "Model WITHOUT Catalysts")
analyze_transition_enablement(data_with, "Model WITH Catalysts")

# ============================================================================
# Root Cause Analysis
# ============================================================================

print("\n\n" + "=" * 80)
print("ROOT CAUSE ANALYSIS")
print("=" * 80)

# Check catalyst initial markings
catalysts = [p for p in data_with['places'] if p.get('is_catalyst', False)]
catalyst_tokens = {}
for cat in catalysts:
    tokens = cat.get('tokens', 0)
    initial = cat.get('initial_marking', 0)
    catalyst_tokens[(tokens, initial)] = catalyst_tokens.get((tokens, initial), 0) + 1

print("\nCatalyst Token Distribution:")
print("-" * 80)
print(f"{'Tokens':<10} {'Initial':<10} {'Count':<10}")
for (tokens, initial), count in sorted(catalyst_tokens.items()):
    print(f"{tokens:<10} {initial:<10} {count:<10}")

# Check test arcs from catalysts
test_arcs = [a for a in data_with['arcs'] if a.get('arc_type') == 'test']
catalyst_ids = {c['id'] for c in catalysts}
test_arcs_from_catalysts = [a for a in test_arcs if a.get('source_id') in catalyst_ids]

print(f"\nTest Arcs from Catalysts: {len(test_arcs_from_catalysts)}/{len(test_arcs)}")

# Check if test arcs require tokens
print("\nTest Arc Semantics Check:")
print("-" * 80)
print("Test arcs should:")
print("  ✓ Check for presence (tokens >= 1)")
print("  ✓ NOT consume tokens (consumes=False)")
print("  ✓ Allow transition to fire if catalyst has ≥ 1 token")

if test_arcs_from_catalysts:
    sample = test_arcs_from_catalysts[0]
    print(f"\nSample test arc:")
    print(f"  source_id: {sample.get('source_id')}")
    print(f"  target_id: {sample.get('target_id')}")
    print(f"  consumes: {sample.get('consumes', True)}")
    print(f"  weight: {sample.get('weight', 1)}")
    print(f"  arc_type: {sample.get('arc_type')}")
    
    source_place = next((p for p in data_with['places'] if p['id'] == sample.get('source_id')), None)
    if source_place:
        print(f"\nSource place ({sample.get('source_id')}):")
        print(f"  tokens: {source_place.get('tokens', 0)}")
        print(f"  initial_marking: {source_place.get('initial_marking', 0)}")
        print(f"  is_catalyst: {source_place.get('is_catalyst', False)}")

# ============================================================================
# CONCLUSION
# ============================================================================

print("\n\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

print("""
CRITICAL ISSUE IDENTIFIED:
-------------------------
All catalyst places have:
  • tokens = 0
  • initial_marking = 0

Test arcs check for presence (tokens >= 1), so:
  • If catalyst has 0 tokens → test arc fails
  • Transition cannot fire even if substrates available

SOLUTION:
---------
During KEGG import with create_enzyme_places=True:
  1. Set catalyst place initial_marking = 1
  2. Set catalyst place tokens = 1
  
This represents: "Enzyme is present and available to catalyze"

CODE LOCATION:
-------------
src/shypn/importer/kegg/pathway_converter.py
Lines ~222-224 and ~279-281:

  place.tokens = 1          # ← ADD THIS
  place.initial_marking = 1 # ← ADD THIS

This makes catalysts "available" without being consumed.
""")

print("=" * 80)
