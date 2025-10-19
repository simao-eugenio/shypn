#!/usr/bin/env python3
"""CurvedArc - Arc with bezier curve path.

Inherits from Arc but renders with a smooth curve instead of straight line.
Useful for parallel opposite arcs to avoid visual overlap.
"""
import math
from typing import Optional, Tuple
from shypn.netobjs.arc import Arc


class CurvedArc(Arc):
    """Arc rendered with a bezier curve path.
    
    Uses quadratic bezier curve with automatic control point calculation:
    - Control point at midpoint perpendicular to straight line
    - Offset is 20% of line length (configurable)
    - Keeps two-line arrowhead from Arc base class
    
    Inherits all properties from Arc but overrides path rendering.
    """
    
    # Curve offset as percentage of line length
    CURVE_OFFSET_RATIO = 0.20  # 20% of line length
    
    def __init__(self, source, target, id: int, name: str, weight: int = 1):
        """Initialize a curved arc.
        
        Args:
            source: Source PetriNetObject (Place or Transition)
            target: Target PetriNetObject (Transition or Place)
            id: Unique integer identifier (immutable, system-assigned)
            name: Unique name in format "C1", "C2", etc. (immutable, system-assigned)
            weight: Arc weight (default: 1)
        """
        super().__init__(source, target, id, name, weight)
    
    def _calculate_curve_control_point(self, offset=None) -> Optional[Tuple[float, float]]:
        """Calculate bezier control point for curved arc.
        
        Creates a curve that bows perpendicular to the straight line
        connecting source and target. For opposite arcs (A→B, B→A),
        uses a canonical direction to ensure mirror symmetry.
        
        Args:
            offset: Optional override for offset distance. If None, uses 20% of line length.
        
        Returns:
            tuple: (x, y) control point coordinates, or None if degenerate
        """
        # Get source and target positions
        sx, sy = self.source.x, self.source.y
        tx, ty = self.target.x, self.target.y
        
        # Calculate midpoint
        mx = (sx + tx) / 2
        my = (sy + ty) / 2
        
        # For mirror symmetry with opposite arcs, use canonical direction
        # Always use left→right (or bottom→top if horizontal is same)
        # This ensures both arcs use the same baseline for perpendicular
        if sx < tx:
            # Source is left of target: use source→target
            dx = tx - sx
            dy = ty - sy
        elif sx > tx:
            # Target is left of source: use target→source
            dx = sx - tx
            dy = sy - ty
        else:
            # Same x coordinate: use bottom→top
            if sy < ty:
                dx = tx - sx
                dy = ty - sy
            else:
                dx = sx - tx
                dy = sy - ty
        
        length = math.sqrt(dx*dx + dy*dy)
        
        if length < 1e-6:
            return None  # Degenerate case: same point
        
        # Unit perpendicular vector (rotated 90° counterclockwise)
        perp_x = -dy / length
        perp_y = dx / length
        
        # Control point offset: use provided offset or default to 20% of line length
        if offset is None:
            offset = length * self.CURVE_OFFSET_RATIO
        
        # Control point at midpoint + perpendicular offset
        cp_x = mx + perp_x * offset
        cp_y = my + perp_y * offset
        
        return (cp_x, cp_y)
    
    def _find_curve_boundary_intersection(self, start_x, start_y, cp_x, cp_y, 
                                          tgt_cx, tgt_cy, target_obj):
        """Find where the bezier curve intersects the target's boundary.
        
        Uses binary search along the curve parameter t ∈ [0,1] to find
        the first point where the curve touches the target perimeter.
        
        Args:
            start_x, start_y: Curve starting point (source boundary)
            cp_x, cp_y: Control point
            tgt_cx, tgt_cy: Target center
            target_obj: Target object (Place or Transition) to check boundary
            
        Returns:
            (x, y): Point where curve intersects target boundary
        """
        from shypn.netobjs.place import Place
        from shypn.netobjs.transition import Transition
        
        # Get target boundary radius/dimensions
        if isinstance(target_obj, Place):
            boundary_threshold = target_obj.radius
            def distance_from_center(x, y):
                return math.sqrt((x - tgt_cx)**2 + (y - tgt_cy)**2)
        elif isinstance(target_obj, Transition):
            w = target_obj.width if target_obj.horizontal else target_obj.height
            h = target_obj.height if target_obj.horizontal else target_obj.width
            half_w, half_h = w / 2, h / 2
            boundary_threshold = min(half_w, half_h)  # Conservative estimate
            def distance_from_center(x, y):
                # Distance from rectangle center to point
                dx = abs(x - tgt_cx)
                dy = abs(y - tgt_cy)
                # If inside, return penetration; if outside, return distance
                return max(dx - half_w, dy - half_h, 0)
        else:
            # Fallback: use target center
            return (tgt_cx, tgt_cy)
        
        # Quadratic Bezier: B(t) = (1-t)²·P0 + 2(1-t)t·P1 + t²·P2
        def bezier_point(t):
            """Evaluate bezier curve at parameter t ∈ [0,1]"""
            s = 1 - t
            x = s*s*start_x + 2*s*t*cp_x + t*t*tgt_cx
            y = s*s*start_y + 2*s*t*cp_y + t*t*tgt_cy
            return (x, y)
        
        # Binary search for intersection point
        t_min, t_max = 0.0, 1.0
        tolerance = 0.001  # 0.1% precision along curve
        
        for _ in range(20):  # Max 20 iterations for binary search
            t_mid = (t_min + t_max) / 2
            x, y = bezier_point(t_mid)
            dist = distance_from_center(x, y)
            
            if abs(dist - boundary_threshold) < 1.0:  # Within 1px of boundary
                return (x, y)
            
            if dist < boundary_threshold:
                # Point is inside target, move backward along curve
                t_max = t_mid
            else:
                # Point is outside target, move forward along curve
                t_min = t_mid
            
            if t_max - t_min < tolerance:
                break
        
        # Return best approximation
        x, y = bezier_point(t_mid)
        return (x, y)
    
    def render(self, cr, transform=None, zoom=1.0):
        """Render curved arc using bezier path.
        
        Overrides Arc.render() to draw a quadratic bezier curve
        instead of a straight line. Automatically detects parallel arcs
        and adjusts curve offset.
        
        Args:
            cr: Cairo context (with zoom transformation already applied)
            transform: Optional function (deprecated, for backward compatibility)
            zoom: Current zoom level for line width compensation
        """
        # Ensure clean Cairo context state
        cr.new_path()
        
        # Get source and target positions in world space
        src_world_x, src_world_y = self.source.x, self.source.y
        tgt_world_x, tgt_world_y = self.target.x, self.target.y
        
        # Check if manual control point is set (from transformation)
        if hasattr(self, 'manual_control_point') and self.manual_control_point is not None:
            # Use manual control point directly
            control_point = self.manual_control_point
        else:
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
            super().render(cr, transform, zoom)
            return
        
        cp_x, cp_y = control_point
        
        # Calculate direction for boundary points
        # For curves, use tangent at endpoints
        
        # Tangent at start: direction from source to control point
        dx_start = cp_x - src_world_x
        dy_start = cp_y - src_world_y
        length_start = math.sqrt(dx_start*dx_start + dy_start*dy_start)
        
        if length_start < 1e-6:
            super().render(cr, transform, zoom)
            return
        
        dx_start /= length_start
        dy_start /= length_start
        
        # Tangent at end: direction from control point to target
        dx_end = tgt_world_x - cp_x
        dy_end = tgt_world_y - cp_y
        length_end = math.sqrt(dx_end*dx_end + dy_end*dy_end)
        
        if length_end < 1e-6:
            super().render(cr, transform, zoom)
            return
        
        dx_end /= length_end
        dy_end /= length_end
        
        # Get boundary points in world space
        start_world_x, start_world_y = self._get_boundary_point(
            self.source, src_world_x, src_world_y, dx_start, dy_start)
        
        # Get arrowhead position at target boundary
        arrowhead_x, arrowhead_y = self._get_boundary_point(
            self.target, tgt_world_x, tgt_world_y, -dx_end, -dy_end)
        
        # Draw curve to a point just before the boundary to avoid line showing through
        # Pull back by 2-3 pixels from boundary
        pullback = 3.0 / zoom
        end_world_x = arrowhead_x - dx_end * pullback
        end_world_y = arrowhead_y - dy_end * pullback
        
        # Add glow effect for colored arcs (CSS-like styling)
        if self.color != self.DEFAULT_COLOR:
            # Draw outer glow (subtle shadow effect)
            cr.move_to(start_world_x, start_world_y)
            cr.curve_to(cp_x, cp_y, cp_x, cp_y, end_world_x, end_world_y)
            r, g, b = self.color
            cr.set_source_rgba(r, g, b, 0.3)  # Semi-transparent color
            cr.set_line_width((self.width + 2) / max(zoom, 1e-6))
            cr.stroke()
        
        # Draw curve in world coordinates
        cr.move_to(start_world_x, start_world_y)
        cr.curve_to(cp_x, cp_y, cp_x, cp_y, end_world_x, end_world_y)
        cr.set_source_rgb(*self.color)
        cr.set_line_width(self.width / max(zoom, 1e-6))  # Compensate for zoom
        cr.stroke()
        
        # Draw arrowhead at target boundary (visible on top of target)
        self._render_arrowhead(cr, arrowhead_x, arrowhead_y, dx_end, dy_end, zoom)
        
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
        
        # Selection rendering moved to ObjectEditingTransforms in src/shypn/api/edit/
    
    def _render_weight_curved(self, cr, x1: float, y1: float, x2: float, y2: float,
                             cp_x: float, cp_y: float, curve_offset: Optional[float], 
                             zoom: float = 1.0):
        """Render weight label on curved arc.
        
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
                # (same calculation as in _calculate_curve_control_point)
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
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is near this curved arc.
        
        Uses bezier curve distance calculation instead of straight line.
        
        Args:
            x, y: Point coordinates (world space)
            
        Returns:
            bool: True if point is near the arc curve
        """
        try:
            # Check if manual control point is set (from transformation)
            if hasattr(self, 'manual_control_point') and self.manual_control_point is not None:
                # Use manual control point directly
                control_point = self.manual_control_point
            else:
                # Calculate offset for parallel arcs (same as rendering)
                offset_distance = None
                if hasattr(self, '_manager') and self._manager:
                    parallels = self._manager.detect_parallel_arcs(self)
                    if parallels:
                        offset_distance = self._manager.calculate_arc_offset(self, parallels)
                
                # Calculate control point with offset (same as rendering)
                control_point = self._calculate_curve_control_point(offset=offset_distance)
            
            if control_point is None:
                # Degenerate case: use straight line check
                return super().contains_point(x, y)
            
            cp_x, cp_y = control_point
            
            # Get source and target centers
            src_world_x, src_world_y = self.source.x, self.source.y
            tgt_world_x, tgt_world_y = self.target.x, self.target.y
            
            # Calculate tangent at start (direction from source to control point)
            dx_start = cp_x - src_world_x
            dy_start = cp_y - src_world_y
            length_start = math.sqrt(dx_start*dx_start + dy_start*dy_start)
            
            if length_start < 1e-6:
                return super().contains_point(x, y)
            
            dx_start /= length_start
            dy_start /= length_start
            
            # Calculate tangent at end (direction from control point to target)
            dx_end = tgt_world_x - cp_x
            dy_end = tgt_world_y - cp_y
            length_end = math.sqrt(dx_end*dx_end + dy_end*dy_end)
            
            if length_end < 1e-6:
                return super().contains_point(x, y)
            
            dx_end /= length_end
            dy_end /= length_end
            
            # Get boundary points (same as rendering)
            sx, sy = self._get_boundary_point(
                self.source, src_world_x, src_world_y, dx_start, dy_start)
            tx, ty = self._get_boundary_point(
                self.target, tgt_world_x, tgt_world_y, -dx_end, -dy_end)
            
            # Sample points along bezier curve and find minimum distance
            # Quadratic bezier: B(t) = (1-t)²*P0 + 2(1-t)t*P1 + t²*P2
            min_dist_sq = float('inf')
            samples = 20  # Number of samples along curve
            
            for i in range(samples + 1):
                t = i / samples
                
                # Quadratic bezier formula
                b0 = (1 - t) * (1 - t)
                b1 = 2 * (1 - t) * t
                b2 = t * t
                
                curve_x = b0 * sx + b1 * cp_x + b2 * tx
                curve_y = b0 * sy + b1 * cp_y + b2 * ty
                
                # Distance to sampled point
                dist_sq = (x - curve_x) ** 2 + (y - curve_y) ** 2
                min_dist_sq = min(min_dist_sq, dist_sq)
            
            # Calculate actual distance
            min_dist = math.sqrt(min_dist_sq)
            
            # Tolerance: 15 pixels in world space (generous for clicking)
            tolerance = 15.0
            
            return min_dist <= tolerance
            
        except Exception as e:
            # Fall back to straight line check on any error
            return super().contains_point(x, y)
    
    def to_dict(self) -> dict:
        """Serialize curved arc to dictionary for persistence.
        
        Returns:
            dict: Dictionary containing all arc properties with type 'curved_arc'
        """
        data = super().to_dict()
        data["object_type"] = "curved_arc"  # Override object_type to distinguish from Arc
        return data
    
    def __repr__(self):
        """String representation of the curved arc."""
        return (f"CurvedArc(id={self.id}, source={self.source.id}, "
                f"target={self.target.id}, weight={self.weight})")
