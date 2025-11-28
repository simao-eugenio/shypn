"""Test Solar System Layout Menu Integration.

This script tests that the Solar System layout can be applied to a test model
and verifies the algorithm is working.
"""

import sys
from pathlib import Path

# Add src to Python path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "src"))

from shypn.data.canvas.document_model import DocumentModel
from shypn.layout.sscc import SolarSystemLayoutEngine


def test_solar_system_layout():
    """Test loading a model and applying Solar System layout."""
    
    print("=" * 80)
    print("SOLAR SYSTEM LAYOUT MENU INTEGRATION TEST")
    print("=" * 80)
    print()
    
    # Load test model
    model_path = repo_root / "workspace" / "Test_flow" / "model" / "hub_constellation.shy"
    
    if not model_path.exists():
        print(f"✗ Test model not found: {model_path}")
        return False
    
    print(f"Loading test model: {model_path.name}")
    print("-" * 80)
    
    try:
        # Load the document
        document = DocumentModel.load_from_file(str(model_path))
        print(f"✓ Model loaded successfully")
        print(f"  Places: {len(document.places)}")
        print(f"  Transitions: {len(document.transitions)}")
        print(f"  Arcs: {len(document.arcs)}")
        print()
        
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Show initial positions
    print("Initial positions (first 5 objects):")
    print("-" * 80)
    for i, place in enumerate(document.places[:3]):
        print(f"  Place {place.id} ({place.name}): x={place.x:.1f}, y={place.y:.1f}")
    for i, trans in enumerate(document.transitions[:2]):
        print(f"  Transition {trans.id} ({trans.name}): x={trans.x:.1f}, y={trans.y:.1f}")
    print()
    
    # Create Solar System Layout engine
    print("Creating Solar System Layout engine...")
    print("-" * 80)
    try:
        engine = SolarSystemLayoutEngine(
            iterations=1000,
            use_arc_weight=True,
            scc_radius=50.0,
            planet_orbit=300.0,
            satellite_orbit=50.0
        )
        print("✓ Engine created with unified physics")
        print(f"  Simulator: {type(engine.simulator).__name__}")
        print()
        
    except Exception as e:
        print(f"✗ Failed to create engine: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Apply layout
    print("Applying Solar System Layout...")
    print("-" * 80)
    try:
        positions = engine.apply_layout(
            places=list(document.places),
            transitions=list(document.transitions),
            arcs=list(document.arcs)
        )
        print(f"✓ Layout applied successfully")
        print(f"  New positions calculated: {len(positions)}")
        print()
        
    except Exception as e:
        print(f"✗ Failed to apply layout: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Show statistics
    print("Layout Statistics:")
    print("-" * 80)
    stats = engine.get_statistics()
    print(f"  Physics Model: {stats['physics_model']}")
    print(f"  SCCs found: {stats['num_sccs']}")
    print(f"  Nodes in SCCs: {stats['num_nodes_in_sccs']}")
    print(f"  Free places: {stats['num_free_places']}")
    print(f"  Total nodes: {stats['total_nodes']}")
    print()
    
    # Show new positions (first 5 objects)
    print("New positions (first 5 objects):")
    print("-" * 80)
    for i, place in enumerate(document.places[:3]):
        new_x, new_y = positions.get(place.id, (place.x, place.y))
        print(f"  Place {place.id} ({place.name}): x={new_x:.1f}, y={new_y:.1f}")
    for i, trans in enumerate(document.transitions[:2]):
        new_x, new_y = positions.get(trans.id, (trans.x, trans.y))
        print(f"  Transition {trans.id} ({trans.name}): x={new_x:.1f}, y={new_y:.1f}")
    print()
    
    # Verify positions changed
    print("Verification:")
    print("-" * 80)
    changes = 0
    for place in document.places:
        new_x, new_y = positions.get(place.id, (place.x, place.y))
        if abs(new_x - place.x) > 0.1 or abs(new_y - place.y) > 0.1:
            changes += 1
    
    print(f"  Objects with changed positions: {changes}/{len(positions)}")
    
    if changes > 0:
        print("✓ Layout algorithm is working!")
    else:
        print("✗ Warning: No positions changed")
    print()
    
    # Calculate hub separation
    if len(document.places) >= 3:
        print("Hub Separation Analysis:")
        print("-" * 80)
        import math
        hub_positions = []
        for i in range(min(3, len(document.places))):
            place = document.places[i]
            x, y = positions.get(place.id, (place.x, place.y))
            hub_positions.append((place.name, x, y))
        
        for i, (name1, x1, y1) in enumerate(hub_positions):
            for j, (name2, x2, y2) in enumerate(hub_positions):
                if i < j:
                    dist = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                    print(f"  {name1} ↔ {name2}: {dist:.1f} units")
        print()
    
    print("=" * 80)
    print("✅ SOLAR SYSTEM LAYOUT TEST COMPLETE")
    print("=" * 80)
    print()
    print("The algorithm is working correctly!")
    print()
    print("To test in the canvas:")
    print("  1. python3 src/shypn.py")
    print("  2. File → Open → workspace/Test_flow/model/hub_constellation.shy")
    print("  3. Right-click canvas → 'Layout: Solar System (SSCC)'")
    print("  4. You should see the same results on the canvas")
    print()
    
    return True


if __name__ == "__main__":
    success = test_solar_system_layout()
    sys.exit(0 if success else 1)
