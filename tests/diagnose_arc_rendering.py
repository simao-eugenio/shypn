#!/usr/bin/env python3
"""
Diagnostic script to check arc rendering in the model canvas manager.
This helps identify why arcs might not be rendering in the application.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.data.model_canvas_manager import ModelCanvasManager


def test_model_canvas_arcs():
    """Test that ModelCanvasManager properly handles arcs."""
    print("=== Testing ModelCanvasManager Arc Handling ===\n")
    
    # Create manager
    manager = ModelCanvasManager()
    print("✓ ModelCanvasManager created")
    
    # Create test objects
    manager.create_test_objects()
    print(f"✓ Test objects created")
    
    # Check collections
    print(f"\nCollections:")
    print(f"  Places: {len(manager.places)}")
    print(f"  Transitions: {len(manager.transitions)}")
    print(f"  Arcs: {len(manager.arcs)}")
    
    # List all objects
    if manager.places:
        print(f"\nPlaces:")
        for p in manager.places:
            print(f"  - {p.name} at ({p.x}, {p.y}), radius={p.radius}")
    
    if manager.transitions:
        print(f"\nTransitions:")
        for t in manager.transitions:
            print(f"  - {t.name} at ({t.x}, {t.y}), size={t.width}x{t.height}")
    
    if manager.arcs:
        print(f"\nArcs:")
        for a in manager.arcs:
            print(f"  - {a.name}: {a.source.name} → {a.target.name}, weight={a.weight}, color={a.color}, width={a.width}")
    else:
        print(f"\n✗ NO ARCS FOUND!")
    
    # Check get_all_objects
    all_objects = manager.get_all_objects()
    print(f"\nget_all_objects() returns {len(all_objects)} objects")
    
    arc_count = sum(1 for obj in all_objects if obj.__class__.__name__ == 'Arc')
    place_count = sum(1 for obj in all_objects if obj.__class__.__name__ == 'Place')
    trans_count = sum(1 for obj in all_objects if obj.__class__.__name__ == 'Transition')
    
    print(f"  Arcs: {arc_count}")
    print(f"  Places: {place_count}")
    print(f"  Transitions: {trans_count}")
    
    # Check rendering order
    print(f"\nRendering order:")
    for i, obj in enumerate(all_objects):
        print(f"  {i+1}. {obj.__class__.__name__}: {obj.name}")
    
    # Verify arcs come first (should be behind other objects)
    if all_objects:
        first_obj = all_objects[0]
        if first_obj.__class__.__name__ == 'Arc':
            print(f"\n✓ Arcs render first (correct - they appear behind nodes)")
        else:
            print(f"\n✗ WARNING: First object is {first_obj.__class__.__name__}, not Arc")
            print(f"  Arcs may render on top of nodes instead of behind them")
    
    # Test render method existence
    print(f"\nChecking render methods:")
    for obj in all_objects:
        has_render = hasattr(obj, 'render') and callable(getattr(obj, 'render'))
        status = "✓" if has_render else "✗"
        print(f"  {status} {obj.__class__.__name__}.render() exists: {has_render}")
    
    return len(manager.arcs) > 0


def test_arc_visibility():
    """Test factors that might affect arc visibility."""
    print("\n\n=== Testing Arc Visibility Factors ===\n")
    
    manager = ModelCanvasManager()
    manager.create_test_objects()
    
    if not manager.arcs:
        print("✗ No arcs to test!")
        return False
    
    arc = manager.arcs[0]
    
    # Check arc properties that affect visibility
    print(f"Arc {arc.name} properties:")
    print(f"  Source: {arc.source.name} at ({arc.source.x}, {arc.source.y})")
    print(f"  Target: {arc.target.name} at ({arc.target.x}, {arc.target.y})")
    print(f"  Color: {arc.color} (black = (0, 0, 0))")
    print(f"  Width: {arc.width}px")
    print(f"  Weight: {arc.weight}")
    
    # Calculate if arc is visible
    import math
    dx = arc.target.x - arc.source.x
    dy = arc.target.y - arc.source.y
    length = math.sqrt(dx * dx + dy * dy)
    
    print(f"\nVisibility checks:")
    print(f"  Distance between nodes: {length:.1f} units")
    
    if length < 1:
        print(f"  ✗ Arc too short to render (< 1 unit)")
        return False
    else:
        print(f"  ✓ Arc length sufficient")
    
    if arc.color == (0, 0, 0):
        print(f"  ✓ Arc color is black (visible on white background)")
    else:
        print(f"  ? Arc color is {arc.color}")
    
    if arc.width > 0:
        print(f"  ✓ Arc width is {arc.width}px (visible)")
    else:
        print(f"  ✗ Arc width is 0 (invisible!)")
        return False
    
    # Check if source/target are valid
    if arc.source and arc.target:
        print(f"  ✓ Source and target objects exist")
    else:
        print(f"  ✗ Source or target missing!")
        return False
    
    # Check if they have positions
    if hasattr(arc.source, 'x') and hasattr(arc.target, 'x'):
        print(f"  ✓ Source and target have positions")
    else:
        print(f"  ✗ Source or target missing position!")
        return False
    
    return True


def main():
    try:
        arcs_exist = test_model_canvas_arcs()
        arcs_visible = test_arc_visibility()
        
        print("\n\n" + "="*60)
        print("DIAGNOSTIC SUMMARY")
        print("="*60)
        
        if arcs_exist and arcs_visible:
            print("\n✓ Arcs are properly created and should be visible")
            print("\nIf arcs still don't appear in the app, check:")
            print("  1. Cairo context is valid during draw")
            print("  2. Transform function (world_to_screen) works correctly")
            print("  3. Draw callback is being triggered")
            print("  4. No exceptions during render()")
            print("  5. Canvas background isn't covering arcs")
        elif not arcs_exist:
            print("\n✗ PROBLEM: Arcs are not being created!")
            print("  Check: ModelCanvasManager.add_arc() and create_test_objects()")
        elif not arcs_visible:
            print("\n✗ PROBLEM: Arcs exist but have visibility issues!")
            print("  Check: Arc color, width, or coordinates")
        
        print()
        return 0
        
    except Exception as e:
        print(f"\n✗ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
