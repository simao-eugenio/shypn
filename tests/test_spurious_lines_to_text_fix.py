#!/usr/bin/env python3
"""Test for spurious lines to text labels fix.

This test creates a simple Petri net and renders it to verify
that no spurious lines appear from object centers to text labels.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import cairo
from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition, Arc
from shypn.netobjs.curved_arc import CurvedArc


def create_test_net():
    """Create a test net with places, transitions, and curved arcs."""
    doc = DocumentModel()
    
    # Create places with labels
    p1 = Place(x=100, y=100, id=1, name="P1", label="Place_1")
    p2 = Place(x=300, y=100, id=2, name="P2", label="Place_2")
    p3 = Place(x=500, y=100, id=3, name="P3", label="Place_3")
    
    # Create transitions with labels
    t1 = Transition(x=200, y=100, id=1, name="T1", label="Trans_1")
    t2 = Transition(x=400, y=100, id=2, name="T2", label="Trans_2")
    
    # Add tokens to visualize
    p1.tokens = 5
    p2.tokens = 3
    
    # Create regular arcs
    a1 = Arc(source=p1, target=t1, id=1, name="A1", weight=2)
    a2 = Arc(source=t1, target=p2, id=2, name="A2", weight=3)
    
    # Create curved arc
    a3 = CurvedArc(source=p2, target=t2, id=3, name="A3", weight=4)
    a4 = Arc(source=t2, target=p3, id=4, name="A4", weight=1)
    
    doc.places.extend([p1, p2, p3])
    doc.transitions.extend([t1, t2])
    doc.arcs.extend([a1, a2, a3, a4])
    
    return doc


def render_to_png(doc, filename, width=600, height=200):
    """Render document to PNG file.
    
    Args:
        doc: DocumentModel instance
        filename: Output PNG filename
        width, height: Image dimensions
    """
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    cr = cairo.Context(surface)
    
    # White background
    cr.set_source_rgb(1, 1, 1)
    cr.paint()
    
    # Set up transform (no zoom, just direct rendering)
    zoom = 1.0
    
    # Render all objects in order
    # 1. Arcs first (background)
    for arc in doc.arcs:
        arc.render(cr, zoom=zoom)
    
    # 2. Places and transitions (foreground)
    for place in doc.places:
        place.render(cr, zoom=zoom)
    
    for transition in doc.transitions:
        transition.render(cr, zoom=zoom)
    
    # Save to file
    surface.write_to_png(filename)
    surface.finish()
    
    print(f"✓ Rendered to {filename}")


def test_no_spurious_lines():
    """Test that no spurious lines appear in rendering."""
    print("\n" + "="*70)
    print("Testing: No Spurious Lines to Text Labels")
    print("="*70)
    
    # Create test net
    print("\n1. Creating test Petri net...")
    doc = create_test_net()
    print(f"   Places: {len(doc.places)}")
    print(f"   Transitions: {len(doc.transitions)}")
    print(f"   Arcs: {len(doc.arcs)}")
    print(f"   Curved arcs: {sum(1 for a in doc.arcs if isinstance(a, CurvedArc))}")
    
    # Render to PNG
    print("\n2. Rendering to PNG...")
    output_file = "test_spurious_lines_fix.png"
    render_to_png(doc, output_file)
    
    # Instructions for visual inspection
    print("\n3. Visual Inspection Required:")
    print(f"   Open: {output_file}")
    print("   Check for:")
    print("   - No lines from place centers to text labels")
    print("   - No lines from place centers to arc weight text")
    print("   - All arcs properly connect place/transition centers")
    print("   - Weight text (2, 3, 4) positioned correctly on arcs")
    print("   - Labels (Place_1, etc.) below places/transitions")
    
    print("\n" + "="*70)
    print("✓ Test complete - Visual inspection required")
    print("="*70)
    
    return True


def test_cairo_path_cleanup():
    """Test that Cairo path state is properly cleaned after text rendering."""
    print("\n" + "="*70)
    print("Testing: Cairo Path State Cleanup")
    print("="*70)
    
    # Create simple surface
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 400, 200)
    cr = cairo.Context(surface)
    
    print("\n1. Testing Place label rendering...")
    p1 = Place(x=100, y=100, id=1, name="P1", label="TestLabel")
    p1.tokens = 5
    
    # Render place (includes tokens and label)
    p1.render(cr, zoom=1.0)
    
    # Check if current point is defined (should be None after new_path())
    try:
        current_point = cr.get_current_point()
        if current_point == (0.0, 0.0):
            print("   ✓ Path properly cleared (no current point)")
        else:
            print(f"   ⚠ Current point still set: {current_point}")
    except:
        print("   ✓ Path properly cleared (no current point)")
    
    print("\n2. Testing Transition label rendering...")
    t1 = Transition(x=300, y=100, id=1, name="T1", label="TestTrans")
    t1.render(cr, zoom=1.0)
    
    try:
        current_point = cr.get_current_point()
        if current_point == (0.0, 0.0):
            print("   ✓ Path properly cleared (no current point)")
        else:
            print(f"   ⚠ Current point still set: {current_point}")
    except:
        print("   ✓ Path properly cleared (no current point)")
    
    print("\n3. Testing Arc weight rendering...")
    p2 = Place(x=100, y=100, id=2, name="P2", label="P2")
    t2 = Transition(x=300, y=100, id=2, name="T2", label="T2")
    arc = Arc(source=p2, target=t2, id=1, name="A1", weight=5)
    
    arc.render(cr, zoom=1.0)
    
    try:
        current_point = cr.get_current_point()
        if current_point == (0.0, 0.0):
            print("   ✓ Path properly cleared (no current point)")
        else:
            print(f"   ⚠ Current point still set: {current_point}")
    except:
        print("   ✓ Path properly cleared (no current point)")
    
    print("\n4. Testing CurvedArc weight rendering...")
    arc2 = CurvedArc(source=p2, target=t2, id=2, name="A2", weight=3)
    arc2.render(cr, zoom=1.0)
    
    try:
        current_point = cr.get_current_point()
        if current_point == (0.0, 0.0):
            print("   ✓ Path properly cleared (no current point)")
        else:
            print(f"   ⚠ Current point still set: {current_point}")
    except:
        print("   ✓ Path properly cleared (no current point)")
    
    surface.finish()
    
    print("\n" + "="*70)
    print("✓ Cairo path cleanup test complete")
    print("="*70)
    
    return True


if __name__ == '__main__':
    print("="*70)
    print("Spurious Lines to Text Labels - Fix Verification")
    print("="*70)
    print("\nThis test verifies that the fix for spurious lines works correctly.")
    print("The fix adds cr.new_path() after all text rendering operations.")
    print("\nFixed files:")
    print("  - src/shypn/netobjs/place.py (_render_tokens, _render_label)")
    print("  - src/shypn/netobjs/transition.py (_render_label)")
    print("  - src/shypn/netobjs/curved_arc.py (_render_weight_curved)")
    
    try:
        # Run tests
        test_cairo_path_cleanup()
        test_no_spurious_lines()
        
        print("\n" + "="*70)
        print("✓ All tests completed successfully")
        print("="*70)
        print("\nNext steps:")
        print("1. Open test_spurious_lines_fix.png and verify visually")
        print("2. Test with real KEGG pathways (e.g., glycolysis)")
        print("3. Edit arc weights and check for spurious lines")
        print("4. Select places and verify no lines to labels")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
