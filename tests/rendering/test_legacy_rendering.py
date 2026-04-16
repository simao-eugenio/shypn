#!/usr/bin/env python3
"""
Test to verify legacy rendering migration is complete.

This test creates a simple Petri net with all object types and renders them
to verify the visual appearance matches the legacy renderer.

Expected Results:
1. Places: Hollow circles (stroke only, 3.0px border)
2. Transitions: Black fill with colored border (3.0px)
3. Arcs: Two-line arrowheads (15px, π/5 angle), 3.0px line
4. Weight: Bold Arial 12pt with white background (if weight > 1)
5. Tokens: Arial 14pt text in place center
6. Inhibitor: White-filled circle with colored ring
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import cairo

from shypn.api.place import Place
from shypn.api.transition import Transition
from shypn.api.arc import Arc
from shypn.api.inhibitor_arc import InhibitorArc


class RenderingTestWindow(Gtk.Window):
    """Window to display rendering test results."""
    
    def __init__(self):
        super().__init__(title="Legacy Rendering Test")
        self.set_default_size(800, 600)
        self.connect("destroy", Gtk.main_quit)
        
        # Create drawing area
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.connect("draw", self.on_draw)
        self.add(self.drawing_area)
        
        # Create test Petri net objects
        self.create_test_objects()
        
        # Instructions label
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        label = Gtk.Label(label=(
            "Visual Test: Verify rendering matches legacy style\n"
            "✓ Places are HOLLOW circles (not filled), 3.0px border\n"
            "✓ Transitions have 3.0px border\n"
            "✓ Arcs have TWO-LINE arrowheads (not filled triangles)\n"
            "✓ Weight shows as bold text with white background\n"
            "✓ Tokens show as numbers (Arial 14pt)\n"
            "✓ Inhibitor has white-filled circle with colored ring"
        ))
        label.set_margin_top(10)
        label.set_margin_bottom(10)
        vbox.pack_start(label, False, False, 0)
        vbox.pack_start(self.drawing_area, True, True, 0)
        self.add(vbox)
    
    def create_test_objects(self):
        """Create a simple Petri net for testing."""
        # Places
        self.p1 = Place(id=1, name="P1", x=150, y=150, initial_tokens=2)
        self.p2 = Place(id=2, name="P2", x=650, y=150, initial_tokens=0)
        self.p3 = Place(id=3, name="P3", x=150, y=450, initial_tokens=3)
        
        # Transitions
        self.t1 = Transition(id=4, name="T1", x=400, y=150, horizontal=True)
        self.t2 = Transition(id=5, name="T2", x=400, y=450, horizontal=False)
        
        # Regular arcs (with different weights to test weight rendering)
        self.a1 = Arc(source=self.p1, target=self.t1, id=6, name="A1", weight=1)
        self.a2 = Arc(source=self.t1, target=self.p2, id=7, name="A2", weight=2)
        self.a3 = Arc(source=self.p3, target=self.t2, id=8, name="A3", weight=3)
        
        # Inhibitor arc
        self.i1 = InhibitorArc(source=self.p1, target=self.t2, id=9, name="I1")
        
        # Collect all objects
        self.objects = [
            self.p1, self.p2, self.p3,
            self.t1, self.t2,
            self.a1, self.a2, self.a3,
            self.i1
        ]
    
    def on_draw(self, widget, cr):
        """Draw all test objects."""
        # White background
        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.paint()
        
        # Render all objects (arcs first, then nodes on top)
        arcs = [obj for obj in self.objects if isinstance(obj, Arc)]
        nodes = [obj for obj in self.objects if not isinstance(obj, Arc)]
        
        for arc in arcs:
            arc.render(cr)
        
        for node in nodes:
            node.render(cr)
        
        # Draw legend
        self._draw_legend(cr)
        
        return False
    
    def _draw_legend(self, cr):
        """Draw legend explaining what to look for."""
        legend_x = 20
        legend_y = 20
        
        cr.set_source_rgb(0, 0, 0)
        cr.select_font_face("Sans", 0, 1)  # Bold
        cr.set_font_size(12)
        
        legend_items = [
            "P1: 2 tokens (text display)",
            "P2: Empty place (hollow circle)",
            "P3: 3 tokens (text display)",
            "A1: Weight=1 (no label)",
            "A2: Weight=2 (shows label)",
            "A3: Weight=3 (shows label)",
            "I1: Inhibitor arc (white marker)"
        ]
        
        for i, item in enumerate(legend_items):
            cr.move_to(legend_x, legend_y + i * 20)
            cr.show_text(item)


def main():
    """Run the rendering test."""
    print("Legacy Rendering Migration Test")
    print("=" * 50)
    print()
    print("This test displays a simple Petri net to verify")
    print("the rendering matches the legacy style.")
    print()
    print("Check for:")
    print("  ✓ Hollow places (stroke only, not filled)")
    print("  ✓ 3.0px line widths everywhere")
    print("  ✓ Two-line arrowheads (not filled triangles)")
    print("  ✓ Weight labels with white background")
    print("  ✓ Token counts as text (Arial 14pt)")
    print("  ✓ Inhibitor marker (white fill + colored ring)")
    print()
    
    win = RenderingTestWindow()
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
