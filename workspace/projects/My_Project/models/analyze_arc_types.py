#!/usr/bin/env python3
"""
Analyze arc types detection in arcs_types.shy model.
Tests detection of: normal, inhibitor, test, signal_flow, straight, curved.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# Load the model
model_path = Path(__file__).parent / "arcs_types.shy"
print(f"Analyzing: {model_path}\n")
print("=" * 80)

if not model_path.exists():
    print(f"ERROR: Model file not found: {model_path}")
    sys.exit(1)

with open(model_path, 'r') as f:
    model = json.load(f)

# Extract arc information
arcs = model.get('arcs', [])
places_dict = {p['id']: p for p in model.get('places', [])}
transitions_dict = {t['id']: t for t in model.get('transitions', [])}
places = {p['id']: p.get('name', f"P{p['id']}") for p in model.get('places', [])}
transitions = {t['id']: t.get('name', f"T{t['id']}") for t in model.get('transitions', [])}

print(f"\nModel Statistics:")
print(f"  Places: {len(places)}")
print(f"    Signal places: {sum(1 for p in model.get('places', []) if p.get('is_signal_place', False))}")
print(f"  Transitions: {len(transitions)}")
print(f"  Arcs: {len(arcs)}")
print("=" * 80)

# Analyze arcs by type
arc_types = defaultdict(list)
geometry_types = defaultdict(int)

print("\n\nDetailed Arc Analysis:\n")
print(f"{'ID':<6} {'Source':<20} {'Target':<20} {'Type':<20} {'Effective':<15} {'Geometry':<10} {'Weight':<8}")
print("-" * 100)

for arc in arcs:
    arc_id = arc.get('id', 'N/A')
    source_id = arc.get('source_id')
    target_id = arc.get('target_id')
    arc_type = arc.get('arc_type', 'normal')
    weight = arc.get('weight', 1.0)
    
    # Get geometry type
    control_points = arc.get('control_points', [])
    geometry = 'straight' if len(control_points) == 0 else 'curved'
    
    # Determine effective arc type (signal place detection)
    effective_type = arc_type
    source_place = places_dict.get(source_id)
    target_place = places_dict.get(target_id)
    source_is_signal = source_place and source_place.get('is_signal_place', False)
    target_is_signal = target_place and target_place.get('is_signal_place', False)
    
    if (source_is_signal or target_is_signal) and arc_type == 'normal':
        effective_type = 'signal_flow'
    
    # Determine source/target names
    if source_id in places:
        source_name = places[source_id]
        direction = "P→T"
    elif source_id in transitions:
        source_name = transitions[source_id]
        direction = "T→P"
    else:
        source_name = f"Unknown({source_id})"
        direction = "?"
    
    if target_id in places:
        target_name = places[target_id]
    elif target_id in transitions:
        target_name = transitions[target_id]
    else:
        target_name = f"Unknown({target_id})"
    
    # Store arc information
    arc_info = {
        'id': arc_id,
        'source': source_name,
        'target': target_name,
        'type': arc_type,
        'effective_type': effective_type,
        'geometry': geometry,
        'weight': weight,
        'direction': direction,
        'control_points': len(control_points)
    }
    
    arc_types[effective_type].append(arc_info)
    geometry_types[geometry] += 1
    
    # Print row
    print(f"{arc_id:<6} {source_name:<20} {target_name:<20} {arc_type:<20} {effective_type:<15} {geometry:<10} {weight:<8.2f}")

print("=" * 100)

# Summary statistics
print("\n\nArc Type Distribution (Effective):\n")
for arc_type, arcs_list in sorted(arc_types.items()):
    print(f"  {arc_type:<15}: {len(arcs_list):>3} arcs")

print(f"\nGeometry Distribution:")
for geom, count in sorted(geometry_types.items()):
    print(f"  {geom:<15}: {count:>3} arcs")

# Validation checks
print("\n\n" + "=" * 80)
print("VALIDATION CHECKS:")
print("=" * 80)

checks = {
    'normal': False,
    'inhibitor': False,
    'test': False,
    'signal_flow': False,
    'straight': False,
    'curved': False
}

for arc_type in arc_types.keys():
    if arc_type in checks:
        checks[arc_type] = True

for geom in geometry_types.keys():
    if geom in checks:
        checks[geom] = True

print("\nArc Type Detection:")
for check_type, detected in sorted(checks.items()):
    status = "✓ DETECTED" if detected else "✗ NOT FOUND"
    print(f"  {check_type:<15}: {status}")

# Check for accounting compatibility
print("\n\nAccounting Path Compatibility:")
print("-" * 80)

# Check if arcs have necessary fields for accounting
required_fields = ['source_id', 'target_id', 'weight', 'arc_type']
missing_fields = defaultdict(list)

for arc in arcs:
    for field in required_fields:
        if field not in arc:
            missing_fields[field].append(arc.get('id', 'unknown'))

if missing_fields:
    print("⚠ WARNING: Some arcs missing required fields:")
    for field, arc_ids in missing_fields.items():
        print(f"  {field}: {', '.join(map(str, arc_ids))}")
else:
    print("✓ All arcs have required fields for accounting")

# Check for special arc types that affect accounting
print("\nSpecial Arc Behavior for Accounting:")
print(f"  • Inhibitor arcs: {len(arc_types.get('inhibitor', []))} (do not consume tokens)")
print(f"  • Test arcs: {len(arc_types.get('test', []))} (do not consume tokens)")
print(f"  • Signal flow arcs: {len(arc_types.get('signal_flow', []))} (do not transfer tokens)")
print(f"  • Normal arcs: {len(arc_types.get('normal', []))} (standard token transfer)")

# Detailed breakdown by direction
print("\n\nArc Direction Analysis:")
input_arcs = [a for arcs_list in arc_types.values() for a in arcs_list if a['direction'] == 'P→T']
output_arcs = [a for arcs_list in arc_types.values() for a in arcs_list if a['direction'] == 'T→P']

print(f"  Input arcs (Place → Transition): {len(input_arcs)}")
print(f"  Output arcs (Transition → Place): {len(output_arcs)}")

# Check for each place/transition connectivity
print("\n\nConnectivity Summary:")
place_connections = defaultdict(lambda: {'input': 0, 'output': 0})
transition_connections = defaultdict(lambda: {'input': 0, 'output': 0})

for arc in arcs:
    source_id = arc.get('source_id')
    target_id = arc.get('target_id')
    
    if source_id in places:
        place_connections[places[source_id]]['output'] += 1
        transition_connections[transitions.get(target_id, str(target_id))]['input'] += 1
    elif source_id in transitions:
        transition_connections[transitions[source_id]]['output'] += 1
        place_connections[places.get(target_id, str(target_id))]['input'] += 1

print(f"\n  Places with connections: {len(place_connections)}")
for place, conn in sorted(place_connections.items()):
    print(f"    {place:<20}: {conn['input']} in, {conn['output']} out")

print(f"\n  Transitions with connections: {len(transition_connections)}")
for trans, conn in sorted(transition_connections.items()):
    print(f"    {trans:<20}: {conn['input']} in, {conn['output']} out")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
