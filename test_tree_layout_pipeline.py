#!/usr/bin/env python3
"""
Test that tree layout is actually being used in the full pipeline.

This test verifies that the use_tree_layout flag flows through:
PathwayPostProcessor → LayoutProcessor → BiochemicalLayoutProcessor → TreeLayoutProcessor
"""

import sys
sys.path.insert(0, 'src')

from shypn.data.pathway.pathway_data import PathwayData, Species, Reaction
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor


def create_test_pathway():
    """Create a simple 1→3 branching pathway."""
    pathway = PathwayData()
    
    # Root
    root = Species(id="A", name="A", initial_concentration=1.0)
    pathway.species.append(root)
    
    # 3 children
    for i in range(3):
        child = Species(id=f"B{i}", name=f"B{i}", initial_concentration=0.0)
        pathway.species.append(child)
        
        reaction = Reaction(
            id=f"r{i}",
            name=f"R{i}",
            reactants=[(root.id, 1.0)],
            products=[(child.id, 1.0)]
        )
        pathway.reactions.append(reaction)
    
    return pathway


def test_tree_layout_pipeline():
    """Test that tree layout is actually used."""
    print("=" * 80)
    print("Testing Tree Layout Pipeline Integration")
    print("=" * 80)
    
    pathway = create_test_pathway()
    
    # Test 1: Fixed spacing (default)
    print("\n1. Testing with FIXED spacing (use_tree_layout=False):")
    print("-" * 80)
    processor_fixed = PathwayPostProcessor(
        spacing=150.0,
        scale_factor=1.0,
        use_tree_layout=False
    )
    processed_fixed = processor_fixed.process(pathway)
    
    print(f"   Layout type: {processed_fixed.metadata.get('layout_type', 'unknown')}")
    print(f"   Positions count: {len(processed_fixed.positions)}")
    
    # Get child positions
    children_fixed = {k: v for k, v in processed_fixed.positions.items() if k.startswith('B')}
    children_fixed_sorted = sorted(children_fixed.items(), key=lambda x: x[1][0])
    
    print(f"   Child positions:")
    for id, (x, y) in children_fixed_sorted:
        print(f"      {id}: x={x:.1f}px")
    
    # Calculate spacings
    if len(children_fixed_sorted) > 1:
        spacings_fixed = []
        for i in range(len(children_fixed_sorted) - 1):
            x1 = children_fixed_sorted[i][1][0]
            x2 = children_fixed_sorted[i+1][1][0]
            spacing = x2 - x1
            spacings_fixed.append(spacing)
        print(f"   Spacings: {[f'{s:.1f}px' for s in spacings_fixed]}")
    
    # Test 2: Tree layout
    print("\n2. Testing with TREE layout (use_tree_layout=True):")
    print("-" * 80)
    processor_tree = PathwayPostProcessor(
        spacing=150.0,
        scale_factor=1.0,
        use_tree_layout=True
    )
    processed_tree = processor_tree.process(pathway)
    
    print(f"   Layout type: {processed_tree.metadata.get('layout_type', 'unknown')}")
    print(f"   Positions count: {len(processed_tree.positions)}")
    
    # Get child positions
    children_tree = {k: v for k, v in processed_tree.positions.items() if k.startswith('B')}
    children_tree_sorted = sorted(children_tree.items(), key=lambda x: x[1][0])
    
    print(f"   Child positions:")
    for id, (x, y) in children_tree_sorted:
        print(f"      {id}: x={x:.1f}px")
    
    # Calculate spacings
    if len(children_tree_sorted) > 1:
        spacings_tree = []
        for i in range(len(children_tree_sorted) - 1):
            x1 = children_tree_sorted[i][1][0]
            x2 = children_tree_sorted[i+1][1][0]
            spacing = x2 - x1
            spacings_tree.append(spacing)
        print(f"   Spacings: {[f'{s:.1f}px' for s in spacings_tree]}")
    
    # Verification
    print("\n" + "=" * 80)
    print("VERIFICATION:")
    print("=" * 80)
    
    # Check layout types are different
    layout_fixed = processed_fixed.metadata.get('layout_type', 'unknown')
    layout_tree = processed_tree.metadata.get('layout_type', 'unknown')
    
    print(f"\n1. Layout types:")
    print(f"   Fixed: {layout_fixed}")
    print(f"   Tree:  {layout_tree}")
    
    if layout_tree == 'hierarchical-tree':
        print(f"   ✅ Tree layout IS being used (metadata correct)")
    else:
        print(f"   ❌ Tree layout NOT being used (metadata shows: {layout_tree})")
        return False
    
    # Check spacings are different
    if len(children_fixed_sorted) > 1 and len(children_tree_sorted) > 1:
        avg_spacing_fixed = sum(spacings_fixed) / len(spacings_fixed)
        avg_spacing_tree = sum(spacings_tree) / len(spacings_tree)
        
        print(f"\n2. Average spacings:")
        print(f"   Fixed: {avg_spacing_fixed:.1f}px")
        print(f"   Tree:  {avg_spacing_tree:.1f}px")
        
        # Tree layout with 3 children should have wider spacing
        # Expected: ~234px vs ~105px (fixed horizontal_spacing * 0.7)
        if avg_spacing_tree > avg_spacing_fixed * 1.5:
            print(f"   ✅ Tree layout produces WIDER spacing (dramatic scaling)")
        else:
            print(f"   ⚠️  Tree spacing not dramatically different")
    
    # Check positions are actually different
    positions_different = False
    for (id1, pos1), (id2, pos2) in zip(children_fixed_sorted, children_tree_sorted):
        if abs(pos1[0] - pos2[0]) > 10:  # More than 10px difference
            positions_different = True
            break
    
    print(f"\n3. Position differences:")
    if positions_different:
        print(f"   ✅ Positions ARE different between fixed and tree layout")
    else:
        print(f"   ❌ Positions are THE SAME (tree layout not working)")
        return False
    
    print("\n" + "=" * 80)
    print("✅ ALL CHECKS PASSED: Tree layout is working in the pipeline!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    try:
        success = test_tree_layout_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
