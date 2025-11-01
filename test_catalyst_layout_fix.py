#!/usr/bin/env python3
"""
Test that catalyst places are properly excluded from layer 0 in hierarchical layout.

This test verifies the fix for the layout flattening issue.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

import networkx as nx
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc
from shypn.netobjs.test_arc import TestArc
from shypn.edit.graph_layout.hierarchical import HierarchicalLayout


def test_catalyst_exclusion():
    """Test that catalysts are excluded from layer 0."""
    
    print("=" * 80)
    print("TEST: Catalyst Exclusion from Layer 0")
    print("=" * 80)
    
    # Create a simple pathway with catalyst
    # Substrate → Reaction → Product
    #   ↑ (test arc from enzyme)
    
    substrate = Place(id="P1", name="Substrate", x=0, y=0)
    enzyme = Place(id="P2", name="Enzyme", x=0, y=0)
    enzyme.is_catalyst = True  # ← CRITICAL: Mark as catalyst
    product = Place(id="P3", name="Product", x=0, y=0)
    
    reaction = Transition(id="T1", name="Reaction", x=0, y=0)
    
    # Build NetworkX graph (as done by LayoutEngine)
    graph = nx.DiGraph()
    
    # Add nodes using actual objects (as LayoutEngine does)
    graph.add_node(substrate, type='place')
    graph.add_node(enzyme, type='place')
    graph.add_node(product, type='place')
    graph.add_node(reaction, type='transition')
    
    # Add edges
    # Normal arcs: Substrate → Reaction → Product
    graph.add_edge(substrate, reaction, weight=1)
    graph.add_edge(reaction, product, weight=1)
    
    # Test arc: Enzyme → Reaction (catalyst)
    graph.add_edge(enzyme, reaction, weight=1)
    
    print(f"\n📊 Graph Structure:")
    print(f"   Nodes: {graph.number_of_nodes()}")
    print(f"   Edges: {graph.number_of_edges()}")
    print(f"\n   Substrate: in_degree={graph.in_degree(substrate)}, out_degree={graph.out_degree(substrate)}")
    print(f"   Enzyme (catalyst): in_degree={graph.in_degree(enzyme)}, out_degree={graph.out_degree(enzyme)}")
    print(f"   Product: in_degree={graph.in_degree(product)}, out_degree={graph.out_degree(product)}")
    print(f"   Reaction: in_degree={graph.in_degree(reaction)}, out_degree={graph.out_degree(reaction)}")
    
    # Create layout algorithm instance
    algo = HierarchicalLayout()
    
    # Call get_layer_assignment (the method we fixed)
    layers = algo.get_layer_assignment(graph)
    
    print(f"\n🔍 Layer Assignments:")
    for node, layer in sorted(layers.items(), key=lambda x: x[1]):
        node_name = getattr(node, 'name', 'Unknown')
        is_catalyst = getattr(node, 'is_catalyst', False)
        catalyst_marker = " (CATALYST)" if is_catalyst else ""
        print(f"   Layer {layer}: {node_name}{catalyst_marker}")
    
    # Verify results
    substrate_layer = layers[substrate]
    enzyme_layer = layers[enzyme]
    reaction_layer = layers[reaction]
    product_layer = layers[product]
    
    print(f"\n✅ VERIFICATION:")
    print(f"   Substrate layer: {substrate_layer} (expected: 0)")
    print(f"   Enzyme layer: {enzyme_layer} (expected: NOT 0)")
    print(f"   Reaction layer: {reaction_layer} (expected: 1)")
    print(f"   Product layer: {product_layer} (expected: 2)")
    
    # Assertions
    assert substrate_layer == 0, f"Substrate should be at layer 0, got {substrate_layer}"
    assert enzyme_layer != 0, f"Enzyme (catalyst) should NOT be at layer 0, got {enzyme_layer}"
    assert reaction_layer == 1, f"Reaction should be at layer 1, got {reaction_layer}"
    assert product_layer == 2, f"Product should be at layer 2, got {product_layer}"
    assert enzyme_layer == reaction_layer, f"Enzyme should be at same layer as catalyzed reaction, got {enzyme_layer} vs {reaction_layer}"
    
    print(f"\n✓ TEST PASSED!")
    print(f"   Catalyst properly excluded from layer 0")
    print(f"   Catalyst positioned at same layer as catalyzed reaction")
    print(f"   Hierarchical structure preserved")


def test_multiple_catalysts():
    """Test with multiple catalysts to verify no flattening."""
    
    print("\n" + "=" * 80)
    print("TEST: Multiple Catalysts (No Flattening)")
    print("=" * 80)
    
    # Create a pathway with multiple reactions and catalysts
    # S1 → R1 → I1 → R2 → P1
    #  ↑       ↑
    # E1 (catalyst for R1)
    #         E2 (catalyst for R2)
    
    s1 = Place(id="P1", name="S1", x=0, y=0)
    i1 = Place(id="P2", name="I1", x=0, y=0)
    p1 = Place(id="P3", name="P1", x=0, y=0)
    
    e1 = Place(id="P4", name="E1", x=0, y=0)
    e1.is_catalyst = True
    
    e2 = Place(id="P5", name="E2", x=0, y=0)
    e2.is_catalyst = True
    
    r1 = Transition(id="T1", name="R1", x=0, y=0)
    r2 = Transition(id="T2", name="R2", x=0, y=0)
    
    # Build graph
    graph = nx.DiGraph()
    
    for node in [s1, i1, p1, e1, e2, r1, r2]:
        node_type = 'transition' if hasattr(node, 'transition_type') else 'place'
        graph.add_node(node, type=node_type)
    
    # Normal pathway: S1 → R1 → I1 → R2 → P1
    graph.add_edge(s1, r1, weight=1)
    graph.add_edge(r1, i1, weight=1)
    graph.add_edge(i1, r2, weight=1)
    graph.add_edge(r2, p1, weight=1)
    
    # Test arcs (catalysts)
    graph.add_edge(e1, r1, weight=1)
    graph.add_edge(e2, r2, weight=1)
    
    print(f"\n📊 Graph Structure:")
    print(f"   Nodes: {graph.number_of_nodes()}")
    print(f"   Edges: {graph.number_of_edges()}")
    print(f"   Expected layers: S1(0) → R1(1) → I1(2) → R2(3) → P1(4)")
    print(f"   Expected catalyst positions: E1(1), E2(3) - at same layer as reactions")
    
    # Get layer assignment
    algo = HierarchicalLayout()
    layers = algo.get_layer_assignment(graph)
    
    print(f"\n🔍 Layer Assignments:")
    max_layer = max(layers.values())
    for layer_num in range(max_layer + 1):
        nodes_in_layer = [node for node, layer in layers.items() if layer == layer_num]
        node_names = [getattr(node, 'name', 'Unknown') for node in nodes_in_layer]
        catalyst_markers = [" (CATALYST)" if getattr(node, 'is_catalyst', False) else "" for node in nodes_in_layer]
        names_with_markers = [f"{name}{marker}" for name, marker in zip(node_names, catalyst_markers)]
        print(f"   Layer {layer_num}: {', '.join(names_with_markers)}")
    
    # Verify: Should have 5 layers (0-4), not flattened to 3
    num_layers = max_layer + 1
    print(f"\n✅ VERIFICATION:")
    print(f"   Number of layers: {num_layers}")
    print(f"   Expected: 5 layers (clean hierarchy)")
    print(f"   Without fix would be: 3 layers (flattened due to catalysts at layer 0)")
    
    assert num_layers >= 5, f"Should have at least 5 layers, got {num_layers} (layout flattening detected!)"
    assert layers[e1] == layers[r1], f"E1 should be at same layer as R1"
    assert layers[e2] == layers[r2], f"E2 should be at same layer as R2"
    assert layers[e1] != 0, f"E1 (catalyst) should NOT be at layer 0"
    assert layers[e2] != 0, f"E2 (catalyst) should NOT be at layer 0"
    
    print(f"\n✓ TEST PASSED!")
    print(f"   Hierarchical structure preserved ({num_layers} layers)")
    print(f"   Catalysts positioned at reaction layers")
    print(f"   No layout flattening!")


def test_isolated_node_filtering():
    """Test that completely isolated nodes are filtered out."""
    
    print("\n" + "=" * 80)
    print("TEST: Isolated Node Filtering")
    print("=" * 80)
    
    # Create pathway with isolated annotation nodes
    # S1 → R1 → P1
    # (E1 isolated, E2 isolated - no arcs at all)
    
    s1 = Place(id="P1", name="S1", x=0, y=0)
    p1 = Place(id="P2", name="P1", x=0, y=0)
    
    # Isolated places (manual annotations, no arcs)
    e1 = Place(id="P3", name="E1_isolated", x=0, y=0)
    e2 = Place(id="P4", name="E2_isolated", x=0, y=0)
    
    r1 = Transition(id="T1", name="R1", x=0, y=0)
    
    # Build graph
    graph = nx.DiGraph()
    
    for node in [s1, p1, e1, e2, r1]:
        node_type = 'transition' if hasattr(node, 'transition_type') else 'place'
        graph.add_node(node, type=node_type)
    
    # Only pathway arcs: S1 → R1 → P1
    # E1 and E2 have NO arcs at all
    graph.add_edge(s1, r1, weight=1)
    graph.add_edge(r1, p1, weight=1)
    
    print(f"\n📊 Graph Structure:")
    print(f"   Total nodes: {graph.number_of_nodes()}")
    print(f"   S1: degree={graph.degree(s1)}")
    print(f"   P1: degree={graph.degree(p1)}")
    print(f"   E1 (isolated): degree={graph.degree(e1)} ← Should be filtered")
    print(f"   E2 (isolated): degree={graph.degree(e2)} ← Should be filtered")
    print(f"   R1: degree={graph.degree(r1)}")
    
    # Apply hierarchical layout
    from shypn.edit.graph_layout.hierarchical import HierarchicalLayout
    algo = HierarchicalLayout()
    positions = algo.compute(graph)
    
    print(f"\n🔍 Layout Results:")
    print(f"   Positioned nodes: {len(positions)}")
    print(f"   Expected: 3 (S1, R1, P1)")
    print(f"   Isolated nodes filtered: {graph.number_of_nodes() - len(positions)}")
    
    # Verify isolated nodes NOT in layout
    assert s1 in positions, "S1 should be positioned"
    assert r1 in positions, "R1 should be positioned"
    assert p1 in positions, "P1 should be positioned"
    assert e1 not in positions, "E1 (isolated) should NOT be positioned"
    assert e2 not in positions, "E2 (isolated) should NOT be positioned"
    
    print(f"\n✓ TEST PASSED!")
    print(f"   Only connected nodes positioned")
    print(f"   Isolated annotation nodes filtered out")


if __name__ == "__main__":
    try:
        test_catalyst_exclusion()
        test_multiple_catalysts()
        test_isolated_node_filtering()
        
        print("\n" + "=" * 80)
        print("ALL TESTS PASSED! ✅")
        print("=" * 80)
        print("\nFix verified:")
        print("  ✓ Catalyst places excluded from layer 0")
        print("  ✓ Catalysts positioned at same layer as catalyzed reactions")
        print("  ✓ Hierarchical layout preserved (no flattening)")
        print("  ✓ Isolated nodes (no arcs) filtered out")
        print("\nUser can now enable 'Show catalysts' in KEGG imports without layout flattening!")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
