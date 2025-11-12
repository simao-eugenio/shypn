"""Simple topology viewer for subnet visualization.

Wayland-safe widget using GTK3 DrawingArea with Cairo.
Displays simplified subnet topology without full Petri net rendering.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import cairo

from typing import Optional, List, Tuple
from shypn.ui.panels.viability.investigation import Subnet, Dependency


class TopologyViewer(Gtk.DrawingArea):
    """Simple topology viewer for subnet visualization.
    
    Displays:
    - Transitions as rectangles
    - Places as circles
    - Arcs as lines
    - Boundary places highlighted
    - Dependencies as bold connections
    
    Wayland-safe: Uses only GTK3 DrawingArea + Cairo (no X11).
    """
    
    def __init__(self, subnet: Optional[Subnet] = None):
        """Initialize topology viewer.
        
        Args:
            subnet: The subnet to visualize
        """
        super().__init__()
        
        self.subnet = subnet
        self.width = 400
        self.height = 300
        
        # Colors
        self.COLOR_TRANSITION = (0.4, 0.6, 0.9)      # Blue
        self.COLOR_PLACE_INTERNAL = (0.9, 0.9, 0.9)  # Light gray
        self.COLOR_PLACE_INPUT = (0.6, 0.9, 0.6)     # Green
        self.COLOR_PLACE_OUTPUT = (0.9, 0.6, 0.6)    # Red
        self.COLOR_ARC = (0.5, 0.5, 0.5)             # Gray
        self.COLOR_DEPENDENCY = (0.9, 0.6, 0.3)      # Orange
        self.COLOR_TEXT = (0.0, 0.0, 0.0)            # Black
        self.COLOR_BACKGROUND = (1.0, 1.0, 1.0)      # White
        
        # Layout cache
        self.layout = {}
        
        # Connect drawing signal
        self.connect('draw', self._on_draw)
        
        # Set size
        self.set_size_request(self.width, self.height)
    
    def _on_draw(self, widget, cr: cairo.Context):
        """Handle draw event.
        
        Args:
            widget: The widget being drawn
            cr: Cairo context
        """
        if not self.subnet:
            self._draw_empty_state(cr)
            return False
        
        # Get actual size
        allocation = self.get_allocation()
        self.width = allocation.width
        self.height = allocation.height
        
        # Clear background
        cr.set_source_rgb(*self.COLOR_BACKGROUND)
        cr.paint()
        
        # Compute layout if needed
        if not self.layout:
            self._compute_layout()
        
        # Draw elements
        self._draw_arcs(cr)
        self._draw_dependencies(cr)
        self._draw_places(cr)
        self._draw_transitions(cr)
        
        return False
    
    def _draw_empty_state(self, cr: cairo.Context):
        """Draw empty state message."""
        allocation = self.get_allocation()
        width = allocation.width
        height = allocation.height
        
        # Background
        cr.set_source_rgb(*self.COLOR_BACKGROUND)
        cr.paint()
        
        # Text
        cr.set_source_rgb(*self.COLOR_TEXT)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(14)
        
        text = "No subnet to display"
        extents = cr.text_extents(text)
        x = (width - extents.width) / 2
        y = (height + extents.height) / 2
        
        cr.move_to(x, y)
        cr.show_text(text)
    
    def _compute_layout(self):
        """Compute positions for all elements using simple grid layout."""
        if not self.subnet:
            return
        
        # Get transitions
        transitions = self.subnet.localities
        n_transitions = len(transitions)
        
        if n_transitions == 0:
            return
        
        # Simple horizontal layout
        margin = 40
        spacing_x = (self.width - 2 * margin) / (n_transitions + 1)
        
        # Place transitions in a row
        for i, locality in enumerate(transitions):
            t_id = locality.transition.id
            x = margin + (i + 1) * spacing_x
            y = self.height / 2
            self.layout[t_id] = ('transition', x, y)
        
        # Place input places above, output places below
        input_places = {}
        output_places = {}
        
        for locality in transitions:
            t_id = locality.transition.id
            t_x, t_y = self.layout[t_id][1], self.layout[t_id][2]
            
            # Inputs above
            for i, place in enumerate(locality.input_places):
                p_id = place.id
                if p_id not in self.layout:
                    # Offset inputs horizontally around transition
                    offset = (i - len(locality.input_places) / 2) * 30
                    self.layout[p_id] = ('place', t_x + offset, t_y - 60)
                    input_places[p_id] = place
            
            # Outputs below
            for i, place in enumerate(locality.output_places):
                p_id = place.id
                if p_id not in self.layout:
                    # Offset outputs horizontally around transition
                    offset = (i - len(locality.output_places) / 2) * 30
                    self.layout[p_id] = ('place', t_x + offset, t_y + 60)
                    output_places[p_id] = place
    
    def _draw_transitions(self, cr: cairo.Context):
        """Draw transitions as rectangles."""
        cr.set_source_rgb(*self.COLOR_TRANSITION)
        
        for element_id, (element_type, x, y) in self.layout.items():
            if element_type != 'transition':
                continue
            
            # Draw rectangle
            width, height = 40, 25
            cr.rectangle(x - width/2, y - height/2, width, height)
            cr.fill_preserve()
            cr.set_source_rgb(0, 0, 0)
            cr.set_line_width(1.5)
            cr.stroke()
            
            # Draw label (abbreviated)
            cr.set_source_rgb(*self.COLOR_TEXT)
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(10)
            
            # Abbreviate if too long
            label = element_id
            if len(label) > 6:
                label = label[:5] + "..."
            
            extents = cr.text_extents(label)
            text_x = x - extents.width / 2
            text_y = y + extents.height / 2
            
            cr.move_to(text_x, text_y)
            cr.show_text(label)
    
    def _draw_places(self, cr: cairo.Context):
        """Draw places as circles with boundary highlighting."""
        for element_id, (element_type, x, y) in self.layout.items():
            if element_type != 'place':
                continue
            
            # Determine color based on boundary type
            if element_id in self.subnet.boundary_places:
                place_type = self.subnet.place_types.get(element_id, 'internal')
                if place_type == 'input':
                    color = self.COLOR_PLACE_INPUT
                elif place_type == 'output':
                    color = self.COLOR_PLACE_OUTPUT
                else:
                    color = self.COLOR_PLACE_INTERNAL
            else:
                color = self.COLOR_PLACE_INTERNAL
            
            # Draw circle
            radius = 15
            cr.arc(x, y, radius, 0, 2 * 3.14159)
            cr.set_source_rgb(*color)
            cr.fill_preserve()
            cr.set_source_rgb(0, 0, 0)
            cr.set_line_width(1.5)
            cr.stroke()
            
            # Draw label (abbreviated, below circle)
            cr.set_source_rgb(*self.COLOR_TEXT)
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(8)
            
            label = element_id
            if len(label) > 6:
                label = label[:5] + "..."
            
            extents = cr.text_extents(label)
            text_x = x - extents.width / 2
            text_y = y + radius + extents.height + 2
            
            cr.move_to(text_x, text_y)
            cr.show_text(label)
    
    def _draw_arcs(self, cr: cairo.Context):
        """Draw arcs as lines."""
        cr.set_source_rgb(*self.COLOR_ARC)
        cr.set_line_width(1.0)
        
        # Draw arcs from localities
        for locality in self.subnet.localities:
            t_id = locality.transition.id
            if t_id not in self.layout:
                continue
            
            t_type, t_x, t_y = self.layout[t_id]
            
            # Input arcs: place -> transition
            for arc in locality.input_arcs:
                p_id = arc.place.id if hasattr(arc, 'place') else arc.source_id
                if p_id in self.layout:
                    p_type, p_x, p_y = self.layout[p_id]
                    cr.move_to(p_x, p_y)
                    cr.line_to(t_x, t_y)
                    cr.stroke()
            
            # Output arcs: transition -> place
            for arc in locality.output_arcs:
                p_id = arc.place.id if hasattr(arc, 'place') else arc.target_id
                if p_id in self.layout:
                    p_type, p_x, p_y = self.layout[p_id]
                    cr.move_to(t_x, t_y)
                    cr.line_to(p_x, p_y)
                    cr.stroke()
    
    def _draw_dependencies(self, cr: cairo.Context):
        """Draw dependencies as bold connections."""
        if not self.subnet.dependencies:
            return
        
        cr.set_source_rgb(*self.COLOR_DEPENDENCY)
        cr.set_line_width(2.5)
        cr.set_dash([5, 3])  # Dashed line
        
        for dep in self.subnet.dependencies:
            source_id = dep.source_transition_id
            target_id = dep.target_transition_id
            
            if source_id in self.layout and target_id in self.layout:
                s_type, s_x, s_y = self.layout[source_id]
                t_type, t_x, t_y = self.layout[target_id]
                
                # Draw curved line between transitions
                cr.move_to(s_x, s_y)
                
                # Control points for curve
                ctrl_y = (s_y + t_y) / 2 + 20
                cr.curve_to(
                    s_x, ctrl_y,      # Control point 1
                    t_x, ctrl_y,      # Control point 2
                    t_x, t_y          # End point
                )
                cr.stroke()
        
        # Reset dash
        cr.set_dash([])
    
    def update_subnet(self, subnet: Subnet):
        """Update the displayed subnet.
        
        Args:
            subnet: New subnet to display
        """
        self.subnet = subnet
        self.layout = {}  # Clear layout cache
        self.queue_draw()
    
    def clear(self):
        """Clear the viewer."""
        self.subnet = None
        self.layout = {}
        self.queue_draw()


class TopologyViewerWithLegend(Gtk.Box):
    """Topology viewer with legend.
    
    Layout:
    ┌─────────────────────────────────────────────────────────┐
    │ ┌─────────────────────────────────────────────────────┐ │
    │ │                                                      │ │
    │ │            (Topology visualization)                 │ │
    │ │                                                      │ │
    │ └─────────────────────────────────────────────────────┘ │
    │ Legend: ⬜ Transition  ⚪ Internal  🟢 Input  🔴 Output │
    └─────────────────────────────────────────────────────────┘
    """
    
    def __init__(self, subnet: Optional[Subnet] = None):
        """Initialize viewer with legend.
        
        Args:
            subnet: The subnet to visualize
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        # Topology viewer
        self.viewer = TopologyViewer(subnet)
        self.pack_start(self.viewer, True, True, 0)
        
        # Legend
        legend = self._create_legend()
        self.pack_start(legend, False, False, 0)
    
    def _create_legend(self) -> Gtk.Box:
        """Create legend box."""
        legend = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        legend.set_halign(Gtk.Align.CENTER)
        legend.set_margin_start(8)
        legend.set_margin_end(8)
        legend.set_margin_bottom(8)
        
        # Title
        title = Gtk.Label(label="Legend:")
        title.get_style_context().add_class('dim-label')
        legend.pack_start(title, False, False, 0)
        
        # Items
        items = [
            ("⬜", "Transition"),
            ("⚪", "Internal"),
            ("🟢", "Input"),
            ("🔴", "Output"),
            ("━━", "Arc"),
            ("┄┄", "Dependency")
        ]
        
        for symbol, label in items:
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            
            symbol_label = Gtk.Label(label=symbol)
            box.pack_start(symbol_label, False, False, 0)
            
            text_label = Gtk.Label(label=label)
            text_label.get_style_context().add_class('dim-label')
            box.pack_start(text_label, False, False, 0)
            
            legend.pack_start(box, False, False, 0)
        
        return legend
    
    def update_subnet(self, subnet: Subnet):
        """Update the displayed subnet."""
        self.viewer.update_subnet(subnet)
    
    def clear(self):
        """Clear the viewer."""
        self.viewer.clear()
