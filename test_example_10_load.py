#!/usr/bin/env python3
"""Test loading Example 10 to see what error occurs."""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

import json

# Load the model file
model_path = '/home/simao/projetos/shypn/workspace/projects/Biochemical-Examples/10_Citric_Acid_Cycle/model.shy'

print("Loading Example 10 model...")
with open(model_path, 'r') as f:
    data = json.load(f)

print(f"✓ JSON loaded successfully")
print(f"  Places: {len(data['places'])}")
print(f"  Transitions: {len(data['transitions'])}")
print(f"  Arcs: {len(data['arcs'])}")

# Check transitions
print("\nTransitions:")
for t in data['transitions']:
    print(f"  {t['id']} - {t['name']}: {t.get('transition_type', 'immediate')}")
    if 'rate' in t:
        print(f"    rate: {t['rate']}")
    if 'rate_forward' in t:
        print(f"    rate_forward: {t['rate_forward']}")
    if 'rate_reverse' in t:
        print(f"    rate_reverse: {t['rate_reverse']}")

# Check arcs
print("\nArc types:")
arc_types = {}
for arc in data['arcs']:
    arc_type = arc.get('arc_type', 'normal')
    object_type = arc.get('object_type', 'arc')
    key = f"{object_type} / {arc_type}"
    arc_types[key] = arc_types.get(key, 0) + 1

for key, count in sorted(arc_types.items()):
    print(f"  {key}: {count}")

# Check for inconsistencies
print("\nChecking for arc type inconsistencies...")
for arc in data['arcs']:
    arc_type = arc.get('arc_type')
    object_type = arc.get('object_type')
    
    if object_type == 'curved_arc' and arc_type != 'curved_arc':
        print(f"  ⚠️  {arc['id']}: object_type={object_type} but arc_type={arc_type}")
    elif object_type == 'curved_inhibitor_arc' and arc_type != 'curved_inhibitor_arc':
        print(f"  ⚠️  {arc['id']}: object_type={object_type} but arc_type={arc_type}")

print("\nModel file structure looks OK!")
