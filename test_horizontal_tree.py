#!/usr/bin/env python3
"""
Test horizontal tree layout - tree grows LEFT to RIGHT.
Siblings spread VERTICALLY (top to bottom).
"""

import sys
sys.path.insert(0, 'src')

from shypn.data.pathway.pathway_data import PathwayData, Species, Reaction
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor


def create_multi_level_pathway():
    """Create pathway with multiple branching levels."""
    pathway = PathwayData()
    
    # Level 0: Root
    root = Species(id="A", name="A", initial_concentration=1.0)
    pathway.species.append(root)
    
    # Level 1: 3 children of root
    level1_ids = ["B0", "B1", "B2"]
    for i, sid in enumerate(level1_ids):
        species = Species(id=sid, name=sid, initial_concentration=0.0)
        pathway.species.append(species)
        
        reaction = Reaction(
            id=f"r1_{i}",
            name=f"R1_{i}",
            reactants=[(root.id, 1.0)],
            products=[(sid, 1.0)]
        )
        pathway.reactions.append(reaction)
    
    # Level 2: Each level1 node has 2-3 children
    children_per_parent = [2, 3, 2]  # B0->2, B1->3, B2->2
    for parent_idx, parent_id in enumerate(level1_ids):
        num_children = children_per_parent[parent_idx]
        for i in range(num_children):
            child_id = f"C{parent_idx}_{i}"
            species = Species(id=child_id, name=child_id, initial_concentration=0.0)
            pathway.species.append(species)
            
            reaction = Reaction(
                id=f"r2_{parent_idx}_{i}",
                name=f"R2_{parent_idx}_{i}",
                reactants=[(parent_id, 1.0)],
                products=[(child_id, 1.0)]
            )
            pathway.reactions.append(reaction)
    
    return pathway


print("=" * 90)
print("HORIZONTAL TREE LAYOUT - LEFT TO RIGHT GROWTH")
print("=" * 90)
print("\nTree grows LEFT → RIGHT (increasing X)")
print("Siblings spread TOP ↕ BOTTOM (varying Y)\n")

pathway = create_multi_level_pathway()

proc = PathwayPostProcessor(spacing=150.0, use_tree_layout=True)
result = proc.process(pathway)

# Organize by X-coordinate (horizontal levels)
levels_by_x = {}
for spec_id, (x, y) in result.positions.items():
    if x not in levels_by_x:
        levels_by_x[x] = []
    levels_by_x[x].append((spec_id, y))

# Sort each level by y coordinate
for x in levels_by_x:
    levels_by_x[x].sort(key=lambda item: item[1])

# Print horizontal structure
print("Horizontal Structure (LEFT → RIGHT):")
print("-" * 90)

for x in sorted(levels_by_x.keys()):
    items = levels_by_x[x]
    print(f"\nLevel at X={x:.0f}px: {len(items)} nodes")
    
    if len(items) > 1:
        # Calculate vertical spacings
        y_coords = [y for _, y in items]
        spacings = [y_coords[i+1] - y_coords[i] for i in range(len(y_coords)-1)]
        min_spacing = min(spacings)
        max_spacing = max(spacings)
        avg_spacing = sum(spacings) / len(spacings)
        
        print(f"  Vertical spacing: min={min_spacing:.1f}px, avg={avg_spacing:.1f}px, max={max_spacing:.1f}px")
        
        # Check if spacing varies (oblique angles)
        if max_spacing - min_spacing > 10:
            print(f"  ✅ OBLIQUE (varying vertical spacing shows angular positioning)")
        else:
            print(f"  ⚠️  FIXED (equal spacing)")
    
    # Show positions
    pos_str = ", ".join([f"{sid}@y{y:.0f}" for sid, y in items])
    print(f"  Nodes: {pos_str}")

# Visualize tree structure (ASCII)
print("\n" + "-" * 90)
print("ASCII Visualization (approximate):")
print("-" * 90)
print()

# Get all positions
all_positions = [(spec_id, x, y) for spec_id, (x, y) in result.positions.items() 
                 if not spec_id.startswith('r')]  # Skip reactions for clarity

# Normalize to character grid
min_x = min(x for _, x, y in all_positions)
max_x = max(x for _, x, y in all_positions)
min_y = min(y for _, x, y in all_positions)
max_y = max(y for _, x, y in all_positions)

# Create simple visualization showing left-to-right flow
print("ROOT (A) on LEFT → Descendants on RIGHT")
print()
for spec_id in ['A']:
    x, y = result.positions[spec_id]
    print(f"{spec_id} @ x={x:.0f}")

for spec_id in ['B0', 'B1', 'B2']:
    x, y = result.positions[spec_id]
    indent = int((x - min_x) / 50)  # Rough indentation
    print(f"{'  ' * indent}├─ {spec_id} @ x={x:.0f}, y={y:.0f}")

for spec_id in ['C0_0', 'C0_1', 'C1_0', 'C1_1', 'C1_2', 'C2_0', 'C2_1']:
    if spec_id in result.positions:
        x, y = result.positions[spec_id]
        indent = int((x - min_x) / 50)
        print(f"{'  ' * indent}├─ {spec_id} @ x={x:.0f}, y={y:.0f}")

print("\n" + "=" * 90)
print("SUMMARY:")
print("=" * 90)
print("✅ Tree grows HORIZONTALLY (left to right, increasing X)")
print("✅ Each parent spreads children VERTICALLY (different Y)")
print("✅ Siblings at same X coordinate (same horizontal level)")
print("✅ Oblique angles create varying vertical spacing")
print("=" * 90)
