#!/usr/bin/env python3
"""
Check if compounds in a chain are visually aligned, creating illusion of direct connection.
"""

import sys
import json
import math

if len(sys.argv) < 2:
    print("Usage: python3 check_specific_chain.py <saved_file.shyn>")
    sys.exit(1)

filepath = sys.argv[1]

with open(filepath, 'r') as f:
    data = json.load(f)

places = {p['id']: p for p in data.get('places', [])}
transitions = {t['id']: t for t in data.get('transitions', [])}
arcs = data.get('arcs', [])

print("=" * 80)
print("COMPOUND CHAIN ANALYSIS")
print("=" * 80)

# The chain mentioned: C00036 → C01159 → C00118 → C00668 → PDHA1
chain_labels = ['C00036', 'C01159', 'C00118', 'C00668', 'PDHA1']

print(f"\nAnalyzing chain: {' → '.join(chain_labels)}")

# Find these objects
chain_objects = []
for label in chain_labels:
    # Check places
    found = None
    for p_id, p in places.items():
        if label in p.get('label', ''):
            found = ('place', p_id, p)
            break
    
    # Check transitions if not found in places
    if not found:
        for t_id, t in transitions.items():
            if label in t.get('label', ''):
                found = ('transition', t_id, t)
                break
    
    if found:
        chain_objects.append(found)
    else:
        print(f"⚠️  {label} not found in model")

if len(chain_objects) < 2:
    print("\n❌ Not enough objects found to analyze chain")
    sys.exit(1)

print(f"\n📍 Object Positions:")
for obj_type, obj_id, obj in chain_objects:
    x = obj['x']
    y = obj['y']
    label = obj.get('label', obj_id)
    print(f"   {label:15} ({obj_type:10}) at ({x:7.1f}, {y:7.1f})")

# Check if they're aligned (same Y coordinate, suggesting horizontal flow)
print(f"\n🔍 Alignment Analysis:")
y_coords = [obj[2]['y'] for obj in chain_objects]
y_range = max(y_coords) - min(y_coords)
print(f"   Y-coordinate range: {y_range:.1f} pixels")

if y_range < 100:
    print(f"   ⚠️  Objects are horizontally aligned (Y range < 100px)")
    print(f"      This creates visual illusion of direct connection!")
else:
    print(f"   ✅ Objects are NOT aligned (Y range > 100px)")

# Check actual connectivity via arcs and transitions
print(f"\n🔗 Actual Connectivity:")

for i in range(len(chain_objects) - 1):
    obj1_type, obj1_id, obj1 = chain_objects[i]
    obj2_type, obj2_id, obj2 = chain_objects[i + 1]
    
    label1 = obj1.get('label', obj1_id)
    label2 = obj2.get('label', obj2_id)
    
    print(f"\n   {label1} → {label2}:")
    
    # Check if there's a direct arc
    direct_arc = None
    for arc in arcs:
        if arc['source_id'] == obj1_id and arc['target_id'] == obj2_id:
            direct_arc = arc
            break
    
    if direct_arc:
        print(f"      🐛 DIRECT ARC EXISTS (Arc {direct_arc['id']})")
        print(f"         This is a BUG - {obj1_type} → {obj2_type} arc!")
    else:
        # Find path through transitions
        if obj1_type == 'place':
            # Find outgoing arcs from place
            outgoing = [a for a in arcs if a['source_id'] == obj1_id]
            print(f"      Place has {len(outgoing)} outgoing arc(s)")
            
            for arc in outgoing:
                trans_id = arc['target_id']
                if trans_id in transitions:
                    trans = transitions[trans_id]
                    trans_label = trans.get('label', trans_id)[:20]
                    print(f"         → Transition {trans_label}")
                    
                    # Check if this transition connects to obj2
                    trans_outgoing = [a for a in arcs if a['source_id'] == trans_id]
                    for t_arc in trans_outgoing:
                        if t_arc['target_id'] == obj2_id:
                            print(f"            → ✅ Connects to {label2}")
                            print(f"            Full path: {label1} → {trans_label} → {label2}")

# Check for visual overlaps
print(f"\n" + "=" * 80)
print("VISUAL OVERLAP CHECK")
print("=" * 80)

print(f"\nChecking if arcs from consecutive compounds overlap visually...")

for i in range(len(chain_objects) - 1):
    obj1_type, obj1_id, obj1 = chain_objects[i]
    obj2_type, obj2_id, obj2 = chain_objects[i + 1]
    
    if obj1_type == 'place' and obj2_type == 'place':
        # Both are places - check if their positions suggest visual connection
        x1, y1 = obj1['x'], obj1['y']
        x2, y2 = obj2['x'], obj2['y']
        
        distance = math.sqrt((x2-x1)**2 + (y2-y1)**2)
        angle = math.degrees(math.atan2(y2-y1, x2-x1))
        
        label1 = obj1.get('label', obj1_id)
        label2 = obj2.get('label', obj2_id)
        
        print(f"\n   {label1} to {label2}:")
        print(f"      Distance: {distance:.1f} px")
        print(f"      Angle: {angle:.1f}°")
        
        if distance < 300:
            print(f"      ⚠️  Very close! Arcs might appear to connect directly")
            
            # Find intermediate transitions
            outgoing = [a for a in arcs if a['source_id'] == obj1_id]
            for arc in outgoing:
                trans_id = arc['target_id']
                if trans_id in transitions:
                    trans = transitions[trans_id]
                    tx, ty = trans['x'], trans['y']
                    tw, th = trans.get('width', 15), trans.get('height', 15)
                    
                    # Check if transition is between the two places
                    if min(x1, x2) <= tx <= max(x1, x2) and min(y1, y2) <= ty <= max(y1, y2):
                        print(f"         Transition {trans.get('label', trans_id)[:20]} is between them")
                        print(f"         Size: {tw:.1f}×{th:.1f} px")
                        
                        if tw < 15 or th < 15:
                            print(f"         🐛 TINY TRANSITION - might be invisible!")

print(f"\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

print(f"\nIf you see visual lines connecting these compounds directly:")
print(f"1. Check if transitions between them are too small to see")
print(f"2. The compounds might be aligned, making arcs appear to connect them")
print(f"3. Zoom in to see if tiny transitions exist at connection points")
