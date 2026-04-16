#!/usr/bin/env python3
"""
Test layout algorithm optimization for large models.

Tests:
1. Small model (<1000 nodes): Should work normally
2. Medium model (1000-5000 nodes): Should warn and reduce iterations
3. Large model (>5000 nodes): Should refuse layout

Author: Simao Eugenio
Date: 2026-02-03
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.edit.graph_layout import LayoutEngine

def create_test_model(num_nodes):
    """Create a test model with specified number of nodes.
    
    Args:
        num_nodes: Number of places to create
        
    Returns:
        ModelCanvasManager: Test model manager
    """
    manager = ModelCanvasManager(canvas_width=3000, canvas_height=3000)
    
    # Create places in a grid
    grid_size = int(num_nodes ** 0.5) + 1
    spacing = 200
    
    for i in range(num_nodes):
        row = i // grid_size
        col = i % grid_size
        x = col * spacing
        y = row * spacing
        
        place = manager.add_place(x, y, radius=20.0)
        place.label = f"P{i}"
    
    print(f"Created model with {num_nodes} nodes")
    return manager

def test_layout(manager, num_nodes, algorithm='force_directed'):
    """Test layout on a model.
    
    Args:
        manager: ModelCanvasManager instance
        num_nodes: Number of nodes (for reporting)
        algorithm: Layout algorithm to test
    """
    print(f"\n{'='*60}")
    print(f"Testing {algorithm} layout on {num_nodes} nodes")
    print(f"{'='*60}")
    
    engine = LayoutEngine(manager)
    
    # Record initial positions
    initial_positions = {p.id: (p.x, p.y) for p in manager.places}
    
    # Apply layout
    result = engine.apply_layout(algorithm)
    
    # Check result
    if not result.get('success', True):
        print(f"❌ Layout REFUSED: {result.get('message')}")
        return False
    
    # Check if positions changed
    moved = 0
    for place in manager.places:
        old_x, old_y = initial_positions[place.id]
        if abs(place.x - old_x) > 1.0 or abs(place.y - old_y) > 1.0:
            moved += 1
    
    print(f"✅ Layout SUCCEEDED")
    print(f"   Algorithm: {result.get('algorithm', 'unknown')}")
    print(f"   Nodes moved: {result.get('nodes_moved', moved)}")
    print(f"   Reason: {result.get('reason', 'N/A')}")
    
    if 'parameters' in result:
        print(f"   Parameters used: {result['parameters']}")
    
    return True

def main():
    """Run layout optimization tests."""
    print("\n" + "="*60)
    print("Layout Algorithm Optimization Test")
    print("="*60)
    
    # Test 1: Small model (500 nodes) - should work normally
    print("\n\nTest 1: Small Model (500 nodes)")
    print("-" * 60)
    manager1 = create_test_model(500)
    test_layout(manager1, 500)
    
    # Test 2: Medium model (2000 nodes) - should warn and reduce iterations
    print("\n\nTest 2: Medium Model (2000 nodes)")
    print("-" * 60)
    manager2 = create_test_model(2000)
    test_layout(manager2, 2000)
    
    # Test 3: Large model (6000 nodes) - should refuse
    print("\n\nTest 3: Large Model (6000 nodes)")
    print("-" * 60)
    manager3 = create_test_model(6000)
    test_layout(manager3, 6000)
    
    # Test 4: Try hierarchical on large model (should work but warn)
    print("\n\nTest 4: Hierarchical Layout on Large Model (6000 nodes)")
    print("-" * 60)
    test_layout(manager3, 6000, algorithm='hierarchical')
    
    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60)

if __name__ == '__main__':
    main()
