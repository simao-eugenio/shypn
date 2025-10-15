#!/usr/bin/env python3
"""
Visualize tree layout structure to check hierarchical flow.
Shows the vertical layers and horizontal spread.
"""

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.data.pathway.pathway_data import PathwayData, Species, Reaction
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor


def create_multi_level_pathway():
    """Create 3-level pathway: A → B0,B1,B2 → (C0,C1 from B0), (D0,D1 from B2)"""
    pathway = PathwayData()
    
    # Level 0: Root
    root = Species(id='A', name='A', initial_concentration=1.0)
    pathway.species.append(root)
    
    # Level 1: 3 children
    b_species = []
    for i in range(3):
        b = Species(id=f'B{i}', name=f'B{i}', initial_concentration=0.0)
        pathway.species.append(b)
        b_species.append(b)
        pathway.reactions.append(Reaction(
            id=f'rA_B{i}', name=f'R_A_B{i}',
            reactants=[(root.id, 1.0)],
            products=[(b.id, 1.0)]
        ))
    
    # Level 2: Grandchildren from B0
    for i in range(2):
        c = Species(id=f'C{i}', name=f'C{i}', initial_concentration=0.0)
        pathway.species.append(c)
        pathway.reactions.append(Reaction(
            id=f'rB0_C{i}', name=f'R_B0_C{i}',
            reactants=[('B0', 1.0)],
            products=[(c.id, 1.0)]
        ))
    
    # Level 2: Grandchildren from B2
    for i in range(2):
        d = Species(id=f'D{i}', name=f'D{i}', initial_concentration=0.0)
        pathway.species.append(d)
        pathway.reactions.append(Reaction(
            id=f'rB2_D{i}', name=f'R_B2_D{i}',
            reactants=[('B2', 1.0)],
            products=[(d.id, 1.0)]
        ))
    
    return pathway


def visualize_layout(positions, title):
    """Create ASCII visualization of layout."""
    # Get bounds
    species_pos = {k: v for k, v in positions.items() if not k.startswith('r')}
    
    if not species_pos:
        print("No positions to visualize")
        return
    
    xs = [x for x, y in species_pos.values()]
    ys = [y for x, y in species_pos.values()]
    
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    print(f"\n{title}")
    print("=" * 80)
    print(f"Bounds: x=[{min_x:.0f}, {max_x:.0f}], y=[{min_y:.0f}, {max_y:.0f}]")
    print(f"Size: {max_x - min_x:.0f}px wide × {max_y - min_y:.0f}px tall")
    print(f"Aspect ratio: {(max_x - min_x) / max(1, max_y - min_y):.2f}:1 (width:height)")
    
    # Group by layer (y-coordinate)
    layers = {}
    for id, (x, y) in species_pos.items():
        y_rounded = round(y / 10) * 10  # Round to nearest 10
        if y_rounded not in layers:
            layers[y_rounded] = []
        layers[y_rounded].append((id, x))
    
    print(f"\nVertical Layers:")
    for y in sorted(layers.keys()):
        species = sorted(layers[y], key=lambda item: item[1])
        species_str = ', '.join([f"{id}({x:.0f})" for id, x in species])
        print(f"  y={y:.0f}: {species_str}")
    
    # ASCII visualization (simplified)
    print(f"\nASCII View:")
    print("-" * 80)
    
    # Normalize to fit in 70 chars width
    width_chars = 70
    height_chars = 20
    
    def normalize(val, min_val, max_val, char_range):
        if max_val == min_val:
            return char_range // 2
        return int((val - min_val) / (max_val - min_val) * (char_range - 1))
    
    # Create grid
    grid = [[' ' for _ in range(width_chars)] for _ in range(height_chars)]
    
    for id, (x, y) in species_pos.items():
        col = normalize(x, min_x, max_x, width_chars)
        row = normalize(y, min_y, max_y, height_chars)
        
        # Use first letter of ID
        char = id[0] if id else '?'
        if 0 <= row < height_chars and 0 <= col < width_chars:
            grid[row][col] = char
    
    for row in grid:
        print(''.join(row))
    
    print("-" * 80)


# Test both layouts
pathway = create_multi_level_pathway()

print("\n" + "=" * 80)
print("COMPARING FIXED vs TREE LAYOUT - HIERARCHICAL STRUCTURE")
print("=" * 80)

# Fixed layout
proc_fixed = PathwayPostProcessor(spacing=150.0, use_tree_layout=False)
result_fixed = proc_fixed.process(pathway)

visualize_layout(result_fixed.positions, "FIXED LAYOUT (traditional hierarchical)")

# Tree layout
proc_tree = PathwayPostProcessor(spacing=150.0, use_tree_layout=True)
result_tree = proc_tree.process(pathway)

visualize_layout(result_tree.positions, "TREE LAYOUT (aperture angle-based)")

# Analysis
print("\n" + "=" * 80)
print("ANALYSIS:")
print("=" * 80)

species_fixed = {k: v for k, v in result_fixed.positions.items() if not k.startswith('r')}
species_tree = {k: v for k, v in result_tree.positions.items() if not k.startswith('r')}

xs_fixed = [x for x, y in species_fixed.values()]
ys_fixed = [y for x, y in species_fixed.values()]
xs_tree = [x for x, y in species_tree.values()]
ys_tree = [y for x, y in species_tree.values()]

width_fixed = max(xs_fixed) - min(xs_fixed)
height_fixed = max(ys_fixed) - min(ys_fixed)
width_tree = max(xs_tree) - min(xs_tree)
height_tree = max(ys_tree) - min(ys_tree)

print(f"\nFixed layout:")
print(f"  Width:  {width_fixed:.0f}px")
print(f"  Height: {height_fixed:.0f}px")
print(f"  Aspect: {width_fixed/max(1, height_fixed):.2f}:1")

print(f"\nTree layout:")
print(f"  Width:  {width_tree:.0f}px")
print(f"  Height: {height_tree:.0f}px")
print(f"  Aspect: {width_tree/max(1, height_tree):.2f}:1")

ratio_width = width_tree / max(1, width_fixed)
ratio_height = height_tree / max(1, height_fixed)

print(f"\nTree vs Fixed:")
print(f"  Width ratio:  {ratio_width:.2f}× (tree is {'wider' if ratio_width > 1 else 'narrower'})")
print(f"  Height ratio: {ratio_height:.2f}× (tree is {'taller' if ratio_height > 1 else 'shorter'})")

if width_tree / max(1, height_tree) > 3.0:
    print(f"\n⚠️  ISSUE: Tree layout is very WIDE (aspect {width_tree/max(1, height_tree):.1f}:1)")
    print(f"    This makes vertical hierarchy hard to see in viewport!")
    print(f"    User needs to scroll horizontally to see all nodes.")
else:
    print(f"\n✅ Tree layout maintains reasonable aspect ratio")

print("=" * 80)
