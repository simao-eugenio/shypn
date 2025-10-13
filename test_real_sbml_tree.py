#!/usr/bin/env python3
"""
Test tree layout with real SBML pathway (BIOMD0000000001).
Shows oblique tree structure with actual biochemical pathway.
"""

import sys
sys.path.insert(0, 'src')

from shypn.data.pathway.pathway_data import PathwayData
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
from shypn.data.pathway.sbml_parser import SBMLParser

print("=" * 90)
print("REAL SBML PATHWAY - OBLIQUE TREE LAYOUT TEST")
print("=" * 90)
print("\nLoading BIOMD0000000001 with tree layout enabled...")

# Load SBML file
parser = SBMLParser()
pathway = parser.parse_file("/tmp/BIOMD0000000001.xml")

print(f"\nPathway loaded:")
print(f"  Species: {len(pathway.species)}")
print(f"  Reactions: {len(pathway.reactions)}")

# Process with tree layout
proc = PathwayPostProcessor(spacing=150.0, use_tree_layout=True)
result = proc.process(pathway)

print(f"\nLayout result:")
print(f"  Layout type: {result.metadata.get('layout_type', 'unknown')}")
print(f"  Positions: {len(result.positions)}")

# Analyze structure
if result.metadata.get('layout_type') == 'hierarchical-tree':
    print("\n✅ TREE LAYOUT APPLIED")
    
    # Group by y-coordinate (levels)
    levels = {}
    for spec_id, (x, y) in result.positions.items():
        if y not in levels:
            levels[y] = []
        levels[y].append((spec_id, x))
    
    print(f"\nHierarchical levels detected: {len(levels)}")
    
    # Show first few levels
    sorted_levels = sorted(levels.keys())
    for i, y in enumerate(sorted_levels[:5]):
        items = levels[y]
        print(f"\nLevel {i} (y={y:.0f}px): {len(items)} nodes")
        
        if len(items) > 1:
            x_coords = sorted([x for _, x in items])
            spacings = [x_coords[j+1] - x_coords[j] for j in range(len(x_coords)-1)]
            if spacings:
                min_sp = min(spacings)
                max_sp = max(spacings)
                avg_sp = sum(spacings) / len(spacings)
                
                print(f"  Spacing: min={min_sp:.0f}px, avg={avg_sp:.0f}px, max={max_sp:.0f}px")
                
                if max_sp - min_sp > 20:
                    print(f"  ✅ Oblique (varying spacing)")
                else:
                    print(f"  ⚠️  Fixed (equal spacing)")
        
        # Show sample nodes
        sample = sorted(items, key=lambda x: x[1])[:3]
        names = ", ".join([f"{sid}@{x:.0f}" for sid, x in sample])
        if len(items) > 3:
            names += f", ... ({len(items)-3} more)"
        print(f"  Nodes: {names}")
    
    if len(sorted_levels) > 5:
        print(f"\n... and {len(sorted_levels)-5} more levels")

else:
    print(f"\n⚠️  Layout type: {result.metadata.get('layout_type', 'unknown')}")
    print("Tree layout not applied - pathway may not be hierarchical")

print("\n" + "=" * 90)
print("Load this file in the app to see visual oblique tree structure")
print("=" * 90)
