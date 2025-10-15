#!/usr/bin/env python3
"""
Test Asymmetric Branching - Where Tree-Based Layout Shines

Creates pathway with ASYMMETRIC branching:
- One side has many branches (should spread wide)
- Other side has single chain (should stay compact)

This demonstrates the key advantage of tree-based layouts:
spacing adapts to LOCAL branching structure, not global averaging.
"""

import sys
import os
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.data.pathway.pathway_data import PathwayData, Species, Reaction, ProcessedPathwayData
from shypn.data.pathway.hierarchical_layout import BiochemicalLayoutProcessor


def create_asymmetric_pathway():
    """Create pathway with asymmetric branching.
    
    Structure:
                    ROOT
                  /      \
             HEAVY        LIGHT
            /  |  \          |
           B1 B2  B3        C1
           |  |   |          |
           E1 E2  E3        D1
    
    Left side: 3-way branch (should spread wide)
    Right side: single chain (should stay compact)
    """
    return PathwayData(
        species=[
            Species(id="ROOT", name="Root"),
            Species(id="HEAVY", name="Heavy Branch"),
            Species(id="LIGHT", name="Light Branch"),
            Species(id="B1", name="Heavy Sub 1"),
            Species(id="B2", name="Heavy Sub 2"),
            Species(id="B3", name="Heavy Sub 3"),
            Species(id="C1", name="Light Sub"),
            Species(id="E1", name="End 1"),
            Species(id="E2", name="End 2"),
            Species(id="E3", name="End 3"),
            Species(id="D1", name="End 4"),
        ],
        reactions=[
            # Root splits
            Reaction(id="R1", name="ROOT to HEAVY", reactants=[("ROOT", 1.0)], products=[("HEAVY", 1.0)]),
            Reaction(id="R2", name="ROOT to LIGHT", reactants=[("ROOT", 1.0)], products=[("LIGHT", 1.0)]),
            
            # Heavy branch splits 3 ways
            Reaction(id="R3", name="HEAVY to B1", reactants=[("HEAVY", 1.0)], products=[("B1", 1.0)]),
            Reaction(id="R4", name="HEAVY to B2", reactants=[("HEAVY", 1.0)], products=[("B2", 1.0)]),
            Reaction(id="R5", name="HEAVY to B3", reactants=[("HEAVY", 1.0)], products=[("B3", 1.0)]),
            
            # Light branch stays linear
            Reaction(id="R6", name="LIGHT to C1", reactants=[("LIGHT", 1.0)], products=[("C1", 1.0)]),
            
            # Terminals
            Reaction(id="R7", name="B1 to E1", reactants=[("B1", 1.0)], products=[("E1", 1.0)]),
            Reaction(id="R8", name="B2 to E2", reactants=[("B2", 1.0)], products=[("E2", 1.0)]),
            Reaction(id="R9", name="B3 to E3", reactants=[("B3", 1.0)], products=[("E3", 1.0)]),
            Reaction(id="R10", name="C1 to D1", reactants=[("C1", 1.0)], products=[("D1", 1.0)]),
        ]
    )


def analyze_layout(positions, title):
    """Analyze and visualize layout."""
    print(f"\n{title}")
    print("=" * 90)
    
    # Group by layer
    by_layer = {}
    for species_id, (x, y) in positions.items():
        if species_id.startswith('R'):  # Skip reactions
            continue
        y_key = round(y / 150) * 150
        if y_key not in by_layer:
            by_layer[y_key] = []
        by_layer[y_key].append((species_id, x))
    
    # Analyze each layer
    for y in sorted(by_layer.keys()):
        species_list = sorted(by_layer[y], key=lambda item: item[1])
        print(f"\nLayer {int(y/150)}:")
        for species_id, x in species_list:
            print(f"  {species_id:10} at X={x:7.1f}px")
        
        if len(species_list) > 1:
            x_positions = [x for _, x in species_list]
            spacings = [x_positions[i+1] - x_positions[i] for i in range(len(x_positions)-1)]
            print(f"  Spacings: {[f'{s:.1f}' for s in spacings]}")
            print(f"  Min: {min(spacings):.1f}px, Max: {max(spacings):.1f}px, Avg: {sum(spacings)/len(spacings):.1f}px")
    
    # Calculate spread for each branch
    print(f"\n{'Branch Analysis:':40}")
    print("-" * 90)
    
    # Heavy branch (B1, B2, B3)
    heavy_species = [s for s, (x, y) in positions.items() if s in ['B1', 'B2', 'B3']]
    if heavy_species:
        heavy_x = [positions[s][0] for s in heavy_species]
        heavy_spread = max(heavy_x) - min(heavy_x) if len(heavy_x) > 1 else 0
        print(f"Heavy branch (3-way split): {heavy_spread:6.1f}px spread")
    
    # Light branch (C1, D1)
    light_species = [s for s, (x, y) in positions.items() if s in ['C1', 'D1']]
    if light_species:
        light_x = [positions[s][0] for s in light_species]
        light_spread = max(light_x) - min(light_x) if len(light_x) > 1 else 0
        print(f"Light branch (linear):      {light_spread:6.1f}px spread")
    
    # Total
    all_x = [x for s, (x, y) in positions.items() if not s.startswith('R')]
    total_spread = max(all_x) - min(all_x) if all_x else 0
    print(f"Total pathway spread:       {total_spread:6.1f}px")
    
    print("=" * 90)
    
    return {
        'heavy_spread': heavy_spread if heavy_species else 0,
        'light_spread': light_spread if light_species else 0,
        'total_spread': total_spread
    }


