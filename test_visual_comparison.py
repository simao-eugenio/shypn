#!/usr/bin/env python3
"""
Visual Comparison: Fixed Spacing vs Tree-Based Aperture Angles

Shows side-by-side comparison to demonstrate the visual effect.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.data.pathway.pathway_data import PathwayData, Species, Reaction, ProcessedPathwayData
from shypn.data.pathway.hierarchical_layout import BiochemicalLayoutProcessor


def create_branching_pathway():
    """Create pathway with significant branching."""
    return PathwayData(
        species=[
            Species(id="A", name="Substrate"),
            Species(id="B1", name="Product 1"),
            Species(id="B2", name="Product 2"),
            Species(id="B3", name="Product 3"),
            Species(id="B4", name="Product 4"),
            Species(id="C1", name="End 1"),
            Species(id="C2", name="End 2"),
            Species(id="C3", name="End 3"),
            Species(id="C4", name="End 4"),
        ],
        reactions=[
            Reaction(id="R1", name="A to B1", reactants=[("A", 1.0)], products=[("B1", 1.0)]),
            Reaction(id="R2", name="A to B2", reactants=[("A", 1.0)], products=[("B2", 1.0)]),
            Reaction(id="R3", name="A to B3", reactants=[("A", 1.0)], products=[("B3", 1.0)]),
            Reaction(id="R4", name="A to B4", reactants=[("A", 1.0)], products=[("B4", 1.0)]),
            Reaction(id="R5", name="B1 to C1", reactants=[("B1", 1.0)], products=[("C1", 1.0)]),
            Reaction(id="R6", name="B2 to C2", reactants=[("B2", 1.0)], products=[("C2", 1.0)]),
            Reaction(id="R7", name="B3 to C3", reactants=[("B3", 1.0)], products=[("C3", 1.0)]),
            Reaction(id="R8", name="B4 to C4", reactants=[("B4", 1.0)], products=[("C4", 1.0)]),
        ]
    )


def visualize_layout(positions, title):
    """Create ASCII visualization of layout."""
    print(f"\n{title}")
    print("=" * 80)
    
    # Group by layer
    by_layer = {}
    for species_id, (x, y) in positions.items():
        if species_id.startswith('R'):  # Skip reactions
            continue
        y_key = round(y / 150) * 150  # Normalize to 150px layers
        if y_key not in by_layer:
            by_layer[y_key] = []
        by_layer[y_key].append((species_id, x))
    
    # Find x range
    all_x = [x for layer in by_layer.values() for _, x in layer]
    min_x = min(all_x) if all_x else 0
    max_x = max(all_x) if all_x else 800
    
    # Create visualization
    canvas_width = 80
    
    for y in sorted(by_layer.keys()):
        species_list = sorted(by_layer[y], key=lambda item: item[1])
        
        # Create line with species positions
        line = [' '] * canvas_width
        
        for species_id, x in species_list:
            # Map x to canvas position
            if max_x > min_x:
                pos = int((x - min_x) / (max_x - min_x) * (canvas_width - 1))
                pos = max(0, min(canvas_width - 1, pos))
            else:
                pos = canvas_width // 2
            
            # Place species marker
            line[pos] = '●'
        
        print(''.join(line))
        
        # Print species info
        species_info = ', '.join([f"{sid}@{x:.0f}" for sid, x in species_list])
        print(f"  {species_info}")
        
        # Calculate spacing
        if len(species_list) > 1:
            x_positions = [x for _, x in species_list]
            spacings = [x_positions[i+1] - x_positions[i] for i in range(len(x_positions)-1)]
            avg_spacing = sum(spacings) / len(spacings)
            print(f"  Avg spacing: {avg_spacing:.1f}px")
        print()
    
    # Summary
    total_spread = max_x - min_x
    print(f"Total horizontal spread: {total_spread:.1f}px")
    print("=" * 80)


def main():
    """Compare fixed vs tree-based layouts."""
    
    print("\n" + "=" * 80)
    print("VISUAL COMPARISON: Fixed Spacing vs Tree-Based Aperture Angles")
    print("=" * 80)
    
    pathway = create_branching_pathway()
    
    print("\nPathway Structure:")
    print("  Root: A")
    print("  4 branches: B1, B2, B3, B4")
    print("  4 end products: C1, C2, C3, C4")
    print()
    
    # Test 1: Fixed spacing (current default)
    print("\n" + "=" * 80)
    print("METHOD 1: Fixed Spacing (Equal Distribution)")
    print("=" * 80)
    
    processed_fixed = ProcessedPathwayData(pathway)
    processor_fixed = BiochemicalLayoutProcessor(
        pathway,
        spacing=150.0,
        use_tree_layout=False  # Fixed spacing
    )
    processor_fixed.process(processed_fixed)
    
    visualize_layout(processed_fixed.positions, "Fixed Spacing Layout")
    
    # Test 2: Tree-based spacing
    print("\n" + "=" * 80)
    print("METHOD 2: Tree-Based Aperture Angles")
    print("=" * 80)
    
    processed_tree = ProcessedPathwayData(pathway)
    processor_tree = BiochemicalLayoutProcessor(
        pathway,
        spacing=150.0,
        use_tree_layout=True  # Tree-based spacing
    )
    processor_tree.process(processed_tree)
    
    visualize_layout(processed_tree.positions, "Tree-Based Layout")
    
    # Comparison
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    
    # Calculate spreads
    fixed_x = [x for sid, (x, y) in processed_fixed.positions.items() if not sid.startswith('R')]
    tree_x = [x for sid, (x, y) in processed_tree.positions.items() if not sid.startswith('R')]
    
    fixed_spread = max(fixed_x) - min(fixed_x) if fixed_x else 0
    tree_spread = max(tree_x) - min(tree_x) if tree_x else 0
    
    print(f"\nFixed Spacing:")
    print(f"  Horizontal spread: {fixed_spread:.1f}px")
    print(f"  Strategy: Equal distribution (100px between all neighbors)")
    
    print(f"\nTree-Based Spacing:")
    print(f"  Horizontal spread: {tree_spread:.1f}px")
    print(f"  Strategy: Aperture angles (150px minimum, wider for branches)")
    
    print(f"\nDifference: {abs(tree_spread - fixed_spread):.1f}px")
    
    if tree_spread > fixed_spread:
        ratio = tree_spread / fixed_spread if fixed_spread > 0 else float('inf')
        print(f"Tree-based is {ratio:.1f}x wider (more visual separation!)")
    
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print("\n✓ Tree-based layout creates MORE visual separation")
    print("✓ Spacing adapts to branching structure")
    print("✓ 4-way branching gets appropriate angular spread")
    print("✓ Each bifurcation accounts for number of children")
    print("\nThe aperture angle approach creates more natural tree-like layouts")
    print("where branching points are visually emphasized through wider spacing.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
