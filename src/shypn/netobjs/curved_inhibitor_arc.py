#!/usr/bin/env python3
"""CurvedInhibitorArc - Inhibitor arc with bezier curve path.

Combines curved path from CurvedArc with hollow circle marker from InhibitorArc.
"""
import math
from shypn.netobjs.curved_arc import CurvedArc
from shypn.netobjs.inhibitor_arc import InhibitorArc


class CurvedInhibitorArc(CurvedArc):
    """Inhibitor arc rendered with a bezier curve path.
    
    Inherits:
    - Bezier curve rendering from CurvedArc
    - Uses InhibitorArc's marker rendering method
    
    This class combines the best of both:
    - Smooth curve to avoid overlap with opposite arcs
    - Hollow circle marker for inhibitor semantics
    """
    
    # Marker size (same as InhibitorArc)
    MARKER_RADIUS = 8.0
    
    def __init__(self, source, target, id: int, name: str, weight: int = 1):
        """Initialize a curved inhibitor arc.
        
        Args:
            source: Source PetriNetObject (typically a Place)
            target: Target PetriNetObject (typically a Transition)
            id: Unique integer identifier (immutable, system-assigned)
            name: Unique name in format "CI1", "CI2", etc. (immutable, system-assigned)
            weight: Arc weight (default: 1)
        """
        # Validate using InhibitorArc rules (Place → Transition only)
        InhibitorArc._validate_connection(source, target)
        # Skip CurvedArc.__init__ to avoid double validation, call Arc.__init__ directly
        from shypn.netobjs.arc import Arc
        Arc.__init__(self, source, target, id, name, weight)
    
    def _render_arrowhead(self, cr, x: float, y: float, dx: float, dy: float, zoom: float = 1.0):
        """Render hollow circle marker instead of two-line arrowhead.
        
        Delegates to InhibitorArc's implementation to avoid code duplication.
        
        Args:
            cr: Cairo context
            x, y: Marker center position (world coords)
            dx, dy: Direction vector (for future use with line trimming)
            zoom: Current zoom level for size compensation
        """
        # Use InhibitorArc's marker rendering
        # This is composition through method delegation
        InhibitorArc._render_arrowhead(self, cr, x, y, dx, dy, zoom)
    
    def render(self, cr, zoom=1.0):
        """Render curved inhibitor arc with line stopping before the hollow circle.
        
        Overrides CurvedArc.render() to adjust the endpoint so the curve doesn't
        go through the hollow circle marker.
        
        Args:
            cr: Cairo context (with zoom transformation already applied)
            zoom: Current zoom level for line width compensation
        """
        # Ensure clean Cairo context state
        cr.new_path()
        
        # Get source and target positions in world space
        src_world_x, src_world_y = self.source.x, self.source.y
        tgt_world_x, tgt_world_y = self.target.x, self.target.y
        
        # Check for parallel arcs and calculate offset for control point
        offset_distance = None  # None = use default 20% offset
        if hasattr(self, '_manager') and self._manager:
            parallels = self._manager.detect_parallel_arcs(self)
            if parallels:
                offset_distance = self._manager.calculate_arc_offset(self, parallels)
        
        # Calculate control point with optional offset
        control_point = self._calculate_curve_control_point(offset=offset_distance)
        
        if control_point is None:
            # Degenerate case: fall back to straight line
            super(CurvedArc, self).render(cr, zoom)  # Call Arc.render()
            return
        
        cp_x, cp_y = control_point
        
        # Calculate tangent at end: direction from control point to target
        dx_end = tgt_world_x - cp_x
        dy_end = tgt_world_y - cp_y
        length_end = math.sqrt(dx_end*dx_end + dy_end*dy_end)
        
        if length_end < 1e-6:
            super(CurvedArc, self).render(cr, zoom)
            return
        
        dx_end /= length_end
        dy_end /= length_end
        
        # Tangent at start: direction from source to control point
        dx_start = cp_x - src_world_x
        dy_start = cp_y - src_world_y
        length_start = math.sqrt(dx_start*dx_start + dy_start*dy_start)
        
        if length_start < 1e-6:
            super(CurvedArc, self).render(cr, zoom)
            return
        
        dx_start /= length_start
        dy_start /= length_start
        
        # Get boundary points in world space
        start_world_x, start_world_y = self._get_boundary_point(
            self.source, src_world_x, src_world_y, dx_start, dy_start)
        
        # Calculate tangent direction at end for marker orientation
        # Tangent at end: direction from control point to target
        dx_end = tgt_world_x - cp_x
        dy_end = tgt_world_y - cp_y
        length = math.sqrt(dx_end*dx_end + dy_end*dy_end)
        if length > 1e-6:
            dx_end /= length
            dy_end /= length
        
        # Get target boundary point for hollow circle placement
        boundary_x, boundary_y = self._get_boundary_point(
            self.target, tgt_world_x, tgt_world_y, -dx_end, -dy_end)
        
        # For inhibitor arc: hollow circle must be entirely outside target
        # The circle's outer edge touches the target boundary (edge-to-edge)
        # Position circle center INWARD (away from target) by marker radius
        marker_radius = self.MARKER_RADIUS / zoom
        marker_x = boundary_x - dx_end * marker_radius
        marker_y = boundary_y - dy_end * marker_radius
        
        # Curve draws to target center, will be cropped by target and circle
        end_world_x = tgt_world_x
        end_world_y = tgt_world_y
        
        # Add glow effect for colored arcs
        if self.color != self.DEFAULT_COLOR:
            cr.move_to(start_world_x, start_world_y)
            cr.curve_to(cp_x, cp_y, cp_x, cp_y, end_world_x, end_world_y)
            r, g, b = self.color
            cr.set_source_rgba(r, g, b, 0.3)
            cr.set_line_width((self.width + 2) / max(zoom, 1e-6))
            cr.stroke()
        
        # Draw curve in world coordinates
        cr.move_to(start_world_x, start_world_y)
        cr.curve_to(cp_x, cp_y, cp_x, cp_y, end_world_x, end_world_y)
        cr.set_source_rgb(*self.color)
        cr.set_line_width(self.width / max(zoom, 1e-6))
        cr.stroke()
        
        # Draw hollow circle at target boundary (not pulled back)
        self._render_arrowhead(cr, marker_x, marker_y, dx_end, dy_end, zoom)
        
        # Draw weight label if > 1
        if self.weight > 1:
            # Use curved arc specific weight rendering (calculates position on curve)
            # Pass offset information to ensure text goes on outer side
            offset_distance = None
            if hasattr(self, '_manager') and self._manager:
                parallels = self._manager.detect_parallel_arcs(self)
                if parallels:
                    offset_distance = self._manager.calculate_arc_offset(self, parallels)
            
            self._render_weight_curved(cr, start_world_x, start_world_y, 
                                      end_world_x, end_world_y, 
                                      cp_x, cp_y, offset_distance, zoom)
        
        # Ensure clean state for next rendering operation
        cr.new_path()
    
    def _render_weight_curved(self, cr, x1: float, y1: float, x2: float, y2: float,
                             cp_x: float, cp_y: float, curve_offset: float, 
                             zoom: float = 1.0):
        """Render weight label on curved inhibitor arc.
        
        Calculates the actual midpoint along the bezier curve and positions
        the text perpendicular to the curve at that point, on the outer side.
        
        Args:
            cr: Cairo context
            x1, y1: Start point (world coords)
            x2, y2: End point (world coords)
            cp_x, cp_y: Control point (world coords)
            curve_offset: Offset distance used for curve (determines which side)
            zoom: Current zoom level
        """
        # Save context to avoid interfering with other rendering
        cr.save()
        
        # Calculate midpoint on bezier curve at t=0.5
        # Quadratic bezier: B(t) = (1-t)²*P0 + 2(1-t)t*P1 + t²*P2
        t = 0.5
        b0 = (1 - t) * (1 - t)
        b1 = 2 * (1 - t) * t
        b2 = t * t
        
        mid_x = b0 * x1 + b1 * cp_x + b2 * x2
        mid_y = b0 * y1 + b1 * cp_y + b2 * y2
        
        # Calculate tangent at midpoint for perpendicular offset
        # Derivative: B'(t) = 2(1-t)(P1-P0) + 2t(P2-P1)
        tangent_x = 2 * (1 - t) * (cp_x - x1) + 2 * t * (x2 - cp_x)
        tangent_y = 2 * (1 - t) * (cp_y - y1) + 2 * t * (y2 - cp_y)
        
        # Normalize tangent
        tangent_length = math.sqrt(tangent_x * tangent_x + tangent_y * tangent_y)
        if tangent_length < 1e-6:
            # Degenerate case: fallback to straight line
            super()._render_weight(cr, x1, y1, x2, y2, zoom)
            return
        
        tangent_x /= tangent_length
        tangent_y /= tangent_length
        
        # Perpendicular direction (rotate tangent 90° counterclockwise)
        perp_x = -tangent_y
        perp_y = tangent_x
        
        # Determine which side to place text based on curve direction
        # For parallel arcs, we want text on the OUTER side (same side as curve bends)
        if curve_offset is not None:
            # Calculate the perpendicular direction from the straight line
            dx = x2 - x1
            dy = y2 - y1
            line_length = math.sqrt(dx*dx + dy*dy)
            
            if line_length > 1e-6:
                # Perpendicular to straight line (normalized)
                line_perp_x = -dy / line_length
                line_perp_y = dx / line_length
                
                # Check if control point is on positive or negative side
                mid_line_x = (x1 + x2) / 2
                mid_line_y = (y1 + y2) / 2
                cp_offset_x = cp_x - mid_line_x
                cp_offset_y = cp_y - mid_line_y
                
                # Dot product tells us which side the control point is on
                side = cp_offset_x * line_perp_x + cp_offset_y * line_perp_y
                
                # If curve is on negative side, flip the perpendicular direction
                # This ensures text stays on the same side as the curve bulge
                if side < 0:
                    perp_x = -perp_x
                    perp_y = -perp_y
        
        # Font setup (legacy style: Bold Arial 12pt)
        cr.select_font_face("Arial", 0, 1)  # Normal slant, Bold weight
        cr.set_font_size(12 / zoom)
        text = str(self.weight)
        extents = cr.text_extents(text)
        
        # Position text perpendicular to curve (on outer side)
        offset = 11 / zoom  # Legacy offset distance
        text_x = mid_x + perp_x * offset - extents.width / 2
        text_y = mid_y + perp_y * offset + extents.height / 2
        
        # Draw white background (legacy style: semi-transparent)
        padding = 2 / zoom
        cr.rectangle(text_x - padding, text_y - extents.height - padding,
                    extents.width + 2 * padding, extents.height + 2 * padding)
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.8)  # White, 0.8 alpha
        cr.fill()
        
        # Draw text
        cr.move_to(text_x, text_y)
        cr.set_source_rgb(0, 0, 0)  # Black text
        cr.show_text(text)
        
        # Clear the current path to avoid artifacts
        cr.new_path()
        
        # Restore context (clear any paths/state)
        cr.restore()
    
    def to_dict(self) -> dict:
        """Serialize curved inhibitor arc to dictionary for persistence.
        
        Returns:
            dict: Dictionary containing all arc properties with type 'curved_inhibitor_arc'
        """
        data = super().to_dict()
        data["object_type"] = "curved_inhibitor_arc"  # Override object_type
        return data
    
    def __repr__(self):
        """String representation of the curved inhibitor arc."""
        return (f"CurvedInhibitorArc(id={self.id}, source={self.source.id}, "
                f"target={self.target.id}, weight={self.weight})")
