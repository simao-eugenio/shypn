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
    
    def _calculate_curve_control_point(self) -> Optional[Tuple[float, float]]:
        """Calculate bezier control point for curved arc.
        
        Creates a curve that bows perpendicular to the straight line
        connecting source and target. Used for opposite arcs.
        
        Returns:
            tuple: (x, y) control point coordinates, or None if degenerate
        """
        # Get source and target positions
        sx, sy = self.source.x, self.source.y
        tx, ty = self.target.x, self.target.y
        
        # Calculate midpoint
        mx = (sx + tx) / 2
        my = (sy + ty) / 2
        
        # Vector from source to target
        dx = tx - sx
        dy = ty - sy
        length = math.sqrt(dx*dx + dy*dy)
        
        if length < 1e-6:
            return None  # Degenerate case: same point
        
        # Unit perpendicular vector (rotated 90° counterclockwise)
        perp_x = -dy / length
        perp_y = dx / length
        
        # Control point offset: 20% of line length
        offset = length * self.CURVE_OFFSET_RATIO
        
        # Control point at midpoint + perpendicular offset
        cp_x = mx + perp_x * offset
        cp_y = my + perp_y * offset
        
        return (cp_x, cp_y)
    
    def render(self, cr, transform=None, zoom=1.0):
        """Render curved arc using bezier path.
        
        Overrides Arc.render() to draw a quadratic bezier curve
        instead of a straight line.
        
        Args:
            cr: Cairo context (with zoom transformation already applied)
            transform: Optional function (deprecated, for backward compatibility)
            zoom: Current zoom level for line width compensation
        """
        # Get source and target positions in world space
        src_world_x, src_world_y = self.source.x, self.source.y
        tgt_world_x, tgt_world_y = self.target.x, self.target.y
        
        # Calculate control point
        control_point = self._calculate_curve_control_point()
        
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
        end_world_x, end_world_y = self._get_boundary_point(
            self.target, tgt_world_x, tgt_world_y, dx_end, dy_end)
        
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
        
        # Draw arrowhead at target (using tangent at end)
        self._render_arrowhead(cr, end_world_x, end_world_y, dx_end, dy_end, zoom)
        
        # Draw weight label if > 1
        if self.weight > 1:
            self._render_weight(cr, start_world_x, start_world_y, end_world_x, end_world_y, zoom)
        
        # Selection rendering moved to ObjectEditingTransforms in src/shypn/api/edit/
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is near this curved arc.
        
        Uses bezier curve distance calculation instead of straight line.
        
        Args:
            x, y: Point coordinates (world space)
            
        Returns:
            bool: True if point is near the arc curve
        """
        # Calculate control point
        control_point = self._calculate_curve_control_point()
        
        if control_point is None:
            # Degenerate case: use straight line check
            return super().contains_point(x, y)
        
        cp_x, cp_y = control_point
        
        # Sample points along bezier curve and find minimum distance
        # Quadratic bezier: B(t) = (1-t)²*P0 + 2(1-t)t*P1 + t²*P2
        sx, sy = self.source.x, self.source.y
        tx, ty = self.target.x, self.target.y
        
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
        
        # Tolerance: 10 pixels in world space (generous for clicking)
        tolerance = 10.0
        
        return min_dist_sq <= (tolerance * tolerance)
    
    def to_dict(self) -> dict:
        """Serialize curved arc to dictionary for persistence.
        
        Returns:
            dict: Dictionary containing all arc properties with type 'curved_arc'
        """
        data = super().to_dict()
        data["type"] = "curved_arc"  # Override type to distinguish from Arc
        return data
    
    def __repr__(self):
        """String representation of the curved arc."""
        return (f"CurvedArc(id={self.id}, source={self.source.id}, "
                f"target={self.target.id}, weight={self.weight})")
