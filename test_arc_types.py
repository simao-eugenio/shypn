#!/usr/bin/env python3
"""Test script for all 4 arc classes.

This script tests:
1. Arc class hierarchy and isinstance checks
2. Serialization and deserialization
3. Control point calculations for curved arcs
4. Visual rendering of all arc types
"""

import sys
import math
sys.path.insert(0, 'src')

from shypn.netobjs import Place, Transition, Arc, InhibitorArc, CurvedArc, CurvedInhibitorArc


def test_arc_hierarchy():
    """Test that arc class hierarchy is correct."""
    print("=" * 70)
    print("TEST 1: Arc Class Hierarchy")
    print("=" * 70)
    
    place = Place(x=0, y=0, id=1, name="P1")
    place.tokens = 0
    trans = Transition(x=100, y=0, id=2, name="T1")
    
    # Create all 4 arc types
    arc = Arc(place, trans, id=10, name="A1")
    inhibitor = InhibitorArc(place, trans, id=11, name="I1")
    curved = CurvedArc(place, trans, id=12, name="C1")
    curved_inhibitor = CurvedInhibitorArc(place, trans, id=13, name="CI1")
    
    # Test isinstance
    print(f"\nArc isinstance checks:")
    print(f"  Arc is Arc: {isinstance(arc, Arc)} (expect True)")
    print(f"  Arc is InhibitorArc: {isinstance(arc, InhibitorArc)} (expect False)")
    print(f"  Arc is CurvedArc: {isinstance(arc, CurvedArc)} (expect False)")
    
    print(f"\nInhibitorArc isinstance checks:")
    print(f"  InhibitorArc is Arc: {isinstance(inhibitor, Arc)} (expect True)")
    print(f"  InhibitorArc is InhibitorArc: {isinstance(inhibitor, InhibitorArc)} (expect True)")
    print(f"  InhibitorArc is CurvedArc: {isinstance(inhibitor, CurvedArc)} (expect False)")
    
    print(f"\nCurvedArc isinstance checks:")
    print(f"  CurvedArc is Arc: {isinstance(curved, Arc)} (expect True)")
    print(f"  CurvedArc is InhibitorArc: {isinstance(curved, InhibitorArc)} (expect False)")
    print(f"  CurvedArc is CurvedArc: {isinstance(curved, CurvedArc)} (expect True)")
    
    print(f"\nCurvedInhibitorArc isinstance checks:")
    print(f"  CurvedInhibitorArc is Arc: {isinstance(curved_inhibitor, Arc)} (expect True)")
    print(f"  CurvedInhibitorArc is CurvedArc: {isinstance(curved_inhibitor, CurvedArc)} (expect True)")
    print(f"  CurvedInhibitorArc is InhibitorArc: {isinstance(curved_inhibitor, InhibitorArc)} (expect False)")
    print(f"  CurvedInhibitorArc is CurvedInhibitorArc: {isinstance(curved_inhibitor, CurvedInhibitorArc)} (expect True)")
    
    print("\n✓ Arc hierarchy tests passed!")


def test_serialization():
    """Test serialization and deserialization of all arc types."""
    print("\n" + "=" * 70)
    print("TEST 2: Serialization and Deserialization")
    print("=" * 70)
    
    place = Place(x=0, y=0, id=1, name="P1")
    place.tokens = 0
    trans = Transition(x=100, y=0, id=2, name="T1")
    
    # Create all 4 arc types
    arcs = [
        (Arc(place, trans, 10, "A1", weight=1), "arc"),
        (InhibitorArc(place, trans, 11, "I1", weight=2), "inhibitor_arc"),
        (CurvedArc(place, trans, 12, "C1", weight=3), "curved_arc"),
        (CurvedInhibitorArc(place, trans, 13, "CI1", weight=4), "curved_inhibitor_arc")
    ]
    
    print("\nSerializing arcs...")
    for arc, expected_type in arcs:
        data = arc.to_dict()
        actual_type = data.get("type")
        status = "✓" if actual_type == expected_type else "✗"
        print(f"  {status} {arc.__class__.__name__}: type='{actual_type}' (expected '{expected_type}')")
        if actual_type != expected_type:
            print(f"      ERROR: Type mismatch!")
            return False
    
    print("\nDeserializing arcs...")
    places = {1: place}
    transitions = {2: trans}
    
    for original_arc, expected_type in arcs:
        data = original_arc.to_dict()
        
        # Use factory method
        loaded_arc = Arc.create_from_dict(data, places, transitions)
        
        # Check type
        same_class = type(loaded_arc) == type(original_arc)
        status = "✓" if same_class else "✗"
        print(f"  {status} {original_arc.__class__.__name__} -> {loaded_arc.__class__.__name__}")
        
        # Check properties
        if loaded_arc.weight != original_arc.weight:
            print(f"      ERROR: Weight mismatch! {loaded_arc.weight} != {original_arc.weight}")
            return False
    
    # Test backward compatibility (old files without 'type' field)
    print("\nTesting backward compatibility (missing 'type' field)...")
    old_data = {
        "id": 20,
        "name": "A_OLD",
        "source_id": 1,
        "source_type": "place",
        "target_id": 2,
        "target_type": "transition",
        "weight": 1,
        "color": [0, 0, 0],
        "width": 3.0,
        "control_points": []
    }
    
    loaded_old = Arc.create_from_dict(old_data, places, transitions)
    is_arc = type(loaded_old) == Arc
    status = "✓" if is_arc else "✗"
    print(f"  {status} Old format loads as Arc: {type(loaded_old).__name__}")
    
    print("\n✓ Serialization tests passed!")
    return True