def main():
    """Compare fixed vs tree-based on asymmetric branching."""
    
    print("\n" + "=" * 90)
    print("ASYMMETRIC BRANCHING TEST")
    print("Where Tree-Based Layout Really Shines")
    print("=" * 90)
    
    print("\nPathway Structure:")
    print("  Root → splits to:")
    print("    • Heavy Branch → 3-way split (B1, B2, B3)")
    print("    • Light Branch → linear chain (C1 → D1)")
    print()
    print("Expected Behavior:")
    print("  FIXED: Equal spacing everywhere (doesn't reflect structure)")
    print("  TREE:  Wide for heavy branch, compact for light branch")
    
    pathway = create_asymmetric_pathway()
    
    # Test 1: Fixed spacing
    print("\n\n" + "=" * 90)
    print("METHOD 1: Fixed Spacing (Equal Distribution)")
    print("=" * 90)
    
    processed_fixed = ProcessedPathwayData(pathway)
    processor_fixed = BiochemicalLayoutProcessor(pathway, spacing=150.0, use_tree_layout=False)
    processor_fixed.process(processed_fixed)
    
    fixed_metrics = analyze_layout(processed_fixed.positions, "Fixed Spacing Layout")
    
    # Test 2: Tree-based spacing
    print("\n\n" + "=" * 90)
    print("METHOD 2: Tree-Based Aperture Angles")
    print("=" * 90)
    
    processed_tree = ProcessedPathwayData(pathway)
    processor_tree = BiochemicalLayoutProcessor(pathway, spacing=150.0, use_tree_layout=True)
    processor_tree.process(processed_tree)
    
    tree_metrics = analyze_layout(processed_tree.positions, "Tree-Based Layout")
    
    # Comparison
    print("\n\n" + "=" * 90)
    print("COMPARISON: Fixed vs Tree-Based")
    print("=" * 90)
    
    print(f"\n{'Metric':<30} {'Fixed':>15} {'Tree-Based':>15} {'Difference':>15}")
    print("-" * 90)
    print(f"{'Heavy branch spread':<30} {fixed_metrics['heavy_spread']:>12.1f}px {tree_metrics['heavy_spread']:>12.1f}px {tree_metrics['heavy_spread'] - fixed_metrics['heavy_spread']:>12.1f}px")
    print(f"{'Light branch spread':<30} {fixed_metrics['light_spread']:>12.1f}px {tree_metrics['light_spread']:>12.1f}px {tree_metrics['light_spread'] - fixed_metrics['light_spread']:>12.1f}px")
    print(f"{'Total spread':<30} {fixed_metrics['total_spread']:>12.1f}px {tree_metrics['total_spread']:>12.1f}px {tree_metrics['total_spread'] - fixed_metrics['total_spread']:>12.1f}px")
    
    print("\n" + "=" * 90)
    print("CONCLUSION")
    print("=" * 90)
    
    if tree_metrics['heavy_spread'] > fixed_metrics['heavy_spread'] * 1.1:
        print("\n✓ SUCCESS: Tree-based creates WIDER spread for heavy branching!")
    else:
        print("\n⚠ Similar spreads - aperture angles match fixed spacing")
    
    if tree_metrics['light_spread'] < fixed_metrics['light_spread'] * 0.9:
        print("✓ SUCCESS: Tree-based creates COMPACT layout for linear chains!")
    else:
        print("⚠ Light branch spacing similar")
    
    print("\nKEY INSIGHT:")
    print("  Tree-based adapts spacing to LOCAL branching structure.")
    print("  Heavy branches get wide angles, light branches stay compact.")
    print("  This reflects the natural tree/forest structure of pathways!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
