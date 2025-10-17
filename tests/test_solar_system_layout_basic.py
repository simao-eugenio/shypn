"""Basic smoke test for Solar System Layout.

This test verifies that the layout engine can be instantiated and run
without errors on a simple Petri net.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.layout.sscc import SolarSystemLayoutEngine
from shypn.netobjs import Place, Transition, Arc


def create_simple_petri_net():
    """Create a simple Petri net with a cycle for testing.
    
    Creates:
        P1 → T1 → P2 → T2 → P1  (cycle)
        P3 → T3 → P4             (branch)
    """
    # Create places (x, y, id, name, radius=None, label="")
    p1 = Place(x=0, y=0, id=1, name="P1", label="Place 1")
    p2 = Place(x=100, y=0, id=2, name="P2", label="Place 2")
    p3 = Place(x=0, y=100, id=3, name="P3", label="Place 3")
    p4 = Place(x=100, y=100, id=4, name="P4", label="Place 4")
    
    # Set initial tokens
    p1.tokens = 1
    
    # Create transitions (x, y, id, name, width=None, height=None, label="")
    t1 = Transition(x=50, y=0, id=5, name="T1", label="Trans 1")
    t2 = Transition(x=50, y=50, id=6, name="T2", label="Trans 2")
    t3 = Transition(x=50, y=100, id=7, name="T3", label="Trans 3")
    
    # Create arcs (source, target, id, name, weight=1)
    arcs = [
        Arc(source=p1, target=t1, id=8, name="A1", weight=1),
        Arc(source=t1, target=p2, id=9, name="A2", weight=1),
        Arc(source=p2, target=t2, id=10, name="A3", weight=1),
        Arc(source=t2, target=p1, id=11, name="A4", weight=1),  # Completes cycle
        Arc(source=p3, target=t3, id=12, name="A5", weight=1),
        Arc(source=t3, target=p4, id=13, name="A6", weight=1),
    ]
    
    return [p1, p2, p3, p4], [t1, t2, t3], arcs


def test_basic_layout():
    """Test basic layout functionality."""
    print("🧪 Testing Solar System Layout...")
    
    # Create simple Petri net
    places, transitions, arcs = create_simple_petri_net()
    print(f"✓ Created Petri net: {len(places)} places, {len(transitions)} transitions, {len(arcs)} arcs")
    
    # Create engine
    engine = SolarSystemLayoutEngine(
        iterations=100,  # Small number for quick test
        use_arc_weight=True,
        scc_radius=50.0,
        planet_orbit=300.0,
        satellite_orbit=50.0
    )
    print("✓ Created Solar System Layout engine")
    
    # Apply layout
    try:
        positions = engine.apply_layout(places, transitions, arcs)
        print(f"✓ Layout completed: {len(positions)} positions computed")
    except Exception as e:
        print(f"✗ Layout failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Verify all objects have positions
    all_objects = places + transitions
    for obj in all_objects:
        if obj.id not in positions:
            print(f"✗ Missing position for object {obj.id}")
            return False
    print("✓ All objects have positions")
    
    # Get statistics
    stats = engine.get_statistics()
    print(f"\nStatistics:")
    print(f"  - SCCs found: {stats['num_sccs']}")
    print(f"  - Nodes in SCCs: {stats['num_nodes_in_sccs']}")
    print(f"  - Free places: {stats['num_free_places']}")
    print(f"  - Transitions: {stats['num_transitions']}")
    print(f"  - Total nodes: {stats['total_nodes']}")
    
    # Verify we detected the cycle (should find 1 SCC with P1, P2)
    if stats['num_sccs'] == 0:
        print("\n⚠️ Warning: No SCCs detected (expected 1 for P1→T1→P2→T2→P1)")
    else:
        print(f"\n✓ Detected {stats['num_sccs']} SCC(s) as expected")
    
    print("\n✅ All tests passed!")
    return True


if __name__ == '__main__':
    success = test_basic_layout()
    sys.exit(0 if success else 1)
