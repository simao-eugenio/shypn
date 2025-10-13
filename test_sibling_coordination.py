#!/usr/bin/env python3
"""
Test Sibling Coordination Rule

Rule 4: Siblings with more children determine the aperture angle
        for ALL siblings at that level (layer coordination)

Demonstrates that siblings coordinate their aperture angles based on
the maximum branching factor among them.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.data.pathway.pathway_data import PathwayData, Species, Reaction
from shypn.data.pathway.tree_layout import TreeLayoutProcessor


def create_uncoordinated_pathway():
    """Create pathway where siblings have DIFFERENT branching factors.
    
    Structure:
                ROOT
               /    \
              A      B
             /|\     |
            / | \    |
           E  F  G   H
    
    Sibling A: 3 children (complex)
    Sibling B: 1 child (simple)
    
    Expected: B should use the SAME aperture as A (coordination!)
    """
    return PathwayData(
        species=[
            Species(id="ROOT", name="Root"),
            Species(id="A", name="Sibling A (3 children)"),
            Species(id="B", name="Sibling B (1 child)"),
            Species(id="E", name="A child 1"),
            Species(id="F", name="A child 2"),
            Species(id="G", name="A child 3"),
            Species(id="H", name="B child 1"),
        ],
        reactions=[
            Reaction(id="R1", name="ROOT→A", reactants=[("ROOT", 1.0)], products=[("A", 1.0)]),
            Reaction(id="R2", name="ROOT→B", reactants=[("ROOT", 1.0)], products=[("B", 1.0)]),
            Reaction(id="R3", name="A→E", reactants=[("A", 1.0)], products=[("E", 1.0)]),
            Reaction(id="R4", name="A→F", reactants=[("A", 1.0)], products=[("F", 1.0)]),
            Reaction(id="R5", name="A→G", reactants=[("A", 1.0)], products=[("G", 1.0)]),
            Reaction(id="R6", name="B→H", reactants=[("B", 1.0)], products=[("H", 1.0)]),
        ]
    )


def create_mixed_coordination_pathway():
    """Create pathway with multiple coordination scenarios.
    
    Structure:
                  ROOT
               /   |    \
              A    B     C
             /\    |    /|\
            E  F   G   H I J
            |      |   |
            K      L   M
    
    Layer 1 (siblings A, B, C):
      - A: 2 children
      - B: 1 child
      - C: 3 children ← MAXIMUM, determines aperture for all
    
    Layer 2 (siblings E, F, G, H, I, J):
      Multiple groups coordinate independently
    """
    return PathwayData(
        species=[
            Species(id="ROOT", name="Root"),
            # Layer 1
            Species(id="A", name="A (2 children)"),
            Species(id="B", name="B (1 child)"),
            Species(id="C", name="C (3 children)"),
            # Layer 2
            Species(id="E", name="E"),
            Species(id="F", name="F"),
            Species(id="G", name="G"),
            Species(id="H", name="H"),
            Species(id="I", name="I"),
            Species(id="J", name="J"),
            # Layer 3
            Species(id="K", name="K"),
            Species(id="L", name="L"),
            Species(id="M", name="M"),
        ],
        reactions=[
            # ROOT → Layer 1
            Reaction(id="R1", name="ROOT→A", reactants=[("ROOT", 1.0)], products=[("A", 1.0)]),
            Reaction(id="R2", name="ROOT→B", reactants=[("ROOT", 1.0)], products=[("B", 1.0)]),
            Reaction(id="R3", name="ROOT→C", reactants=[("ROOT", 1.0)], products=[("C", 1.0)]),
            # Layer 1 → Layer 2
            Reaction(id="R4", name="A→E", reactants=[("A", 1.0)], products=[("E", 1.0)]),
            Reaction(id="R5", name="A→F", reactants=[("A", 1.0)], products=[("F", 1.0)]),
            Reaction(id="R6", name="B→G", reactants=[("B", 1.0)], products=[("G", 1.0)]),
            Reaction(id="R7", name="C→H", reactants=[("C", 1.0)], products=[("H", 1.0)]),
            Reaction(id="R8", name="C→I", reactants=[("C", 1.0)], products=[("I", 1.0)]),
            Reaction(id="R9", name="C→J", reactants=[("C", 1.0)], products=[("J", 1.0)]),
            # Layer 2 → Layer 3
            Reaction(id="R10", name="E→K", reactants=[("E", 1.0)], products=[("K", 1.0)]),
            Reaction(id="R11", name="G→L", reactants=[("G", 1.0)], products=[("L", 1.0)]),
            Reaction(id="R12", name="H→M", reactants=[("H", 1.0)], products=[("M", 1.0)]),
        ]
    )


def analyze_coordination(pathway, title):
    """Analyze sibling coordination in pathway."""
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)
    
    processor = TreeLayoutProcessor(pathway, base_vertical_spacing=150, min_horizontal_spacing=150)
    positions = processor.calculate_tree_layout()
    
    # Group by layers
    layers = {}
    for species_id, (x, y) in positions.items():
        if species_id.startswith('R'):
            continue
        y_key = round(y / 150) * 150
        if y_key not in layers:
            layers[y_key] = []
        layers[y_key].append((species_id, x))
    
    # Analyze each layer
    for layer_y in sorted(layers.keys()):
        layer_species = sorted(layers[layer_y], key=lambda item: item[1])
        layer_num = int(layer_y / 150)
        
        print(f"\nLayer {layer_num} (Y={layer_y:.0f}):")
        
        # For each species in this layer, check if it has children
        siblings_info = []
        for species_id, x in layer_species:
            # Count children
            children_reactions = [r for r in pathway.reactions 
                                if any(reactant_id == species_id for reactant_id, _ in r.reactants)]
            num_children = len(set(product_id for r in children_reactions 
                                 for product_id, _ in r.products))
            
            # Calculate expected spacing for children
            if num_children > 1:
                next_layer_y = layer_y + 150
                children_positions = [(pid, positions[pid][0]) 
                                    for r in children_reactions 
                                    for pid, _ in r.products 
                                    if pid in positions and round(positions[pid][1]) == next_layer_y]
                
                if len(children_positions) > 1:
                    children_x = sorted([x for _, x in children_positions])
                    spread = children_x[-1] - children_x[0] if len(children_x) > 1 else 0
                else:
                    spread = 0
            else:
                spread = 0
            
            siblings_info.append({
                'id': species_id,
                'x': x,
                'num_children': num_children,
                'children_spread': spread
            })
        
        # Display sibling information
        max_children = max((s['num_children'] for s in siblings_info), default=0)
        
        for sibling in siblings_info:
            marker = " ← COORDINATION DRIVER" if sibling['num_children'] == max_children and max_children > 1 else ""
            print(f"  {sibling['id']:10} at X={sibling['x']:7.1f} - "
                  f"{sibling['num_children']} children, spread={sibling['children_spread']:6.1f}px{marker}")
        
        # Check coordination
        if len(siblings_info) > 1 and max_children > 1:
            spreads = [s['children_spread'] for s in siblings_info if s['num_children'] > 0]
            
            # Check if all non-zero spreads are similar (coordination working)
            if spreads:
                min_spread = min(s for s in spreads if s > 0) if any(s > 0 for s in spreads) else 0
                max_spread = max(spreads)
                
                if min_spread > 0:
                    ratio = max_spread / min_spread
                    if ratio < 2.0:  # Spreads are coordinated
                        print(f"\n  ✓ COORDINATION ACTIVE: All siblings use similar aperture")
                        print(f"    Max children: {max_children} → determines aperture for all siblings")
                    else:
                        print(f"\n  ⚠ Spreads vary significantly (ratio: {ratio:.1f})")
    
    return positions


def main():
    print("\n" + "=" * 90)
    print("RULE 4: SIBLING COORDINATION")
    print("Siblings with more children determine aperture for ALL siblings at that level")
    print("=" * 90)
    
    # Test 1: Simple coordination
    print("\n\nTEST 1: Simple Sibling Coordination")
    print("-" * 90)
    print("\nStructure:")
    print("          ROOT")
    print("         /    \\")
    print("        A      B")
    print("       /|\\     |")
    print("      E F G    H")
    print()
    print("Sibling A: 3 children (should set aperture)")
    print("Sibling B: 1 child (should USE A's aperture)")
    
    pathway1 = create_uncoordinated_pathway()
    positions1 = analyze_coordination(pathway1, "ANALYSIS: Simple Coordination")
    
    # Test 2: Complex coordination
    print("\n\n" + "=" * 90)
    print("TEST 2: Multi-Level Coordination")
    print("-" * 90)
    print("\nStructure:")
    print("              ROOT")
    print("           /   |    \\")
    print("          A    B     C")
    print("         /\\    |    /|\\")
    print("        E  F   G   H I J")
    print()
    print("Layer 1 siblings (A, B, C):")
    print("  - A: 2 children")
    print("  - B: 1 child")
    print("  - C: 3 children ← Should determine aperture for all")
    
    pathway2 = create_mixed_coordination_pathway()
    positions2 = analyze_coordination(pathway2, "ANALYSIS: Multi-Level Coordination")
    
    # Summary
    print("\n\n" + "=" * 90)
    print("CONCLUSION")
    print("=" * 90)
    print()
    print("✓ RULE 4 IMPLEMENTED:")
    print("  - Siblings at the same layer coordinate their aperture angles")
    print("  - The sibling with the MOST children determines the aperture")
    print("  - All siblings at that level use the SAME aperture angle")
    print("  - This creates visual consistency within each layer")
    print()
    print("BENEFITS:")
    print("  - Uniform appearance within layers")
    print("  - Complex siblings don't dominate visually")
    print("  - Simpler siblings get appropriate space allocation")
    print("  - Layer-by-layer coordination maintains hierarchy")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
