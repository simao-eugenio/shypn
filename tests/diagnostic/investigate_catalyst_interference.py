#!/usr/bin/env python3
"""
Investigation: Catalyst Places Interfering with Simulation Firing

Refinements to investigate:
1. KEGG auto-load WITHOUT catalysts works fine
2. KEGG auto-load WITH catalysts has firing issues
3. Evidence: Normal places and catalyst places are interfering in scheduling
4. Without catalyst metadata, heuristic parameters are poor

This suggests the catalyst places are being treated as normal places
during simulation firing checks, blocking transitions from firing.
"""

import json
from pathlib import Path
from collections import defaultdict

print("=" * 80)
print("INVESTIGATING CATALYST INTERFERENCE IN SIMULATION")
print("=" * 80)

# Load a KEGG model with catalysts
model_file = Path('/home/simao/projetos/shypn/workspace/projects/models/hsa00010.shy')

if not model_file.exists():
    print(f"\n❌ Model file not found: {model_file}")
    exit(1)

with open(model_file) as f:
    data = json.load(f)

print(f"\n📊 Model Statistics:")
print("-" * 80)
print(f"Total places: {len(data['places'])}")
print(f"Total transitions: {len(data['transitions'])}")
print(f"Total arcs: {len(data['arcs'])}")

# Separate catalyst and regular places
catalyst_places = [p for p in data['places'] if p.get('is_catalyst', False)]
regular_places = [p for p in data['places'] if not p.get('is_catalyst', False)]

print(f"\nPlace Breakdown:")
print(f"  Regular places: {len(regular_places)}")
print(f"  Catalyst places: {len(catalyst_places)}")

# ============================================================================
# ISSUE 1: Check if catalysts have input arcs (they shouldn't consume!)
# ============================================================================

print("\n" + "=" * 80)
print("ISSUE 1: CATALYST PLACES AS ARC SOURCES (SHOULD ONLY BE TEST ARCS)")
print("=" * 80)

catalyst_ids = {p['id'] for p in catalyst_places}

# Check regular arcs from catalysts
regular_arcs_from_catalysts = []
for arc in data['arcs']:
    if 'arc_type' in arc and arc['arc_type'] == 'test':
        continue  # Skip test arcs (these are OK)
    
    # Check if source is a catalyst
    source_id = arc.get('source')
    if source_id in catalyst_ids:
        regular_arcs_from_catalysts.append(arc)

print(f"\n🔍 Regular arcs from catalyst places: {len(regular_arcs_from_catalysts)}")

if regular_arcs_from_catalysts:
    print("\n⚠️  PROBLEM: Catalysts are used as arc sources in regular (consuming) arcs!")
    print("   This causes simulation to check catalyst token counts before firing.")
    print("   If catalyst has 0 tokens, transitions will be blocked!")
    
    print("\n   Examples:")
    for arc in regular_arcs_from_catalysts[:5]:
        source_id = arc['source']
        target_id = arc['target']
        arc_type = arc.get('arc_type', 'normal')
        weight = arc.get('weight', 1)
        print(f"     {source_id} --[{arc_type}, w={weight}]--> {target_id}")
else:
    print("✅ No regular arcs from catalyst places")

# Check test arcs from catalysts
test_arcs_from_catalysts = [arc for arc in data['arcs'] 
                            if arc.get('arc_type') == 'test' 
                            and arc.get('source') in catalyst_ids]

print(f"\n🧪 Test arcs from catalyst places: {len(test_arcs_from_catalysts)}")

if test_arcs_from_catalysts:
    print("✅ Correct: Catalysts use test arcs (non-consuming)")
    print("\n   Examples:")
    for arc in test_arcs_from_catalysts[:5]:
        source_id = arc['source']
        target_id = arc['target']
        print(f"     {source_id} ==TEST==> {target_id}")

# ============================================================================
# ISSUE 2: Check catalyst token counts
# ============================================================================

print("\n\n" + "=" * 80)
print("ISSUE 2: CATALYST PLACE TOKEN COUNTS")
print("=" * 80)

print("\n💰 Token Distribution:")
print("-" * 80)

catalyst_tokens = defaultdict(int)
for p in catalyst_places:
    tokens = p.get('tokens', 0)
    catalyst_tokens[tokens] += 1

print("\nCatalyst places by token count:")
for tokens in sorted(catalyst_tokens.keys()):
    count = catalyst_tokens[tokens]
    print(f"  {tokens} tokens: {count} places")

zero_token_catalysts = [p for p in catalyst_places if p.get('tokens', 0) == 0]

if zero_token_catalysts:
    print(f"\n⚠️  WARNING: {len(zero_token_catalysts)} catalyst places have 0 tokens!")
    print("   If these are used in regular (consuming) arcs, they will block firing!")
    print("\n   Examples:")
    for p in zero_token_catalysts[:5]:
        print(f"     {p['id']}: {p.get('name', 'unnamed')} (tokens={p.get('tokens', 0)})")

# ============================================================================
# ISSUE 3: Check if catalysts are connected to transitions correctly
# ============================================================================

print("\n\n" + "=" * 80)
print("ISSUE 3: CATALYST-TRANSITION CONNECTIVITY")
print("=" * 80)

# Build connectivity map
catalyst_connections = defaultdict(list)

for arc in data['arcs']:
    source_id = arc.get('source')
    target_id = arc.get('target')
    arc_type = arc.get('arc_type', 'normal')
    
    if source_id in catalyst_ids:
        # Catalyst → something
        catalyst_connections[source_id].append({
            'type': arc_type,
            'direction': 'output',
            'target': target_id,
            'weight': arc.get('weight', 1)
        })

print(f"\n🔗 Catalyst Connectivity Analysis:")
print("-" * 80)

