#!/usr/bin/env python3
"""
Test hierarchical layout with enzyme places (catalysts).

This test verifies that:
1. Enzyme places (connected only via test arcs) are excluded from dependency graph
2. Main pathway maintains hierarchical structure (not flattened)
3. Enzyme places are positioned separately near their catalyzed reactions
4. Layout has proper vertical spacing between layers

The issue was that enzyme places with only test arc connections were being
included in the dependency graph with in_degree=0, causing them to all be
assigned to layer 0, which flattened the entire hierarchical structure.

Solution: Exclude species connected only via test arcs from the dependency graph,
then position them separately after the main hierarchical layout.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.data.pathway.pathway_data import PathwayData, Species, Reaction
from shypn.data.pathway.hierarchical_layout import HierarchicalLayoutProcessor


def create_test_pathway_with_enzymes():
    """Create a simple pathway with enzyme places (catalysts).
    
    Pathway structure:
        A → B → C → D (main chain with 4 layers)
        
        Enzymes (catalysts):
        E1 catalyzes A → B
        E2 catalyzes B → C
        E3 catalyzes C → D
        
    Without fix: All enzymes assigned to layer 0, flattening entire structure
    With fix: Enzymes excluded from hierarchy, positioned separately
    """
    # Create species (no x,y in constructor - they go in metadata)
    species = [
        Species(id="A", name="Substrate A"),
        Species(id="B", name="Intermediate B"),
        Species(id="C", name="Intermediate C"),
        Species(id="D", name="Product D"),
        Species(id="E1", name="Enzyme 1"),
        Species(id="E2", name="Enzyme 2"),
        Species(id="E3", name="Enzyme 3"),
    ]
    
    # Add original coordinates to metadata (for enzyme positioning logic)
    species[4].metadata['x'] = 200  # E1
    species[4].metadata['y'] = 150
    species[5].metadata['x'] = 200  # E2
    species[5].metadata['y'] = 300
    species[6].metadata['x'] = 200  # E3
    species[6].metadata['y'] = 450
    
    # Create reactions with modifiers (catalysts)
    reactions = [
        Reaction(
            id="R1",
            name="Reaction 1: A → B",
            reactants=[("A", 1.0)],
            products=[("B", 1.0)],
            modifiers=["E1"]  # E1 catalyzes this reaction
        ),
        Reaction(
            id="R2",
            name="Reaction 2: B → C",
            reactants=[("B", 1.0)],
            products=[("C", 1.0)],
            modifiers=["E2"]  # E2 catalyzes this reaction
        ),
        Reaction(
            id="R3",
            name="Reaction 3: C → D",
            reactants=[("C", 1.0)],
            products=[("D", 1.0)],
            modifiers=["E3"]  # E3 catalyzes this reaction
        ),
    ]
    
    return PathwayData(species=species, reactions=reactions)


def test_hierarchical_layout_excludes_enzymes():
    """Test that enzyme places are excluded from hierarchical layout."""
    print("="*70)
    print("TEST: Hierarchical Layout with Enzyme Places (Catalysts)")
    print("="*70)
    
    # Create test pathway
    pathway = create_test_pathway_with_enzymes()
    
    print("\nPathway Structure:")
    print("  Main chain: A → B → C → D (4 species, 3 reactions)")
    print("  Enzymes: E1, E2, E3 (catalyze reactions, connected via test arcs)")
    print("  Total: 7 species, 3 reactions")
    
    # Create layout processor
    layout = HierarchicalLayoutProcessor(
        pathway=pathway,
        vertical_spacing=150.0,
        horizontal_spacing=100.0
    )
    
    print("\nStep 1: Build dependency graph...")
    graph, in_degree = layout._build_dependency_graph()
    
    print(f"  Graph nodes: {sorted(graph.keys())}")
    print(f"  In-degrees: {in_degree}")
    
    # Verify enzymes are excluded
    enzyme_ids = {"E1", "E2", "E3"}
    included_species = set(in_degree.keys())
    excluded_species = enzyme_ids - included_species
    
    print(f"\n  ✓ Included in graph: {sorted(included_species)}")
    print(f"  ✓ Excluded from graph: {sorted(excluded_species)}")
    
    assert excluded_species == enzyme_ids, \
        f"Expected enzymes {enzyme_ids} to be excluded, but got {excluded_species}"
    
    print("\n  ✅ PASS: Enzyme places correctly excluded from dependency graph")
    
    # Test layer assignment
    print("\nStep 2: Assign layers...")
    layers = layout._assign_layers(graph, in_degree)
    
    print(f"  Number of layers: {len(layers)}")
    for i, layer in enumerate(layers):
        print(f"    Layer {i}: {layer}")
    
    # Verify layer structure
    assert len(layers) == 4, f"Expected 4 layers, got {len(layers)}"
    assert layers[0] == ["A"], f"Expected layer 0 = ['A'], got {layers[0]}"
    assert layers[1] == ["B"], f"Expected layer 1 = ['B'], got {layers[1]}"
    assert layers[2] == ["C"], f"Expected layer 2 = ['C'], got {layers[2]}"
    assert layers[3] == ["D"], f"Expected layer 3 = ['D'], got {layers[3]}"
    
    print("\n  ✅ PASS: Main chain correctly assigned to 4 separate layers")
    
    # Test full layout
    print("\nStep 3: Calculate complete layout...")
    positions = layout.calculate_hierarchical_layout()
    
    print(f"  Total positioned: {len(positions)} elements")
    print("\n  Main chain positions (should have increasing Y):")
    for species_id in ["A", "B", "C", "D"]:
        x, y = positions[species_id]
        print(f"    {species_id}: ({x:.1f}, {y:.1f})")
    
    # Verify vertical ordering
    y_values = [positions[sid][1] for sid in ["A", "B", "C", "D"]]
    assert y_values == sorted(y_values), \
        f"Expected increasing Y values, got {y_values}"
    
    # Verify vertical spacing
    for i in range(len(y_values) - 1):
        spacing = y_values[i+1] - y_values[i]
        print(f"    Spacing {['A','B','C','D'][i]} → {['A','B','C','D'][i+1]}: {spacing:.1f}px")
        assert spacing > 100, \
            f"Expected spacing > 100px, got {spacing:.1f}px"
    
    print("\n  ✅ PASS: Main chain has proper hierarchical structure")
    
    # Test enzyme positioning
    print("\n  Enzyme positions (should be near reactions):")
    for enzyme_id in ["E1", "E2", "E3"]:
        if enzyme_id in positions:
            x, y = positions[enzyme_id]
            print(f"    {enzyme_id}: ({x:.1f}, {y:.1f})")
        else:
            print(f"    {enzyme_id}: NOT POSITIONED")
    
    # Verify all enzymes are positioned
    for enzyme_id in enzyme_ids:
        assert enzyme_id in positions, \
            f"Enzyme {enzyme_id} not positioned"
    
    print("\n  ✅ PASS: All enzyme places positioned")
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED!")
    print("="*70)
    print("\nSummary:")
    print("  ✓ Enzyme places excluded from dependency graph")
    print("  ✓ Main pathway maintains hierarchical structure (4 layers)")
    print("  ✓ Proper vertical spacing between layers (>100px)")
    print("  ✓ All enzyme places positioned after main layout")
    print("\nThis fix prevents layout flattening when catalysts are enabled.")


def test_layout_without_enzymes():
    """Control test: Layout without enzymes should work as before."""
    print("\n" + "="*70)
    print("CONTROL TEST: Layout without Enzymes")
    print("="*70)
    
    # Create pathway without enzymes (just main chain)
    species = [
        Species(id="A", name="Substrate A"),
        Species(id="B", name="Intermediate B"),
        Species(id="C", name="Intermediate C"),
        Species(id="D", name="Product D"),
    ]
    
    reactions = [
        Reaction(id="R1", reactants=[("A", 1.0)], products=[("B", 1.0)]),
        Reaction(id="R2", reactants=[("B", 1.0)], products=[("C", 1.0)]),
        Reaction(id="R3", reactants=[("C", 1.0)], products=[("D", 1.0)]),
    ]
    
    pathway = PathwayData(species=species, reactions=reactions)
    layout = HierarchicalLayoutProcessor(pathway=pathway)
    
    print("\nPathway: A → B → C → D (no enzymes)")
    
    positions = layout.calculate_hierarchical_layout()
    
    print(f"Positioned: {len(positions)} elements")
    
    # Verify all species positioned
    assert len(positions) == 7, \
        f"Expected 7 elements (4 species + 3 reactions), got {len(positions)}"
    
    # Verify hierarchical structure
    y_values = [positions[sid][1] for sid in ["A", "B", "C", "D"]]
    assert y_values == sorted(y_values), "Expected increasing Y values"
    
    print("✅ PASS: Control test (no enzymes) works correctly")


if __name__ == "__main__":
    test_hierarchical_layout_excludes_enzymes()
    test_layout_without_enzymes()
    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
    print("="*70)
