#!/usr/bin/env python3
"""
Test Hierarchical Layout for Biochemical Pathways

Tests the hierarchical layout algorithm that creates top-to-bottom
layouts based on reaction dependencies.

Expected: Linear pathway should be laid out vertically with layers
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.data.pathway.pathway_data import PathwayData, Species, Reaction
from shypn.data.pathway.hierarchical_layout import (
    HierarchicalLayoutProcessor,
    BiochemicalLayoutProcessor
)


def create_linear_pathway():
    """Create simple linear pathway: A → B → C → D"""
    pathway = PathwayData(
        species=[
            Species(id="A", name="Compound A", compartment="c", initial_concentration=10.0),
            Species(id="B", name="Compound B", compartment="c", initial_concentration=0.0),
            Species(id="C", name="Compound C", compartment="c", initial_concentration=0.0),
            Species(id="D", name="Compound D", compartment="c", initial_concentration=0.0),
        ],
        reactions=[
            Reaction(
                id="R1",
                name="A to B",
                reactants=[("A", 1.0)],
                products=[("B", 1.0)],
                reversible=False
            ),
            Reaction(
                id="R2",
                name="B to C",
                reactants=[("B", 1.0)],
                products=[("C", 1.0)],
                reversible=False
            ),
            Reaction(
                id="R3",
                name="C to D",
                reactants=[("C", 1.0)],
                products=[("D", 1.0)],
                reversible=False
            ),
        ]
    )
    return pathway


def create_branched_pathway():
    """Create branched pathway:
         A
        / \\
       B   C
        \\ /
         D
    """
    pathway = PathwayData(
        species=[
            Species(id="A", name="Compound A", compartment="c", initial_concentration=10.0),
            Species(id="B", name="Compound B", compartment="c", initial_concentration=0.0),
            Species(id="C", name="Compound C", compartment="c", initial_concentration=0.0),
            Species(id="D", name="Compound D", compartment="c", initial_concentration=0.0),
        ],
        reactions=[
            Reaction(
                id="R1",
                name="A to B",
                reactants=[("A", 1.0)],
                products=[("B", 1.0)],
                reversible=False
            ),
            Reaction(
                id="R2",
                name="A to C",
                reactants=[("A", 1.0)],
                products=[("C", 1.0)],
                reversible=False
            ),
            Reaction(
                id="R3",
                name="B to D",
                reactants=[("B", 1.0)],
                products=[("D", 1.0)],
                reversible=False
            ),
            Reaction(
                id="R4",
                name="C to D",
                reactants=[("C", 1.0)],
                products=[("D", 1.0)],
                reversible=False
            ),
        ]
    )
    return pathway


def test_linear_pathway():
    """Test hierarchical layout on linear pathway."""
    print("=" * 60)
    print("TEST 1: Linear Pathway (A → B → C → D)")
    print("=" * 60)
    
    pathway = create_linear_pathway()
    processor = HierarchicalLayoutProcessor(pathway, vertical_spacing=150, horizontal_spacing=100)
    
    positions = processor.calculate_hierarchical_layout()
    
    print("\nLayer Assignment:")
    print("-" * 60)
    
    # Extract Y positions to determine layers
    species_y = {sid: y for sid, (x, y) in positions.items() if sid in ['A', 'B', 'C', 'D']}
    sorted_species = sorted(species_y.items(), key=lambda x: x[1])
    
    for i, (species_id, y) in enumerate(sorted_species):
        print(f"Layer {i}: {species_id} at Y={y:.1f}")
    
    # Check ordering: A should be topmost, D should be bottommost
    assert sorted_species[0][0] == 'A', "A should be in layer 0 (top)"
    assert sorted_species[1][0] == 'B', "B should be in layer 1"
    assert sorted_species[2][0] == 'C', "C should be in layer 2"
    assert sorted_species[3][0] == 'D', "D should be in layer 3 (bottom)"
    
    print("\n✓ Linear pathway correctly ordered top-to-bottom")
    
    return positions


def test_branched_pathway():
    """Test hierarchical layout on branched pathway."""
    print("\n" + "=" * 60)
    print("TEST 2: Branched Pathway")
    print("=" * 60)
    print("Structure:")
    print("     A")
    print("    / \\")
    print("   B   C")
    print("    \\ /")
    print("     D")
    
    pathway = create_branched_pathway()
    processor = HierarchicalLayoutProcessor(pathway, vertical_spacing=150, horizontal_spacing=100)
    
    positions = processor.calculate_hierarchical_layout()
    
    print("\nLayer Assignment:")
    print("-" * 60)
    
    # Group by Y position (layer)
    layers = {}
    for species_id in ['A', 'B', 'C', 'D']:
        if species_id in positions:
            x, y = positions[species_id]
            y_key = round(y, 1)  # Round to handle floating point
            if y_key not in layers:
                layers[y_key] = []
            layers[y_key].append((species_id, x))
    
    for i, (y, species_list) in enumerate(sorted(layers.items())):
        species_names = [f"{sid}(X={x:.1f})" for sid, x in sorted(species_list)]
        print(f"Layer {i} (Y={y:.1f}): {', '.join(species_names)}")
    
    # Check structure
    species_y = {sid: y for sid, (x, y) in positions.items() if sid in ['A', 'B', 'C', 'D']}
    
    # A should be at top
    assert species_y['A'] < species_y['B'], "A should be above B"
    assert species_y['A'] < species_y['C'], "A should be above C"
    
    # B and C should be at same level (parallel branches)
    assert abs(species_y['B'] - species_y['C']) < 1.0, "B and C should be at same layer"
    
    # D should be at bottom
    assert species_y['D'] > species_y['B'], "D should be below B"
    assert species_y['D'] > species_y['C'], "D should be below C"
    
    print("\n✓ Branched pathway correctly structured in layers")
    
    return positions


def test_pathway_type_detection():
    """Test automatic pathway type detection."""
    print("\n" + "=" * 60)
    print("TEST 3: Pathway Type Detection")
    print("=" * 60)
    
    linear = create_linear_pathway()
    branched = create_branched_pathway()
    
    processor_linear = BiochemicalLayoutProcessor(linear)
    processor_branched = BiochemicalLayoutProcessor(branched)
    
    type_linear = processor_linear._analyze_pathway_type()
    type_branched = processor_branched._analyze_pathway_type()
    
    print(f"\nLinear pathway detected as: {type_linear}")
    print(f"Branched pathway detected as: {type_branched}")
    
    assert type_linear == "hierarchical", "Linear pathway should be detected as hierarchical"
    assert type_branched == "hierarchical", "Branched pathway should be detected as hierarchical"
    
    print("\n✓ Pathway types correctly detected")


def main():
    """Run all hierarchical layout tests."""
    print("\n" + "=" * 60)
    print("HIERARCHICAL LAYOUT TEST SUITE")
    print("=" * 60)
    print("\nTesting biochemical layout with reaction ordering...")
    print("Key concept: Reactions occur in order, layout should reflect this\n")
    
    try:
        # Test 1: Linear pathway
        linear_positions = test_linear_pathway()
        
        # Test 2: Branched pathway
        branched_positions = test_branched_pathway()
        
        # Test 3: Type detection
        test_pathway_type_detection()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nHierarchical layout correctly:")
        print("  • Orders species by reaction dependencies")
        print("  • Creates top-to-bottom flow")
        print("  • Places parallel branches at same layer")
        print("  • Detects pathway type automatically")
        print("\nReady for integration with SBML import!")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
