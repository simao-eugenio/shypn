#!/usr/bin/env python3
"""Inspect a saved .shyn file for spurious arcs.

Usage: python3 inspect_saved_file.py <path_to_file.shyn>
"""

import sys
import json

if len(sys.argv) < 2:
    print("Usage: python3 inspect_saved_file.py <path_to_file.shyn>")
    sys.exit(1)

filename = sys.argv[1]

print("=" * 80)
print(f"INSPECTING: {filename}")
print("=" * 80)

with open(filename, 'r') as f:
    data = json.load(f)

places = data.get('places', [])
transitions = data.get('transitions', [])
arcs = data.get('arcs', [])

print(f"\nObjects: {len(places)} places, {len(transitions)} transitions, {len(arcs)} arcs")

# Build lookup for places and transitions
place_ids = {p['id']: p for p in places}
trans_ids = {t['id']: t for t in transitions}

print("\n" + "=" * 80)
print("ARC ANALYSIS")
print("=" * 80)

place_to_place_arcs = []
trans_to_trans_arcs = []
long_arcs = []
invalid_refs = []

for i, arc in enumerate(arcs):
    source_id = arc.get('source')
    target_id = arc.get('target')
    
    # Check if source/target exist
    source_is_place = source_id in place_ids
    source_is_trans = source_id in trans_ids
    target_is_place = target_id in place_ids
    target_is_trans = target_id in trans_ids
    
    if not (source_is_place or source_is_trans):
        invalid_refs.append((i, arc, f"source={source_id} not found"))
        continue
    
    if not (target_is_place or target_is_trans):
        invalid_refs.append((i, arc, f"target={target_id} not found"))
        continue
    
    # Check types
    if source_is_place and target_is_place:
        source_label = place_ids[source_id].get('label', '?')
        target_label = place_ids[target_id].get('label', '?')
        
        # Calculate distance
        sx = place_ids[source_id].get('x', 0)
        sy = place_ids[source_id].get('y', 0)
        tx = place_ids[target_id].get('x', 0)
        ty = place_ids[target_id].get('y', 0)
        dist = ((tx-sx)**2 + (ty-sy)**2) ** 0.5
        
        place_to_place_arcs.append((i, source_label, target_label, dist))
    
    if source_is_trans and target_is_trans:
        source_label = trans_ids[source_id].get('label', '?')
        target_label = trans_ids[target_id].get('label', '?')
        trans_to_trans_arcs.append((i, source_label, target_label))
    
    # Check distance
    if source_is_place:
        sx = place_ids[source_id].get('x', 0)
        sy = place_ids[source_id].get('y', 0)
        source_label = place_ids[source_id].get('label', '?')
        source_type = "Place"
    else:
        sx = trans_ids[source_id].get('x', 0)
        sy = trans_ids[source_id].get('y', 0)
        source_label = trans_ids[source_id].get('label', '?')
        source_type = "Transition"
    
    if target_is_place:
        tx = place_ids[target_id].get('x', 0)
        ty = place_ids[target_id].get('y', 0)
        target_label = place_ids[target_id].get('label', '?')
        target_type = "Place"
    else:
        tx = trans_ids[target_id].get('x', 0)
        ty = trans_ids[target_id].get('y', 0)
        target_label = trans_ids[target_id].get('label', '?')
        target_type = "Transition"
    
    dist = ((tx-sx)**2 + (ty-sy)**2) ** 0.5
    if dist > 500:
        long_arcs.append((i, source_type, source_label, target_type, target_label, dist))

print(f"Place→Place arcs: {len(place_to_place_arcs)}")
print(f"Transition→Transition arcs: {len(trans_to_trans_arcs)}")
print(f"Long arcs (>500px): {len(long_arcs)}")
print(f"Invalid references: {len(invalid_refs)}")

if place_to_place_arcs:
    print("\n❌ FOUND PLACE→PLACE ARCS:")
    for idx, src, tgt, dist in place_to_place_arcs:
        print(f"  Arc #{idx}: {src} → {tgt} (distance={dist:.1f})")

if trans_to_trans_arcs:
    print("\n❌ FOUND TRANSITION→TRANSITION ARCS:")
    for idx, src, tgt in trans_to_trans_arcs:
        print(f"  Arc #{idx}: {src} → {tgt}")

if long_arcs:
    print("\n⚠️  FOUND LONG ARCS:")
    for idx, src_type, src_label, tgt_type, tgt_label, dist in long_arcs:
        print(f"  Arc #{idx}: {src_type}({src_label}) → {tgt_type}({tgt_label}) (distance={dist:.1f})")

if invalid_refs:
    print("\n❌ FOUND INVALID REFERENCES:")
    for idx, arc, reason in invalid_refs:
        print(f"  Arc #{idx}: {reason}")

print("\n" + "=" * 80)
