#!/usr/bin/env python3
"""
Check the stochastic source transitions and see why they're not generating tokens.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.data.canvas.document_model import DocumentModel

model_path = "workspace/projects/Interactive/models/hsa00010.shy"
document = DocumentModel.load_from_file(model_path)

print("🔍 CHECKING STOCHASTIC SOURCES:\n")

# Find transitions with no input arcs (sources)
sources = []
for transition in document.transitions:
    input_arcs = [arc for arc in document.arcs if hasattr(arc, 'target') and arc.target == transition]
    output_arcs = [arc for arc in document.arcs if hasattr(arc, 'source') and arc.source == transition]
    
    if len(input_arcs) == 0 and len(output_arcs) > 0:
        sources.append({
            'transition': transition,
            'input_count': len(input_arcs),
            'output_count': len(output_arcs),
            'outputs': output_arcs
        })

print(f"Found {len(sources)} source transitions (no inputs, have outputs)\n")

for i, source_data in enumerate(sources, 1):
    t = source_data['transition']
    print(f"{i}. Transition: {t.name or t.id}")
    print(f"   ID: {t.id}")
    print(f"   Type: {getattr(t, 'type', 'unknown')}")
    print(f"   Label: {t.label}")
    
    # Check if it's stochastic
    behavior = getattr(t, 'behavior', None)
    if behavior:
        print(f"   Behavior: {behavior}")
    
    # Check properties
    properties = getattr(t, 'properties', {})
    if properties:
        print(f"   Properties keys: {list(properties.keys())}")
        if 'behavior' in properties:
            print(f"   properties.behavior: {properties['behavior']}")
        if 'type' in properties:
            print(f"   properties.type: {properties['type']}")
        if 'rate' in properties:
            print(f"   properties.rate: {properties['rate']}")
    
    # Show output places
    print(f"   Outputs to {len(source_data['outputs'])} place(s):")
    for arc in source_data['outputs']:
        target_name = arc.target.name if arc.target else "Unknown"
        print(f"      → {target_name}")
    
    print()

# Check transition types in saved file to see if stochastic behavior is saved
print("\n🔍 CHECKING SAVED FILE FOR STOCHASTIC MARKERS:\n")

import json
with open(model_path, 'r') as f:
    data = json.load(f)

# Find source transitions in saved data
for transition_data in data.get('transitions', []):
    t_id = transition_data.get('id')
    
    # Check if this is one of our sources
    for source in sources:
        if source['transition'].id == t_id:
            print(f"Transition {t_id} in saved file:")
            print(f"   name: {transition_data.get('name')}")
            print(f"   type: {transition_data.get('type')}")
            
            # Check for behavior indicators
            if 'behavior' in transition_data:
                print(f"   behavior: {transition_data.get('behavior')}")
            if 'rate' in transition_data:
                print(f"   rate: {transition_data.get('rate')}")
            
            properties = transition_data.get('properties', {})
            if properties:
                print(f"   properties: {properties}")
            
            print()