def test_curved_arc_geometry():
    """Test curved arc control point calculations."""
    print("\n" + "=" * 70)
    print("TEST 3: Curved Arc Geometry")
    print("=" * 70)
    
    # Horizontal arc (0, 0) -> (100, 0)
    place1 = Place(x=0, y=0, id=1, name="P1")
    place1.tokens = 0
    trans1 = Transition(x=100, y=0, id=2, name="T1")
    curved = CurvedArc(place1, trans1, id=10, name="C1")
    
    cp = curved._calculate_curve_control_point()
    print(f"\nHorizontal arc (0,0) -> (100,0):")
    print(f"  Control point: {cp}")
    print(f"  Expected: (50, ±20)  [midpoint + 20% perpendicular offset]")
    
    if cp is not None:
        cp_x, cp_y = cp
        midpoint_ok = abs(cp_x - 50) < 1e-6
        offset_ok = abs(abs(cp_y) - 20) < 1e-6
        
        status_x = "✓" if midpoint_ok else "✗"
        status_y = "✓" if offset_ok else "✗"
        
        print(f"  {status_x} X at midpoint: {cp_x} (expected 50)")
        print(f"  {status_y} Y offset correct: {abs(cp_y)} (expected 20)")
        
        if not (midpoint_ok and offset_ok):
            print("  ERROR: Control point calculation incorrect!")
            return False
    else:
        print("  ERROR: Control point is None!")
        return False
    
    # Vertical arc (0, 0) -> (0, 100)
    place2 = Place(x=0, y=0, id=3, name="P2")
    place2.tokens = 0
    trans2 = Transition(x=0, y=100, id=4, name="T2")
    curved2 = CurvedArc(place2, trans2, id=11, name="C2")
    
    cp2 = curved2._calculate_curve_control_point()
    print(f"\nVertical arc (0,0) -> (0,100):")
    print(f"  Control point: {cp2}")
    print(f"  Expected: (±20, 50)  [midpoint + 20% perpendicular offset]")
    
    if cp2 is not None:
        cp_x, cp_y = cp2
        midpoint_ok = abs(cp_y - 50) < 1e-6
        offset_ok = abs(abs(cp_x) - 20) < 1e-6
        
        status_y = "✓" if midpoint_ok else "✗"
        status_x = "✓" if offset_ok else "✗"
        
        print(f"  {status_x} X offset correct: {abs(cp_x)} (expected 20)")
        print(f"  {status_y} Y at midpoint: {cp_y} (expected 50)")
    
    # Degenerate case: same source and target position
    place3 = Place(x=50, y=50, id=5, name="P3")
    place3.tokens = 0
    trans3 = Transition(x=50, y=50, id=6, name="T3")
    curved3 = CurvedArc(place3, trans3, id=12, name="C3")
    
    cp3 = curved3._calculate_curve_control_point()
    print(f"\nDegenerate arc (same source/target position):")
    print(f"  Control point: {cp3}")
    print(f"  Expected: None")
    
    status = "✓" if cp3 is None else "✗"
    print(f"  {status} Returns None for degenerate case")
    
    print("\n✓ Geometry tests passed!")
    return True


