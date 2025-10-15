#!/usr/bin/env python3
"""Test that high branching factors don't cause transition overlap (black bar issue)."""

import sys
import math
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.data.pathway.tree_layout import TreeLayoutProcessor
from shypn.data.pathway.pathway_data import PathwayData, Species, Reaction


def create_high_branching_pathway(num_children: int):
    """Create a pathway with one root and many children (high branching)."""
    pathway = PathwayData()
    
    # Root species
    root = Species(id="root", name="Root", initial_concentration=1.0)
    pathway.species.append(root)
    
    # Many children
    for i in range(num_children):
        child = Species(id=f"child_{i}", name=f"Child {i}", initial_concentration=0.0)
        pathway.species.append(child)
        
        # Reaction: root → child
        # reactants and products are lists of (species_id, stoichiometry) tuples
        reaction = Reaction(
            id=f"r{i}",
            name=f"R{i}",
            reactants=[(root.id, 1.0)],
            products=[(child.id, 1.0)]
        )
        pathway.reactions.append(reaction)
    
    return pathway


def test_high_branching_no_overlap():
    """Test that high branching factors don't cause overlap."""
    print("=" * 80)
    print("Testing High Branching Factors (Black Bar Issue)")
    print("=" * 80)
    
    transition_width = 44.0  # Default transition width
    
    test_cases = [2, 3, 5, 8, 10, 15, 20]
    
    all_passed = True
    
    for num_children in test_cases:
        print(f"\n{'─' * 80}")
        print(f"Testing {num_children}-way branching:")
        print(f"{'─' * 80}")
        
        # Create pathway
        pathway = create_high_branching_pathway(num_children)
        
        # Apply tree layout
        processor = TreeLayoutProcessor(
            pathway,
            base_vertical_spacing=150.0,
            base_aperture_angle=45.0,
            min_horizontal_spacing=150.0
        )
        
        positions = processor.calculate_tree_layout()
        
        # Get child positions (excluding root)
        child_positions = [(id, pos) for id, pos in positions.items() if id.startswith('child_')]
        # VERTICAL TREE: sort by X coordinate (horizontal spread)
        child_positions.sort(key=lambda x: x[1][0])  # Sort by x coordinate
        
        # Calculate aperture angle
        base_aperture_deg = 45.0
        scaling_factor = num_children * 1.0
        desired_aperture_deg = base_aperture_deg * scaling_factor
        
        # Check if capping was applied
        MAX_APERTURE_DEG = 170.0
        capped_aperture_deg = min(desired_aperture_deg, MAX_APERTURE_DEG)
        was_capped = desired_aperture_deg > MAX_APERTURE_DEG
        
        print(f"  Desired aperture: {desired_aperture_deg:.1f}°")
        print(f"  Actual aperture: {capped_aperture_deg:.1f}° {'(CAPPED)' if was_capped else ''}")
        
        # Verify angles are within safe range
        aperture_rad = math.radians(capped_aperture_deg)
        half_aperture = aperture_rad / 2
        max_angle_deg = math.degrees(half_aperture)
        
        print(f"  Child angle range: ±{max_angle_deg:.1f}°")
        
        # Check if within tan() safe domain
        if max_angle_deg > 85.0:
            print(f"  ❌ UNSAFE: Angles exceed ±85° (tan() domain)")
            all_passed = False
            continue
        else:
            print(f"  ✅ SAFE: Angles within tan() domain (±85°)")
        
        # Check spacings (HORIZONTAL for vertical tree)
        if len(child_positions) > 1:
            spacings = []
            for i in range(len(child_positions) - 1):
                x1 = child_positions[i][1][0]
                x2 = child_positions[i+1][1][0]
                spacing = x2 - x1
                spacings.append(spacing)
            
            min_spacing = min(spacings)
            max_spacing = max(spacings)
            avg_spacing = sum(spacings) / len(spacings)
            
            print(f"  Spacings: min={min_spacing:.1f}px, max={max_spacing:.1f}px, avg={avg_spacing:.1f}px")
            
            # Check for overlap
            if min_spacing < 0:
                print(f"  ❌ NEGATIVE SPACING: Positions out of order (tan() wrap-around)")
                all_passed = False
            elif min_spacing < transition_width:
                print(f"  ❌ OVERLAP: Min spacing ({min_spacing:.1f}px) < transition width ({transition_width}px)")
                all_passed = False
            else:
                print(f"  ✅ NO OVERLAP: Min spacing ({min_spacing:.1f}px) >= transition width ({transition_width}px)")
            
            # Verify positions are in ascending order (no wrap-around)
            # VERTICAL TREE: check X coordinates
            x_coords = [pos[1][0] for pos in child_positions]
            is_sorted = all(x_coords[i] <= x_coords[i+1] for i in range(len(x_coords) - 1))
            
            if is_sorted:
                print(f"  ✅ POSITIONS SORTED: No tan() wrap-around")
            else:
                print(f"  ❌ POSITIONS SCRAMBLED: tan() wrap-around detected")
                all_passed = False
            
            # Show some positions (X coords for vertical tree)
            print(f"  Sample positions (x coords):")
            for i in [0, len(child_positions)//2, len(child_positions)-1]:
                if i < len(child_positions):
                    id, (x, y) = child_positions[i]
                    print(f"    {id}: x={x:.1f}px")
        
        # Calculate total spread (HORIZONTAL for vertical tree)
        if len(child_positions) > 1:
            total_spread = child_positions[-1][1][0] - child_positions[0][1][0]
            print(f"  Total horizontal spread: {total_spread:.1f}px")
    
    print(f"\n{'=' * 80}")
    if all_passed:
        print("✅ ALL TESTS PASSED: No overlap, no tan() wrap-around")
        print("The black bar issue is FIXED!")
    else:
        print("❌ SOME TESTS FAILED: Black bar issue still present")
    print(f"{'=' * 80}")
    
    return all_passed


if __name__ == "__main__":
    success = test_high_branching_no_overlap()
    sys.exit(0 if success else 1)
