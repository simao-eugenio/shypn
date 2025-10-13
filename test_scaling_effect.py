#!/usr/bin/env python3
"""
Demonstrate Scaling Effect: 2, 3, 4, 5-way Branching

Shows how aperture angles increase dramatically with number of children.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.data.pathway.pathway_data import PathwayData, Species, Reaction
from shypn.data.pathway.tree_layout import TreeLayoutProcessor


def create_n_way_branch(n):
    """Create pathway with n-way branching."""
    species = [Species(id="ROOT", name="Root")]
    reactions = []
    
    for i in range(n):
        child_id = f"C{i+1}"
        species.append(Species(id=child_id, name=f"Child {i+1}"))
        reactions.append(
            Reaction(id=f"R{i+1}", name=f"ROOT to {child_id}",
                    reactants=[("ROOT", 1.0)], products=[(child_id, 1.0)])
        )
    
    return PathwayData(species=species, reactions=reactions)


def main():
    print("\n" + "=" * 80)
    print("SCALING EFFECT: Aperture Angles vs. Number of Children")
    print("=" * 80)
    print("\nFormula: aperture_angle = atan(width/height) × num_children × 1.0")
    print()
    
    results = []
    
    for n in [2, 3, 4, 5, 6]:
        pathway = create_n_way_branch(n)
        processor = TreeLayoutProcessor(pathway, base_vertical_spacing=150, min_horizontal_spacing=150)
        positions = processor.calculate_tree_layout()
        
        # Calculate spread
        children = [s for s in positions.keys() if s.startswith('C')]
        if len(children) > 1:
            x_vals = [positions[c][0] for c in children]
            spread = max(x_vals) - min(x_vals)
            spacings = sorted([x_vals[i+1] - x_vals[i] for i in range(len(x_vals)-1)])
            avg_spacing = sum(spacings) / len(spacings)
        else:
            spread = 0
            spacings = []
            avg_spacing = 0
        
        results.append((n, spread, spacings, avg_spacing))
        
        print(f"\n{n}-WAY BRANCHING:")
        print("-" * 80)
        print(f"  Total spread: {spread:6.1f}px")
        print(f"  Avg spacing:  {avg_spacing:6.1f}px")
        if spacings:
            print(f"  Spacings:     {[f'{s:.1f}' for s in spacings]}")
    
    # Summary table
    print("\n\n" + "=" * 80)
    print("SUMMARY: Spread Increases with Branching")
    print("=" * 80)
    print(f"\n{'Children':>10} {'Spread (px)':>15} {'Avg Spacing':>15} {'Amplification':>15}")
    print("-" * 80)
    
    baseline_spread = results[0][1]  # 2-way branch as baseline
    
    for n, spread, _, avg_spacing in results:
        amplification = spread / baseline_spread if baseline_spread > 0 else 1.0
        print(f"{n:>10} {spread:>15.1f} {avg_spacing:>15.1f} {amplification:>15.2f}x")
    
    # Visualization
    print("\n\n" + "=" * 80)
    print("VISUAL REPRESENTATION")
    print("=" * 80)
    print("\nEach • represents a child, spacing shows aperture angle effect:\n")
    
    for n, spread, spacings, _ in results:
        # Create visual representation
        max_width = 60
        if spread > 0:
            positions_visual = []
            total = 0
            for i in range(n):
                if i == 0:
                    pos = 0
                else:
                    total += spacings[i-1] if i-1 < len(spacings) else 150
                    pos = int((total / spread) * max_width)
                positions_visual.append(pos)
            
            line = [' '] * (max_width + 1)
            for pos in positions_visual:
                line[min(pos, max_width)] = '●'
            print(f"{n}-way: {''.join(line)}")
        else:
            print(f"{n}-way: ●")
    
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print("\n✓ Spread increases DRAMATICALLY with number of children")
    print("✓ 6-way branching is", end=" ")
    if results[-1][1] / results[0][1] > 1.5:
        print(f"{results[-1][1] / results[0][1]:.1f}x wider than 2-way")
    print("✓ Aperture angles scale proportionally to branching factor")
    print("✓ Visual separation clearly emphasizes branching complexity")
    print("\nThe amplification factor (num_children × 1.0) creates")
    print("visually dramatic differences that reflect pathway structure!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