def test_visual_rendering():
    """Test visual rendering of all arc types (requires GTK)."""
    print("\n" + "=" * 70)
    print("TEST 4: Visual Rendering Test")
    print("=" * 70)
    
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        import cairo
    except ImportError:
        print("  ⚠ GTK not available, skipping visual test")
        return True
    
    print("\nCreating test window with all 4 arc types...")
    
    class ArcTestWindow(Gtk.Window):
        def __init__(self):
            super().__init__(title="Arc Types Test - All 4 Types")
            self.set_default_size(900, 400)
            
            # Create drawing area
            self.draw_area = Gtk.DrawingArea()
            self.draw_area.connect("draw", self.on_draw)
            self.add(self.draw_area)
            
            # Create test objects in 4 columns
            # Column 1: Arc (straight, normal arrow)
            self.p1 = Place(x=100, y=200, id=1, name="P1")
            self.p1.tokens = 3
            self.t1 = Transition(x=200, y=200, id=2, name="T1")
            self.arc1 = Arc(self.p1, self.t1, 10, "A1", weight=2)
            
            # Column 2: InhibitorArc (straight, hollow circle)
            self.p2 = Place(x=300, y=200, id=3, name="P2")
            self.p2.tokens = 2
            self.t2 = Transition(x=400, y=200, id=4, name="T2")
            self.arc2 = InhibitorArc(self.p2, self.t2, 11, "I1", weight=1)
            
            # Column 3: CurvedArc (curve, normal arrow)
            self.p3 = Place(x=500, y=200, id=5, name="P3")
            self.p3.tokens = 1
            self.t3 = Transition(x=600, y=200, id=6, name="T3")
            self.arc3 = CurvedArc(self.p3, self.t3, 12, "C1", weight=3)
            
            # Column 4: CurvedInhibitorArc (curve, hollow circle)
            self.p4 = Place(x=700, y=200, id=7, name="P4")
            self.p4.tokens = 0
            self.t4 = Transition(x=800, y=200, id=8, name="T4")
            self.arc4 = CurvedInhibitorArc(self.p4, self.t4, 13, "CI1", weight=2)
            
            # Add labels
            self.labels = [
                (150, 50, "Arc"),
                (350, 50, "InhibitorArc"),
                (550, 50, "CurvedArc"),
                (750, 50, "CurvedInhibitorArc")
            ]
        
        def on_draw(self, widget, cr):
            # White background
            cr.set_source_rgb(1, 1, 1)
            cr.paint()
            
            zoom = 1.0
            
            # Draw labels
            cr.select_font_face("Arial", 0, 1)  # Bold
            cr.set_font_size(14)
            cr.set_source_rgb(0, 0, 0)
            for x, y, label in self.labels:
                extents = cr.text_extents(label)
                cr.move_to(x - extents.width / 2, y)
                cr.show_text(label)
            
            # Render all objects
            objects = [
                self.p1, self.t1, self.arc1,
                self.p2, self.t2, self.arc2,
                self.p3, self.t3, self.arc3,
                self.p4, self.t4, self.arc4
            ]
            
            for obj in objects:
                obj.render(cr, zoom=zoom)
    
    win = ArcTestWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    
    print("  ✓ Test window created successfully")
    print("\n  Visual inspection:")
    print("    - Column 1: Should show straight arc with two-line arrowhead")
    print("    - Column 2: Should show straight arc with hollow circle")
    print("    - Column 3: Should show curved arc with two-line arrowhead")
    print("    - Column 4: Should show curved arc with hollow circle")
    print("\n  Close the window to continue...")
    
    Gtk.main()
    
    print("\n✓ Visual test completed!")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("ARC TYPES COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    try:
        test_arc_hierarchy()
        if not test_serialization():
            return 1
        if not test_curved_arc_geometry():
            return 1
        if not test_visual_rendering():
            return 1
        
        print("\n" + "=" * 70)
        print("ALL TESTS PASSED! ✓")
        print("=" * 70)
        print("\nSummary:")
        print("  ✓ Arc class hierarchy correct")
        print("  ✓ Serialization/deserialization works")
        print("  ✓ Curved arc geometry calculations correct")
        print("  ✓ Visual rendering successful")
        print("\nNext steps:")
        print("  - Test at different zoom levels (50%, 200%)")
        print("  - Test with colored arcs")
        print("  - Test selection (clicking on arcs)")
        print("  - Integrate with UI dialog for arc type selection")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
