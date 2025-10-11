#!/usr/bin/env python3
"""Analyze a saved .shyn file for spurious arcs.

Usage: python3 analyze_saved_file.py <file.shyn>
"""

import sys
import json
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: python3 analyze_saved_file.py <file.shyn>")
    sys.exit(1)

file_path = Path(sys.argv[1])

if not file_path.exists():
    print(f"Error: File not found: {file_path}")
    sys.exit(1)

print("=" * 80)
print(f"ANALYZING: {file_path}")
print("=" * 80)
print()

# Load JSON
with open(file_path, 'r') as f:
    data = json.load(f)

places = data.get('places', [])
transitions = data.get('transitions', [])
arcs = data.get('arcs', [])

print(f"Document contains:")
print(f"  Places: {len(places)}")
print(f"  Transitions: {len(transitions)}")
print(f"  Arcs: {len(arcs)}")
print()

# Build lookup tables
place_ids = {p['id'] for p in places}
transition_ids = {t['id'] for t in transitions}
place_by_id = {p['id']: p for p in places}
transition_by_id = {t['id']: t for t in transitions}

# Analyze arcs
print("=" * 80)
print("ARC ANALYSIS")
print("=" * 80)

place_to_place = []
trans_to_trans = []
long_arcs = []
invalid_refs = []

for arc in arcs:
    source_id = arc.get('source_id') or arc.get('source')
    target_id = arc.get('target_id') or arc.get('target')
    
    # Check if source/target exist
    source_is_place = source_id in place_ids
    source_is_trans = source_id in transition_ids
    target_is_place = target_id in place_ids
    target_is_trans = target_id in transition_ids
    
    if not (source_is_place or source_is_trans):
        invalid_refs.append((arc['id'], source_id, 'source', 'MISSING'))
        continue
    
    if not (target_is_place or target_is_trans):
        invalid_refs.append((arc['id'], target_id, 'target', 'MISSING'))
        continue
    
    # Get coordinates
    if source_is_place:
        src = place_by_id[source_id]
        src_type = "Place"
    else:
        src = transition_by_id[source_id]
        src_type = "Transition"
    
    if target_is_place:
        tgt = place_by_id[target_id]
        tgt_type = "Place"
    else:
        tgt = transition_by_id[target_id]
        tgt_type = "Transition"
    
    # Calculate distance
    dx = tgt['x'] - src['x']
    dy = tgt['y'] - src['y']
    distance = (dx*dx + dy*dy) ** 0.5
    
    # Check for violations
    if source_is_place and target_is_place:
        src_label = src.get('label', src.get('name', f"P{source_id}"))
        tgt_label = tgt.get('label', tgt.get('name', f"P{target_id}"))
        place_to_place.append((arc['id'], src_label, tgt_label, distance))
    
    if source_is_trans and target_is_trans:
        src_label = src.get('label', src.get('name', f"T{source_id}"))
        tgt_label = tgt.get('label', tgt.get('name', f"T{target_id}"))
        trans_to_trans.append((arc['id'], src_label, tgt_label, distance))
    
    if distance > 500:
        src_label = src.get('label', src.get('name', f"{src_type[0]}{source_id}"))
        tgt_label = tgt.get('label', tgt.get('name', f"{tgt_type[0]}{target_id}"))
        long_arcs.append((arc['id'], src_type, src_label, tgt_type, tgt_label, distance))

print(f"Invalid references: {len(invalid_refs)}")
print(f"Place→Place arcs: {len(place_to_place)}")
print(f"Transition→Transition arcs: {len(trans_to_trans)}")
print(f"Long arcs (>500px): {len(long_arcs)}")
print()

if invalid_refs:
    print("❌ INVALID REFERENCES:")
    for arc_id, ref_id, ref_type, status in invalid_refs:
        print(f"  Arc {arc_id}: {ref_type} ID {ref_id} - {status}")
    print()

if place_to_place:
    print("❌ PLACE→PLACE ARCS (VIOLATION):")
    for arc_id, src, tgt, dist in place_to_place:
        print(f"  Arc {arc_id}: {src} → {tgt} (distance={dist:.1f}px)")
    print()

if trans_to_trans:
    print("❌ TRANSITION→TRANSITION ARCS (VIOLATION):")
    for arc_id, src, tgt, dist in trans_to_trans:
        print(f"  Arc {arc_id}: {src} → {tgt} (distance={dist:.1f}px)")
    print()

if long_arcs:
    print("⚠️  LONG ARCS (>500px - possibly spurious):")
    for arc_id, src_type, src, tgt_type, tgt, dist in long_arcs:
        print(f"  Arc {arc_id}: {src_type}({src}) → {tgt_type}({tgt}) (distance={dist:.1f}px)")
    print()

if not (invalid_refs or place_to_place or trans_to_trans or long_arcs):
    print("✅ All arcs are valid! No issues found in saved data.")
    print()

print("=" * 80)
print("If you see spurious lines in GUI but this analysis shows no issues,")
print("then the spurious lines are NOT in the saved data - they're being")
print("drawn by extra rendering code somewhere in the application.")
print("=" * 80)
