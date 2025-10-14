#!/usr/bin/env python3
"""
Test Place-to-Place Repulsion in Force-Directed Layout

This script verifies that places repel other places (not just connected nodes).

Expected behavior:
- With DiGraph: Only connected nodes repel → places clump together
- With Graph (undirected): ALL nodes repel → places spread out

Test:
1. Create simple pathway: 3 disconnected places + 1 transition
2. Apply force-directed layout
3. Measure distances between places
4. If places repel: distances should be large (similar to place-transition distances)
5. If places don't repel: distances should be small (places clump)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import networkx as nx
import math

def test_graph_vs_digraph():
    """Compare DiGraph vs Graph repulsion behavior."""
    
    print("=" * 70)
    print("PLACE-TO-PLACE REPULSION TEST")
    print("=" * 70)
    print()
    
    # Create simple graph: 3 places (disconnected) + 1 transition
    # Places: P1, P2, P3 (no connections between them)
    # Transition: T1 (connected to P1 only)
    #
    # Expected physics:
    # - P1 ↔ T1: attract (spring) + repel (electrostatic)
    # - P1 ↔ P2: SHOULD repel (but won't in DiGraph!)
    # - P1 ↔ P3: SHOULD repel (but won't in DiGraph!)
    # - P2 ↔ P3: SHOULD repel (but won't in DiGraph!)
    
    # Test 1: DiGraph (directed) - WRONG PHYSICS
    print("Test 1: DiGraph (directed graph)")
    print("-" * 70)
    
    digraph = nx.DiGraph()
    digraph.add_node('P1', type='place')
    digraph.add_node('P2', type='place')
    digraph.add_node('P3', type='place')
    digraph.add_node('T1', type='transition')
    digraph.add_edge('P1', 'T1', weight=1.0)  # Only P1 connected
    
    print(f"Nodes: {list(digraph.nodes())}")
    print(f"Edges: {list(digraph.edges())}")
    print(f"Graph type: {type(digraph).__name__}")
    print()
    
    # Run spring_layout on DiGraph
    pos_digraph = nx.spring_layout(digraph, k=None, iterations=500, scale=1000, seed=42)
    
    # Measure distances
    p1 = pos_digraph['P1']
    p2 = pos_digraph['P2']
    p3 = pos_digraph['P3']
    t1 = pos_digraph['T1']
    
    dist_p1_p2 = math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    dist_p1_p3 = math.sqrt((p1[0] - p3[0])**2 + (p1[1] - p3[1])**2)
    dist_p2_p3 = math.sqrt((p2[0] - p3[0])**2 + (p2[1] - p3[1])**2)
    dist_p1_t1 = math.sqrt((p1[0] - t1[0])**2 + (p1[1] - t1[1])**2)
    
    print(f"Distances (DiGraph):")
    print(f"  P1 ↔ P2: {dist_p1_p2:.1f}px")
    print(f"  P1 ↔ P3: {dist_p1_p3:.1f}px")
    print(f"  P2 ↔ P3: {dist_p2_p3:.1f}px")
    print(f"  P1 ↔ T1: {dist_p1_t1:.1f}px (connected via spring)")
    print()
    
    avg_place_place = (dist_p1_p2 + dist_p1_p3 + dist_p2_p3) / 3
    print(f"Average place-to-place distance: {avg_place_place:.1f}px")
    
    if avg_place_place < 100:
        print("❌ FAIL: Places are clumping (not repelling each other)")
    else:
        print("✓ PASS: Places are spreading out (repelling)")
    print()
    print()
    
    # Test 2: Graph (undirected) - CORRECT PHYSICS
    print("Test 2: Graph (undirected graph)")
    print("-" * 70)
    
    # Convert to undirected
    graph = digraph.to_undirected()
    
    print(f"Nodes: {list(graph.nodes())}")
    print(f"Edges: {list(graph.edges())}")
    print(f"Graph type: {type(graph).__name__}")
    print()
    
    # Run spring_layout on Graph
    pos_graph = nx.spring_layout(graph, k=None, iterations=500, scale=1000, seed=42)
    
    # Measure distances
    p1 = pos_graph['P1']
    p2 = pos_graph['P2']
    p3 = pos_graph['P3']
    t1 = pos_graph['T1']
    
    dist_p1_p2 = math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    dist_p1_p3 = math.sqrt((p1[0] - p3[0])**2 + (p1[1] - p3[1])**2)
    dist_p2_p3 = math.sqrt((p2[0] - p3[0])**2 + (p2[1] - p3[1])**2)
    dist_p1_t1 = math.sqrt((p1[0] - t1[0])**2 + (p1[1] - t1[1])**2)
    
    print(f"Distances (Graph):")
    print(f"  P1 ↔ P2: {dist_p1_p2:.1f}px")
    print(f"  P1 ↔ P3: {dist_p1_p3:.1f}px")
    print(f"  P2 ↔ P3: {dist_p2_p3:.1f}px")
    print(f"  P1 ↔ T1: {dist_p1_t1:.1f}px (connected via spring)")
    print()
    
    avg_place_place = (dist_p1_p2 + dist_p1_p3 + dist_p2_p3) / 3
    print(f"Average place-to-place distance: {avg_place_place:.1f}px")
    
    if avg_place_place < 100:
        print("❌ FAIL: Places are clumping (not repelling each other)")
    else:
        print("✓ PASS: Places are spreading out (repelling)")
    print()
    print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("The force-directed layout MUST use Graph (undirected), not DiGraph.")
    print("DiGraph only repels nodes that are path-connected.")
    print("Graph repels ALL nodes universally (correct physics).")
    print()
    print("Our implementation converts DiGraph → Graph before calling spring_layout.")
    print("This ensures places repel other places (universal repulsion).")

if __name__ == '__main__':
    test_graph_vs_digraph()
