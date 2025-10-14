#!/usr/bin/env python3
"""
Test vertical tree layout - tree grows TOP to BOTTOM.
Shows the spacing issue at each level.
"""

import sys
sys.path.insert(0, 'src')

from shypn.data.pathway.pathway_data import PathwayData, Species, Reaction
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor


def create_deep_pathway():
    """Create pathway with 5 levels of branching."""
    pathway = PathwayData()
    
    # Level 0: Root
    root = Species(id="A", name="A", initial_concentration=1.0)
    pathway.species.append(root)
    
    # Level 1: 3 children
    level1 = []
    for i in range(3):
        sid = f"B{i}"
        species = Species(id=sid, name=sid, initial_concentration=0.0)
        pathway.species.append(species)
        level1.append(sid)
        
        reaction = Reaction(id=f"r1_{i}", name=f"R1_{i}",
                           reactants=[(root.id, 1.0)],
                           products=[(sid, 1.0)])
        pathway.reactions.append(reaction)
    
    # Level 2: Each has 2 children
    level2 = []
    for parent_id in level1:
        for i in range(2):
            child_id = f"{parent_id}_C{i}"
            species = Species(id=child_id, name=child_id, initial_concentration=0.0)
            pathway.species.append(species)
            level2.append(child_id)
            
            reaction = Reaction(id=f"r_{child_id}", name=f"R_{child_id}",
                               reactants=[(parent_id, 1.0)],
                               products=[(child_id, 1.0)])
            pathway.reactions.append(reaction)
    
    return pathway


print("=" * 90)
print("VERTICAL TREE - SPACING ANALYSIS")
print("=" * 90)
print("\nTree grows TOP → BOTTOM (increasing Y)")
print("Siblings spread LEFT ↔ RIGHT (varying X)\n")

pathway = create_deep_pathway()

proc = PathwayPostProcessor(spacing=150.0, use_tree_layout=True)
result = proc.process(pathway)

# Organize by Y-coordinate (vertical levels)
levels_by_y = {}
for spec_id, (x, y) in result.positions.items():
    # Skip reactions for clarity
    if not spec_id.startswith('r'):
        if y not in levels_by_y:
            levels_by_y[y] = []
        levels_by_y[y].append((spec_id, x))

# Sort each level by x coordinate
for y in levels_by_y:
    levels_by_y[y].sort(key=lambda item: item[1])

# Print vertical structure
print("Vertical Structure (TOP → BOTTOM):")
print("-" * 90)

for level_num, y in enumerate(sorted(levels_by_y.keys())):
    items = levels_by_y[y]
    print(f"\nLevel {level_num} (Y={y:.0f}px): {len(items)} nodes")
    
    if len(items) > 1:
        # Calculate horizontal spacings
        x_coords = [x for _, x in items]
        spacings = [x_coords[i+1] - x_coords[i] for i in range(len(x_coords)-1)]
        min_spacing = min(spacings)
        max_spacing = max(spacings)
        avg_spacing = sum(spacings) / len(spacings)
        total_width = x_coords[-1] - x_coords[0]
        
        print(f"  Horizontal spacing: min={min_spacing:.0f}px, avg={avg_spacing:.0f}px, max={max_spacing:.0f}px")
        print(f"  Total width: {total_width:.0f}px")
        
        # Check if spacing is excessive
        if avg_spacing > 200:
            print(f"  ⚠️  EXCESSIVE SPACING (avg={avg_spacing:.0f}px)")
        elif avg_spacing > 150:
            print(f"  ⚠️  WIDE spacing")
        else:
            print(f"  ✅ Reasonable spacing")
    
    # Show positions
    pos_str = ", ".join([f"{sid}@x{x:.0f}" for sid, x in items])
    print(f"  Nodes: {pos_str}")

# Calculate total canvas size needed
all_x = [x for spec_id, (x, y) in result.positions.items()]
all_y = [y for spec_id, (x, y) in result.positions.items()]
canvas_width = max(all_x) - min(all_x)
canvas_height = max(all_y) - min(all_y)

print("\n" + "=" * 90)
print("CANVAS SIZE ANALYSIS:")
print("=" * 90)
print(f"Width needed: {canvas_width:.0f}px")
print(f"Height needed: {canvas_height:.0f}px")
print(f"Aspect ratio: {canvas_width/canvas_height:.2f}:1")
print()

if canvas_width > 2000:
    print("⚠️  PROBLEM: Canvas too wide (>2000px)")
    print("   → Horizontal spacing growing too much at each level")
    print("   → Angles too wide or minimum spacing too large")
elif canvas_width > 1000:
    print("⚠️  Canvas moderately wide (>1000px)")
else:
    print("✅ Canvas width reasonable")

print("=" * 90)
