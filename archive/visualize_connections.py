#!/usr/bin/env python3
"""
Visualize arc rendering to understand spurious lines.
This creates a simple ASCII diagram showing how arcs connect.
"""

import sys
import json
import math

if len(sys.argv) < 2:
    print("Usage: python3 visualize_connections.py <saved_file.shyn> [compound_id]")
    sys.exit(1)

filepath = sys.argv[1]
focus_compound = sys.argv[2] if len(sys.argv) > 2 else None

with open(filepath, 'r') as f:
    data = json.load(f)

places = {p['id']: p for p in data.get('places', [])}
transitions = {t['id']: t for t in data.get('transitions', [])}
arcs = data.get('arcs', [])

if focus_compound:
    # Find place with this compound
    focus_place = None
    for p_id, p in places.items():
        if focus_compound in p.get('label', ''):
            focus_place = p
            break
    
    if not focus_place:
        print(f"No place found with label containing '{focus_compound}'")
        sys.exit(1)
    
    print("=" * 80)
    print(f"CONNECTION DIAGRAM FOR: {focus_place['label']} ({focus_place['id']})")
    print("=" * 80)
    
    place_x = focus_place['x']
    place_y = focus_place['y']
    
    print(f"\nPlace position: ({place_x:.1f}, {place_y:.1f})")
    print(f"\nConnected arcs:")
    
    # Find all arcs connected to this place
    connected = []
    for arc in arcs:
        if arc['source_id'] == focus_place['id']:
            # Outgoing
            target_id = arc['target_id']
            if target_id in transitions:
                trans = transitions[target_id]
                connected.append(('OUT', trans, arc))
        elif arc['target_id'] == focus_place['id']:
            # Incoming
            source_id = arc['source_id']
            if source_id in transitions:
                trans = transitions[source_id]
                connected.append(('IN', trans, arc))
    
    print(f"\nTotal connections: {len(connected)}")
    
    for direction, trans, arc in connected:
        trans_x = trans['x']
        trans_y = trans['y']
        trans_w = trans.get('width', 15)
        trans_h = trans.get('height', 15)
        
        # Calculate distance and angle
        if direction == 'OUT':
            dx = trans_x - place_x
            dy = trans_y - place_y
        else:
            dx = place_x - trans_x
            dy = place_y - trans_y
        
        distance = math.sqrt(dx*dx + dy*dy)
        angle = math.degrees(math.atan2(dy, dx))
        
        arrow = "→" if direction == 'OUT' else "←"
        print(f"\n   {arrow} {trans.get('label', trans['id'])[:30]}")
        print(f"      Position: ({trans_x:.1f}, {trans_y:.1f})")
        print(f"      Size: {trans_w:.1f} × {trans_h:.1f} = {trans_w*trans_h:.0f} sq px")
        print(f"      Distance: {distance:.1f} px")
        print(f"      Angle: {angle:.0f}°")
        
        if trans_w < 15 or trans_h < 15:
            print(f"      ⚠️  SMALL TRANSITION - might be hard to see!")
    
    # Check for visual overlaps
    print(f"\n" + "=" * 80)
    print("VISUAL OVERLAP ANALYSIS")
    print("=" * 80)
    
    print(f"\nChecking if any arcs point in similar directions...")
    
    angles = []
    for direction, trans, arc in connected:
        trans_x = trans['x']
        trans_y = trans['y']
        
        if direction == 'OUT':
            dx = trans_x - place_x
            dy = trans_y - place_y
        else:
            dx = place_x - trans_x
            dy = place_y - trans_y
        
        angle = math.degrees(math.atan2(dy, dx))
        angles.append((angle, trans, direction))
    
    # Find arcs with similar angles (within 20 degrees)
    angles.sort()
    for i in range(len(angles)):
        for j in range(i+1, len(angles)):
            angle_diff = abs(angles[i][0] - angles[j][0])
            if angle_diff < 20:
                print(f"\n⚠️  Visual overlap detected:")
                print(f"   Arc to {angles[i][1].get('label', '')} ({angles[i][0]:.0f}°)")
                print(f"   Arc to {angles[j][1].get('label', '')} ({angles[j][0]:.0f}°)")
                print(f"   Angle difference: {angle_diff:.1f}°")
                print(f"   → These arcs might appear to overlap visually")

else:
    # Show overview
    print("=" * 80)
    print("CONNECTION OVERVIEW")
    print("=" * 80)
    
    print(f"\nPlaces with 3+ connections (candidates for visual confusion):")
    
    arcs_by_place = {}
    for arc in arcs:
        src_id = arc['source_id']
        tgt_id = arc['target_id']
        
        if src_id in places:
            arcs_by_place.setdefault(src_id, []).append(arc)
        if tgt_id in places:
            arcs_by_place.setdefault(tgt_id, []).append(arc)
    
    for place_id, connections in sorted(arcs_by_place.items(), key=lambda x: -len(x[1]))[:10]:
        place = places[place_id]
        label = place.get('label', place_id)
        print(f"   {label:15} ({place_id}): {len(connections)} connections")
    
    print(f"\nTo analyze a specific compound, run:")
    print(f"   python3 visualize_connections.py {filepath} <compound_id>")
    print(f"\nExample:")
    print(f"   python3 visualize_connections.py {filepath} C00036")