catalysts_with_no_connections = [p['id'] for p in catalyst_places 
                                 if p['id'] not in catalyst_connections]

print(f"\nCatalysts with connections: {len(catalyst_connections)}")
print(f"Catalysts with NO connections: {len(catalysts_with_no_connections)}")

if catalysts_with_no_connections:
    print("\n⚠️  Disconnected catalysts (not affecting any transition):")
    for cat_id in catalysts_with_no_connections[:10]:
        cat_place = next(p for p in catalyst_places if p['id'] == cat_id)
        print(f"     {cat_id}: {cat_place.get('name', 'unnamed')}")

# Check connection types
connection_stats = {'test': 0, 'normal': 0, 'inhibitor': 0}

for cat_id, connections in catalyst_connections.items():
    for conn in connections:
        conn_type = conn['type']
        connection_stats[conn_type] = connection_stats.get(conn_type, 0) + 1

print(f"\n📈 Connection Type Statistics:")
for conn_type, count in sorted(connection_stats.items()):
    print(f"  {conn_type}: {count}")

if connection_stats.get('normal', 0) > 0:
    print(f"\n⚠️  CRITICAL ISSUE: {connection_stats['normal']} normal (consuming) arcs from catalysts!")
    print("   This means simulation will check catalyst tokens and consume them.")
    print("   Expected: ALL catalyst arcs should be 'test' type (non-consuming).")

# ============================================================================
# ISSUE 4: Check metadata for heuristic parameters
# ============================================================================

print("\n\n" + "=" * 80)
print("ISSUE 4: CATALYST METADATA FOR HEURISTIC PARAMETERS")
print("=" * 80)

print("\n🏷️  Metadata Analysis:")
print("-" * 80)

metadata_stats = {
    'has_kegg_id': 0,
    'has_kegg_reaction': 0,
    'has_ec_numbers': 0,
    'has_enzyme_name': 0,
    'is_marked_catalyst': 0,
    'no_metadata': 0
}

catalyst_metadata_examples = []

for p in catalyst_places:
    metadata = p.get('metadata', {})
    
    if not metadata:
        metadata_stats['no_metadata'] += 1
        continue
    
    if 'kegg_id' in metadata or 'kegg_entry_id' in metadata:
        metadata_stats['has_kegg_id'] += 1
    
    if 'catalyzes_reaction' in metadata or 'kegg_reaction' in metadata:
        metadata_stats['has_kegg_reaction'] += 1
    
    if 'ec_numbers' in metadata:
        metadata_stats['has_ec_numbers'] += 1
    
    if 'is_enzyme' in metadata or 'is_catalyst' in metadata:
        metadata_stats['is_marked_catalyst'] += 1
    
    # Collect example
    if len(catalyst_metadata_examples) < 3:
        catalyst_metadata_examples.append((p['id'], metadata))

print("\nCatalyst Metadata Statistics:")
for key, value in sorted(metadata_stats.items()):
    print(f"  {key}: {value}/{len(catalyst_places)}")

print("\n📝 Example Catalyst Metadata:")
for place_id, metadata in catalyst_metadata_examples:
    print(f"\n{place_id}:")
    for key, value in list(metadata.items())[:8]:
        print(f"  {key}: {value}")

# Check if reaction codes are available
reactions_with_catalysts = defaultdict(list)

for p in catalyst_places:
    metadata = p.get('metadata', {})
    reaction = metadata.get('catalyzes_reaction') or metadata.get('kegg_reaction')
    if reaction:
        reactions_with_catalysts[reaction].append(p['id'])

print(f"\n🧪 Reactions with Catalyst Information:")
print(f"  Total reactions referenced: {len(reactions_with_catalysts)}")

if reactions_with_catalysts:
    print("\n  Examples:")
    for reaction, catalyst_list in list(reactions_with_catalysts.items())[:5]:
        print(f"    {reaction}: {len(catalyst_list)} catalyst(s)")
else:
    print("\n⚠️  NO reaction codes found in catalyst metadata!")
    print("   This prevents linking catalysts to reaction parameters.")

# ============================================================================
# FINAL RECOMMENDATIONS
# ============================================================================

print("\n\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)

issues_found = []

if regular_arcs_from_catalysts:
    issues_found.append({
        'priority': 'CRITICAL',
        'issue': 'Catalysts used in consuming arcs',
        'impact': 'Blocks transitions from firing (simulation deadlock)',
        'fix': 'Convert all catalyst arcs to test arcs (arc_type="test")'
    })

if zero_token_catalysts:
    issues_found.append({
        'priority': 'HIGH',
        'issue': f'{len(zero_token_catalysts)} catalysts have 0 tokens',
        'impact': 'If used in consuming arcs, blocks firing',
        'fix': 'Set initial_marking=1 for all catalysts OR ensure test arcs'
    })

if connection_stats.get('normal', 0) > 0:
    issues_found.append({
        'priority': 'CRITICAL',
        'issue': 'Normal arcs from catalysts consume tokens',
        'impact': 'Simulation treats catalysts as regular places',
        'fix': 'Mark all catalyst arcs with arc_type="test" during import'
    })

if not reactions_with_catalysts:
    issues_found.append({
        'priority': 'MEDIUM',
        'issue': 'Missing reaction codes in catalyst metadata',
        'impact': 'Cannot link catalysts to heuristic parameters',
        'fix': 'Store reaction code in metadata during KEGG import'
    })

if issues_found:
    print("\n🚨 Issues Found:\n")
    for i, issue in enumerate(issues_found, 1):
        print(f"{i}. [{issue['priority']}] {issue['issue']}")
        print(f"   Impact: {issue['impact']}")
        print(f"   Fix: {issue['fix']}")
        print()
else:
    print("\n✅ No critical issues found!")

print("=" * 80)
