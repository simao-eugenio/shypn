#!/usr/bin/env python3
"""
Test Hierarchical Layout Improvements

Tests two key improvements:
1. No curved arcs for hierarchical layouts (straight arcs only)
2. Better horizontal spacing within layers (equal spacing)
"""

import sys
import os
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.data.pathway.pathway_data import PathwayData, Species, Reaction
from shypn.data.pathway.hierarchical_layout import HierarchicalLayoutProcessor


def test_horizontal_spacing():
    """Test that species in same layer get equal horizontal spacing."""
    
    print("=" * 70)
    print("TEST: Horizontal Spacing Within Layers")
    print("=" * 70)
    
    # Create pathway with branching (multiple species in same layer)
    pathway = PathwayData(
        species=[
            Species(id="A", name="Substrate"),
            Species(id="B", name="Product B"),
            Species(id="C", name="Product C"),
            Species(id="D", name="Product D"),
            Species(id="E", name="Final Product"),
        ],
        reactions=[
            Reaction(id="R1", name="A to B", reactants=[("A", 1.0)], products=[("B", 1.0)]),
            Reaction(id="R2", name="A to C", reactants=[("A", 1.0)], products=[("C", 1.0)]),
            Reaction(id="R3", name="A to D", reactants=[("A", 1.0)], products=[("D", 1.0)]),
            Reaction(id="R4", name="B+C+D to E", 
                     reactants=[("B", 1.0), ("C", 1.0), ("D", 1.0)], 
                     products=[("E", 1.0)]),
        ]
    )
    
    processor = HierarchicalLayoutProcessor(pathway, vertical_spacing=150, horizontal_spacing=100)
    positions = processor.calculate_hierarchical_layout()
    
    # Analyze layer 1 (B, C, D should be at same Y, evenly spaced)
    layer_1_species = ['B', 'C', 'D']
    layer_1_positions = {sid: positions[sid] for sid in layer_1_species}
    
    print("\nLayer 1 (Products of A):")
    print("-" * 70)
    
    y_values = [y for x, y in layer_1_positions.values()]
    x_values = sorted([x for x, y in layer_1_positions.values()])
    
    # Check same Y coordinate
    assert len(set(y_values)) == 1, "All species in layer should have same Y"
    print(f"✓ All species at same Y: {y_values[0]}")
    
    # Check equal spacing
    if len(x_values) > 1:
        spacings = [x_values[i+1] - x_values[i] for i in range(len(x_values)-1)]
        print(f"\nHorizontal spacings: {spacings}")
        
        # All spacings should be equal (within floating point tolerance)
        spacing_variance = max(spacings) - min(spacings)
        assert spacing_variance < 1.0, f"Spacing should be equal (variance: {spacing_variance})"
        print(f"✓ Equal spacing: {spacings[0]:.1f} pixels")
    
    # Check centering
    center_x = 400.0
    avg_x = sum(x_values) / len(x_values)
    print(f"\nCenter X: {center_x}, Average X: {avg_x:.1f}")
    assert abs(avg_x - center_x) < 10.0, "Layer should be centered"
    print(f"✓ Layer is centered (offset: {abs(avg_x - center_x):.1f} pixels)")
    
    print("\n" + "=" * 70)
    print("✓ HORIZONTAL SPACING TEST PASSED")
    print("=" * 70)
    
    return positions


def test_reaction_positioning():
    """Test that reactions are positioned between layers, not on layers."""
    
    print("\n" + "=" * 70)
    print("TEST: Reaction Positioning Between Layers")
    print("=" * 70)
    
    # Create simple linear pathway
    pathway = PathwayData(
        species=[
            Species(id="S1", name="Species 1"),
            Species(id="S2", name="Species 2"),
            Species(id="S3", name="Species 3"),
        ],
        reactions=[
            Reaction(id="R1", name="S1 to S2", reactants=[("S1", 1.0)], products=[("S2", 1.0)]),
            Reaction(id="R2", name="S2 to S3", reactants=[("S2", 1.0)], products=[("S3", 1.0)]),
        ]
    )
    
    processor = HierarchicalLayoutProcessor(pathway, vertical_spacing=150, horizontal_spacing=100)
    positions = processor.calculate_hierarchical_layout()
    
    print("\nPositions:")
    print("-" * 70)
    
    # Extract species and reaction positions
    species_y = {sid: y for sid, (x, y) in positions.items() if sid.startswith('S')}
    reaction_y = {rid: y for rid, (x, y) in positions.items() if rid.startswith('R')}
    
    for sid in sorted(species_y.keys()):
        x, y = positions[sid]
        print(f"Species {sid}: Y={y:.1f}")
    
    print()
    for rid in sorted(reaction_y.keys()):
        x, y = positions[rid]
        print(f"Reaction {rid}: Y={y:.1f}")
    
    # Check that reactions are between species layers
    print("\nChecking reaction positions:")
    print("-" * 70)
    
    s1_y = species_y['S1']
    s2_y = species_y['S2']
    s3_y = species_y['S3']
    
    r1_y = reaction_y['R1']
    r2_y = reaction_y['R2']
    
    # R1 should be between S1 and S2
    assert s1_y < r1_y < s2_y, f"R1 should be between S1 and S2"
    print(f"✓ R1 (Y={r1_y:.1f}) is between S1 (Y={s1_y:.1f}) and S2 (Y={s2_y:.1f})")
    
    # R2 should be between S2 and S3
    assert s2_y < r2_y < s3_y, f"R2 should be between S2 and S3"
    print(f"✓ R2 (Y={r2_y:.1f}) is between S2 (Y={s2_y:.1f}) and S3 (Y={s3_y:.1f})")
    
    # Reactions should NOT be at same Y as species
    all_species_y = set(species_y.values())
    all_reaction_y = set(reaction_y.values())
    
    overlap = all_species_y.intersection(all_reaction_y)
    assert len(overlap) == 0, f"Reactions should not overlap with species layers: {overlap}"
    print(f"✓ No reactions on species layers (kept separate)")
    
    print("\n" + "=" * 70)
    print("✓ REACTION POSITIONING TEST PASSED")
    print("=" * 70)
    
    return positions


def main():
    """Run improvement tests."""
    
    print("\n" + "=" * 70)
    print("HIERARCHICAL LAYOUT IMPROVEMENTS TEST")
    print("=" * 70)
    print("\nTesting two key improvements:")
    print("  1. Equal horizontal spacing within layers")
    print("  2. Reactions positioned between layers (not on them)")
    print()
    
    try:
        # Test 1: Horizontal spacing
        test_horizontal_spacing()
        
        # Test 2: Reaction positioning
        test_reaction_positioning()
        
        print("\n" + "=" * 70)
        print("ALL IMPROVEMENT TESTS PASSED ✓")
        print("=" * 70)
        print("\nImprovements verified:")
        print("  ✓ Equal spacing between neighbors in each layer")
        print("  ✓ Reactions kept separate from species (between layers)")
        print("  ✓ Layers properly centered horizontally")
        print("\nNote: Arc routing will be disabled for hierarchical layouts")
        print("      (straight arcs look better for vertical flow)")
        
        return 0
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
