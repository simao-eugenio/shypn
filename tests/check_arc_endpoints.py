#!/usr/bin/env python3
"""
Check if arcs have correct source/target or if they're being rendered incorrectly.
"""

import sys
import json

if len(sys.argv) < 2:
    print("Usage: python3 check_arc_endpoints.py <saved_file.shyn>")
    sys.exit(1)

filepath = sys.argv[1]

with open(filepath, 'r') as f:
    data = json.load(f)

places = {p['id']: p for p in data.get('places', [])}
transitions = {t['id']: t for t in data.get('transitions', [])}
arcs = data.get('arcs', [])

print("=" * 80)
print("ARC ENDPOINT VERIFICATION")
print("=" * 80)

print(f"\nAnalyzing {len(arcs)} arcs...")

# Group arcs by place
arcs_by_place = {}
for arc in arcs:
    src_id = arc['source_id']
    tgt_id = arc['target_id']
    
    if src_id in places:
        arcs_by_place.setdefault(src_id, []).append(('OUT', arc))
    if tgt_id in places:
        arcs_by_place.setdefault(tgt_id, []).append(('IN', arc))

# Find places with many connections (candidates for spurious lines)
print(f"\n🔍 Places with multiple connections:")
for place_id, connections in sorted(arcs_by_place.items(), key=lambda x: -len(x[1])):
    place = places[place_id]
    label = place.get('label', place_id)
    
    if len(connections) >= 3:  # 3 or more connections
        print(f"\n   {label} ({place_id}): {len(connections)} connections")
        
        for direction, arc in connections:
            if direction == 'OUT':
                target_id = arc['target_id']
                if target_id in transitions:
                    target = transitions[target_id]
                    target_label = target.get('label', target_id)[:30]
                    print(f"      → {target_label} (T)")
                else:
                    print(f"      → UNKNOWN TARGET: {target_id}")
            else:
                source_id = arc['source_id']
                if source_id in transitions:
                    source = transitions[source_id]
                    source_label = source.get('label', source_id)[:30]
                    print(f"      ← {source_label} (T)")
                else:
                    print(f"      ← UNKNOWN SOURCE: {source_id}")

# Check for arcs with control points (curved arcs)
print(f"\n" + "=" * 80)
print("CURVED ARCS CHECK")
print("=" * 80)

curved_arcs = [a for a in arcs if a.get('is_curved') or a.get('control_points')]
print(f"\nFound {len(curved_arcs)} curved arcs")

if curved_arcs:
    for arc in curved_arcs[:10]:
        src = places.get(arc['source_id']) or transitions.get(arc['source_id'])
        tgt = places.get(arc['target_id']) or transitions.get(arc['target_id'])
        print(f"\n   Arc {arc['id']}:")
        print(f"      From: {src.get('label', arc['source_id']) if src else 'UNKNOWN'}")
        print(f"      To: {tgt.get('label', arc['target_id']) if tgt else 'UNKNOWN'}")
        if 'control_points' in arc:
            print(f"      Control points: {arc['control_points']}")
        if 'control_offset_x' in arc or 'control_offset_y' in arc:
            print(f"      Offsets: ({arc.get('control_offset_x', 0)}, {arc.get('control_offset_y', 0)})")

print(f"\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)

print(f"\n💡 Next debugging steps:")
print(f"1. In the GUI, click on one of the 'spurious' lines")
print(f"2. Does it select? Does it have properties?")
print(f"3. Try to delete it - does it disappear?")
print(f"4. Zoom in very close - is there a tiny transition at the end?")
print(f"\n5. If the lines are truly non-interactive:")
print(f"   - They're being drawn by rendering code")
print(f"   - Need to add print statements in Arc.render() to debug")
