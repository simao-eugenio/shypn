#!/usr/bin/env python3
"""Arc - Directed connection in a Petri net.

Arcs connect places to transitions or transitions to places.
Rendered as an arrow with optional weight label.
"""
import math
from typing import List, Tuple
from shypn.netobjs.petri_net_object import PetriNetObject


class Arc(PetriNetObject):
    """A directed arc in a Petri net.
    
    Arcs connect places to transitions or transitions to places.
    Rendered as an arrow with optional weight label.
    """
    
    # Default styling (legacy renderer values)
    DEFAULT_COLOR = (0.0, 0.0, 0.0)  # Black
    DEFAULT_WIDTH = 3.0  # Legacy: 3.0px line width
    ARROW_SIZE = 15.0    # Legacy: 15px arrowhead length
    
    def __init__(self, source, target, id: str, name: str, weight: int = 1):
        """Initialize an Arc.
        
        Args:
            source: Source object instance (Place or Transition)
            target: Target object instance (Place or Transition)
            id: Unique string identifier (immutable, system-assigned)
            name: Unique name in format "A1", "A2", etc. (immutable, system-assigned)
            weight: Arc weight (multiplicity)
        
        Raises:
            ValueError: If source and target are of the same type (violates bipartite property)
        """
        # Validate bipartite connection (Place↔Transition only)
        self._validate_connection(source, target)
        
        # Initialize base class (arcs don't have user labels typically)
        super().__init__(id, name, label="")
        
        # Connection (references to object instances)
        self.source = source
        self.target = target
        self.weight = int(weight)
        
        # Styling
        self.color = self.DEFAULT_COLOR
        self.width = self.DEFAULT_WIDTH
        
        # Behavioral properties (formula support)
        self.threshold = None  # Threshold formula (can be dict, expression, or value)
        
        # Curved arc support
        self.is_curved = False  # Whether arc is curved or straight
        self.control_offset_x = 0.0  # X offset from midpoint for control point
        self.control_offset_y = 0.0  # Y offset from midpoint for control point
        
        # Control points for curved arcs (optional, legacy)
        self.control_points: List[Tuple[float, float]] = []
    
    @property
    def source_id(self) -> str:
        """Get source object ID (for behavior compatibility)."""
        return self.source.id
    
    @property
    def target_id(self) -> str:
        """Get target object ID (for behavior compatibility)."""
        return self.target.id
    
    @property
    def arc_type(self) -> str:
        """Get the arc type identifier.
        
        Returns:
            str: Arc type - "normal", "inhibitor", "test"
        """
        from shypn.netobjs.inhibitor_arc import InhibitorArc
        if isinstance(self, InhibitorArc):
            return "inhibitor"
        # Future: add "test" arc support
        return "normal"
    
    def set_arc_type(self, arc_type: str):
        """Set the arc type by converting to appropriate class.
        
        This method should be called by the dialog to trigger transformation.
        The actual transformation is handled by arc_transform utilities and
        the manager's replace_arc method.
        
        Args:
            arc_type: "normal", "inhibitor", or "test"
        
        Raises:
            ValueError: If arc_type is invalid or transformation fails validation
        """
        if arc_type == self.arc_type:
            return  # No change needed
        
        from shypn.utils.arc_transform import convert_to_inhibitor, convert_to_normal
        
        if arc_type == "inhibitor":
            # Will raise ValueError if Transition→Place
            new_arc = convert_to_inhibitor(self)
        elif arc_type == "normal":
            new_arc = convert_to_normal(self)
        elif arc_type == "test":
            raise NotImplementedError("Test arcs not yet implemented")
        else:
            raise ValueError(f"Unknown arc type: {arc_type}")
        
        # Replace self with new arc in manager
        if hasattr(self, '_manager') and self._manager:
            self._manager.replace_arc(self, new_arc)
        else:
            raise RuntimeError("Arc has no manager reference - cannot perform transformation")
    
    @staticmethod
    def _validate_connection(source, target):
        """Validate that connection follows bipartite property.
        
        Petri nets are bipartite graphs: arcs must connect Place↔Transition only.
        - Valid: Place → Transition
        - Valid: Transition → Place
        - Invalid: Place → Place
        - Invalid: Transition → Transition
        
        Args:
            source: Source object
            target: Target object
        
        Raises:
            ValueError: If source and target are of the same type
        """
        from shypn.netobjs.place import Place
        from shypn.netobjs.transition import Transition
        
        source_is_place = isinstance(source, Place)
        target_is_place = isinstance(target, Place)
        
        # Both are places or both are transitions → invalid
        if source_is_place == target_is_place:
            source_type = "Place" if source_is_place else "Transition"
            target_type = "Place" if target_is_place else "Transition"
            raise ValueError(
                f"Invalid connection: {source_type} → {target_type}. "
                f"Arcs must connect Place↔Transition (bipartite property). "
                f"Valid connections: Place→Transition or Transition→Place."
            )
    
    def render(self, cr, transform=None, zoom=1.0):
        """Render the arc using Cairo.
        
        Uses legacy rendering style with Cairo transform approach:
        - 3.0px line width (compensated for zoom to maintain constant pixel size)
        - Two-line arrowhead (15px, π/5 angle)
        - Bold Arial 12pt weight text with white background
        - Only shows weight if > 1
        - Draws in world coordinates (Cairo transform handles scaling)
        
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
        
        # Calculate direction in world space
        dx_world = tgt_world_x - src_world_x
        dy_world = tgt_world_y - src_world_y
        length_world = math.sqrt(dx_world * dx_world + dy_world * dy_world)
        
        if length_world < 1:
            return  # Too short to draw
        
        # Normalize direction
        dx_world /= length_world
        dy_world /= length_world
        
        # Get boundary points using straight-line direction from actual centers
        start_world_x, start_world_y = self._get_boundary_point(
            self.source, src_world_x, src_world_y, dx_world, dy_world)
        end_world_x, end_world_y = self._get_boundary_point(
            self.target, tgt_world_x, tgt_world_y, -dx_world, -dy_world)
        
        # Check for parallel arcs - offset will be applied to control point only
        parallel_offset = 0.0
        if hasattr(self, '_manager') and self._manager:
            parallels = self._manager.detect_parallel_arcs(self)
            if parallels:
                parallel_offset = self._manager.calculate_arc_offset(self, parallels)
        
        # Endpoints stay at boundaries (not offset)
        display_start_x = start_world_x
        display_start_y = start_world_y
        display_end_x = end_world_x
        display_end_y = end_world_y
        display_start_x = start_world_x
        display_start_y = start_world_y
        display_end_x = end_world_x
        display_end_y = end_world_y
        
        # Calculate control point for curved arcs
        # Control point uses offset from the midpoint between boundary points
        if self.is_curved:
            mid_x = (start_world_x + end_world_x) / 2
            mid_y = (start_world_y + end_world_y) / 2
            
            # Apply parallel arc offset to the midpoint (perpendicular to arc direction)
            if abs(parallel_offset) > 1e-6:
                perp_x = -dy_world
                perp_y = dx_world
                mid_x += perp_x * parallel_offset
                mid_y += perp_y * parallel_offset
            
            control_x = mid_x + self.control_offset_x
            control_y = mid_y + self.control_offset_y
        
        # Add glow effect for colored arcs (CSS-like styling)
        if self.color != self.DEFAULT_COLOR:
            # Draw outer glow (subtle shadow effect)
            if self.is_curved:
                cr.move_to(display_start_x, display_start_y)
                cr.curve_to(control_x, control_y, control_x, control_y, display_end_x, display_end_y)
            else:
                cr.move_to(display_start_x, display_start_y)
                cr.line_to(display_end_x, display_end_y)
            r, g, b = self.color
            cr.set_source_rgba(r, g, b, 0.3)  # Semi-transparent color
            cr.set_line_width((self.width + 2) / max(zoom, 1e-6))
            cr.stroke()
        
        # Draw line in world coordinates (straight or curved)
        if self.is_curved:
            cr.move_to(display_start_x, display_start_y)
            cr.curve_to(control_x, control_y, control_x, control_y, display_end_x, display_end_y)
        else:
            cr.move_to(display_start_x, display_start_y)
            cr.line_to(display_end_x, display_end_y)
        cr.set_source_rgb(*self.color)
        cr.set_line_width(self.width / max(zoom, 1e-6))  # Compensate for zoom
        cr.stroke()
        
        # Calculate direction at end point for arrowhead
        if self.is_curved:
            # For curved arc, calculate tangent at end point
            # Using simple approximation: direction from control point to end
            arrow_dx = display_end_x - control_x
            arrow_dy = display_end_y - control_y
            arrow_length = math.sqrt(arrow_dx * arrow_dx + arrow_dy * arrow_dy)
            if arrow_length > 1e-6:
                arrow_dx /= arrow_length
                arrow_dy /= arrow_length
            else:
                arrow_dx, arrow_dy = dx_world, dy_world
        else:
            arrow_dx, arrow_dy = dx_world, dy_world
        
        # Draw arrowhead at target (with zoom compensation)
        self._render_arrowhead(cr, display_end_x, display_end_y, arrow_dx, arrow_dy, zoom)
        
        # Draw weight label if > 1
        if self.weight > 1:
            self._render_weight(cr, display_start_x, display_start_y, display_end_x, display_end_y, zoom)
        
        # Ensure clean state for next rendering operation
        cr.new_path()
        
        # Selection rendering moved to ObjectEditingTransforms in src/shypn/api/edit/
    
    def _get_boundary_point(self, obj, cx: float, cy: float, 
                           dx: float, dy: float) -> Tuple[float, float]:
        """Calculate where arc intersects object boundary.
        
        The border stroke is centered on the mathematical perimeter:
        - Inner edge at perimeter - border_width/2 (-1.5px for 3px border)
        - Outer edge at perimeter + border_width/2 (+1.5px for 3px border)
        
        For natural appearance, arcs should touch at the OUTER edge of the border,
        which is the visible boundary of the object.
        
        Args:
            obj: Place or Transition object
            cx, cy: Object center
            dx, dy: Direction vector (normalized)
            
        Returns:
            tuple: (x, y) point at outer edge of object border
        """
        # Import here to avoid circular dependency
        from shypn.netobjs.place import Place
        from shypn.netobjs.transition import Transition
        
        if isinstance(obj, Place):
            # Circle: radius + half border width to reach outer edge
            border_width = getattr(obj, 'border_width', 3.0)
            border_offset = border_width / 2.0  # +1.5px for 3px border
            effective_radius = obj.radius + border_offset
            
            result = (cx + dx * effective_radius, cy + dy * effective_radius)
            return result
            
        elif isinstance(obj, Transition):
            # Rectangle: dimensions + half border width to reach outer edge
            border_width = getattr(obj, 'border_width', 3.0)
            border_offset = border_width / 2.0  # +1.5px for 3px border
            
            # Rectangle dimensions (accounting for orientation)
            w = obj.width if obj.horizontal else obj.height
            h = obj.height if obj.horizontal else obj.width
            
            # Extend to outer edge of border
            half_w = w / 2 + border_offset
            half_h = h / 2 + border_offset
            
            # Calculate intersection with rectangle edges
            # The rectangle is axis-aligned in world space
            # We need to find which edge the ray intersects first
            
            # Avoid division by zero
            if abs(dx) < 1e-10:
                dx = 1e-10
            if abs(dy) < 1e-10:
                dy = 1e-10
            
            # Calculate t values for intersection with each edge
            # Ray: (cx, cy) + t * (dx, dy)
            # Edges: x = cx ± half_w, y = cy ± half_h
            
            # Right/Left edges (x = cx ± half_w)
            t_right = half_w / dx if dx > 0 else float('inf')
            t_left = -half_w / dx if dx < 0 else float('inf')
            
            # Top/Bottom edges (y = cy ± half_h)
            t_bottom = half_h / dy if dy > 0 else float('inf')
            t_top = -half_h / dy if dy < 0 else float('inf')
            
            # Find minimum positive t (closest intersection)
            t = min(t_right, t_left, t_bottom, t_top)
            
            # Calculate intersection point
            # Clamp to rectangle bounds to handle floating point errors
            intersect_x = cx + t * dx
            intersect_y = cy + t * dy
            intersect_x = max(cx - half_w, min(cx + half_w, intersect_x))
            intersect_y = max(cy - half_h, min(cy + half_h, intersect_y))
            
            result = (intersect_x, intersect_y)
            return result
        else:
            # Unknown object type: use center
            return (cx, cy)
    
    def _render_arrowhead(self, cr, x: float, y: float, dx: float, dy: float, zoom: float = 1.0):
        """Render two-line arrowhead at arrow tip (legacy style).
        
        Legacy rendering characteristics:
        - Two separate lines (not a filled triangle)
        - 15px length (compensated for zoom), π/5 angle (36 degrees)
        - Same color and width as arc line
        
        Args:
            cr: Cairo context
            x, y: Arrow tip position (world coords)
            dx, dy: Direction vector (normalized, world space)
            zoom: Current zoom level for size compensation
        """
        # Legacy style: π/5 angle (36 degrees, not 30)
        angle = math.atan2(dy, dx)
        arrow_angle = math.pi / 5  # 36 degrees
        
        # Arrow size compensated for zoom (15px constant screen size)
        arrow_size = self.ARROW_SIZE / zoom
        
        # Calculate wing endpoints
        left_x = x - arrow_size * math.cos(angle - arrow_angle)
        left_y = y - arrow_size * math.sin(angle - arrow_angle)
        
        right_x = x - arrow_size * math.cos(angle + arrow_angle)
        right_y = y - arrow_size * math.sin(angle + arrow_angle)
        
        # Draw two lines (legacy style, not filled triangle)
        cr.set_source_rgb(*self.color)
        cr.set_line_width(self.width / max(zoom, 1e-6))
        
        # Left wing line
        cr.move_to(x, y)
        cr.line_to(left_x, left_y)
        cr.stroke()
        
        # Right wing line
        cr.move_to(x, y)
        cr.line_to(right_x, right_y)
        cr.stroke()
    
    def _render_weight(self, cr, x1: float, y1: float, x2: float, y2: float, zoom: float = 1.0):
        """Render weight label near the arc midpoint.
        
        Uses legacy rendering style:
        - Bold Arial 12pt font (compensated for zoom)
        - White semi-transparent background (0.8 alpha)
        - Positioned perpendicular to arc
        
        Args:
            cr: Cairo context
            x1, y1: Start point (world coords)
            x2, y2: End point (world coords)
            zoom: Current zoom level for font/offset compensation
        """
        # Save context to avoid interfering with other rendering
        cr.save()
        
        # Calculate midpoint
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        # Legacy style: Bold Arial 12pt (compensated for zoom)
        cr.select_font_face("Arial", 0, 1)  # Normal slant, Bold weight
        cr.set_font_size(12 / zoom)
        text = str(self.weight)
        extents = cr.text_extents(text)
        
        # Calculate perpendicular offset (11px screen size = 11/zoom world space)
        offset = 11 / zoom
        dx = y2 - y1  # Perpendicular direction
        dy = x1 - x2
        length = math.sqrt(dx * dx + dy * dy)
        if length > 0:
            dx = dx / length * offset
            dy = dy / length * offset
        
        # Text position (centered)
        text_x = mid_x + dx - extents.width / 2
        text_y = mid_y + dy + extents.height / 2
        
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
        """Check if a point is near this arc.
        
        Arcs are thin and harder to click, so this uses a tolerance distance.
        Takes into account parallel arc offsets for accurate hit detection.
        
        Args:
            x, y: Point coordinates (world space)
            
        Returns:
            bool: True if point is near the arc line
        """
        # Get source and target positions
        src_x, src_y = self.source.x, self.source.y
        tgt_x, tgt_y = self.target.x, self.target.y
        
        # Check if this arc has parallel arcs and get offset for control point
        parallel_offset = 0.0
        if hasattr(self, '_manager') and self._manager:
            try:
                parallels = self._manager.detect_parallel_arcs(self)
                if parallels:
                    parallel_offset = self._manager.calculate_arc_offset(self, parallels)
            except (AttributeError, Exception):
                pass
        
        # Tolerance: Account for visual stroke width plus comfortable margin
        # The arc centerline is measured, but users click on the visible stroke
        # Stroke width is 3px (self.width), so half-width is 1.5px
        # Add generous margin for comfortable clicking
        half_stroke = self.width / 2.0
        # Treat parallel arcs as curves for hit detection (even if not is_curved)
        has_parallel = abs(parallel_offset) > 1e-6
        click_margin = 25.0 if (self.is_curved or has_parallel) else 8.0
        tolerance = half_stroke + click_margin
        
        # Handle curved arcs and parallel "straight" arcs (which render as curves)
        if self.is_curved or abs(parallel_offset) > 1e-6:
            # Calculate direction for boundary points
            dx = tgt_x - src_x
            dy = tgt_y - src_y
            length = (dx * dx + dy * dy) ** 0.5
            
            if length < 1e-6:
                return False  # Degenerate arc
            
            dx_norm = dx / length
            dy_norm = dy / length
            
            # Get boundary points from ACTUAL centers (same as rendering)
            start_x, start_y = self._get_boundary_point(self.source, src_x, src_y, dx_norm, dy_norm)
            end_x, end_y = self._get_boundary_point(self.target, tgt_x, tgt_y, -dx_norm, -dy_norm)
            
            # Calculate control point from BOUNDARY midpoint
            mid_x = (start_x + end_x) / 2
            mid_y = (start_y + end_y) / 2
            
            # Apply parallel arc offset perpendicular to arc direction
            if abs(parallel_offset) > 1e-6:
                perp_x = -dy_norm
                perp_y = dx_norm
                mid_x += perp_x * parallel_offset
                mid_y += perp_y * parallel_offset
            
            control_x = mid_x + self.control_offset_x
            control_y = mid_y + self.control_offset_y
            
            # Sample points along the Bezier curve and find minimum distance
            min_dist_sq = float('inf')
            num_samples = 50  # Increase samples for better accuracy (was 20)
            
            for i in range(num_samples + 1):
                t = i / num_samples
                # Quadratic Bezier formula: B(t) = (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
                one_minus_t = 1.0 - t
                curve_x = (one_minus_t * one_minus_t * start_x + 
                          2 * one_minus_t * t * control_x + 
                          t * t * end_x)
                curve_y = (one_minus_t * one_minus_t * start_y + 
                          2 * one_minus_t * t * control_y + 
                          t * t * end_y)
                
                # Distance from point to this sample point on curve
                dist_sq = (x - curve_x) ** 2 + (y - curve_y) ** 2
                min_dist_sq = min(min_dist_sq, dist_sq)
            
            return min_dist_sq <= (tolerance * tolerance)
        else:
            # Straight arc: use line segment distance
            # Need to account for parallel offset
            dx = tgt_x - src_x
            dy = tgt_y - src_y
            length = (dx * dx + dy * dy) ** 0.5
            
            if length < 1e-6:
                return False  # Degenerate arc
            
            dx_norm = dx / length
            dy_norm = dy / length
            
            # Get boundary points (same as rendering)
            start_x, start_y = self._get_boundary_point(self.source, src_x, src_y, dx_norm, dy_norm)
            end_x, end_y = self._get_boundary_point(self.target, tgt_x, tgt_y, -dx_norm, -dy_norm)
            
            # Apply parallel offset to straight line (same as rendering)
            if abs(parallel_offset) > 1e-6:
                perp_x = -dy_norm
                perp_y = dx_norm
                start_x += perp_x * parallel_offset
                start_y += perp_y * parallel_offset
                end_x += perp_x * parallel_offset
                end_y += perp_y * parallel_offset
            
            # Calculate line segment parameters
            seg_dx = end_x - start_x
            seg_dy = end_y - start_y
            length_sq = seg_dx * seg_dx + seg_dy * seg_dy
            
            if length_sq < 1e-6:
                return False
            
            # Calculate closest point on line segment to (x, y)
            # Parameter t represents position along line: 0=start, 1=end
            t = max(0.0, min(1.0, ((x - start_x) * seg_dx + (y - start_y) * seg_dy) / length_sq))
            
            # Closest point on segment
            closest_x = start_x + t * seg_dx
            closest_y = start_y + t * seg_dy
            
            # Distance from point to line segment
            dist_sq = (x - closest_x) ** 2 + (y - closest_y) ** 2
            
            return dist_sq <= (tolerance * tolerance)
    
    def set_position(self, x: float, y: float):
        """Arcs don't have a direct position (they connect other objects).
        
        This method is not applicable for arcs.
        
        Args:
            x, y: Position (ignored)
        """
        pass  # Arcs move when their source/target objects move
    
    def set_weight(self, weight: int):
        """Set the arc weight.
        
        Args:
            weight: New weight (positive integer)
        """
        self.weight = max(1, weight)
        self._trigger_redraw()
    
    def to_dict(self) -> dict:
        """Serialize arc to dictionary for persistence.
        
        Note: Arcs store references to source/target by ID, not the object itself.
        The actual object references must be restored during deserialization.
        
        Returns:
            dict: Dictionary containing all arc properties
        """
        from shypn.netobjs.place import Place
        
        data = super().to_dict()  # Get base properties (id, name, label)
        data.update({
            "type": "arc",
            "source_id": self.source.id,
            "source_type": "place" if isinstance(self.source, Place) else "transition",
            "target_id": self.target.id,
            "target_type": "place" if isinstance(self.target, Place) else "transition",
            "weight": self.weight,
            "color": list(self.color),
            "width": self.width,
            "control_points": self.control_points
        })
        return data
    
    @classmethod
    def from_dict(cls, data: dict, places: dict, transitions: dict) -> 'Arc':
        """Create arc from dictionary (deserialization).
        
        NOTE: source_id and target_id can be either:
        - Integer IDs (modern format) - look up by ID
        - String names like 'P45', 'T12' (legacy format) - look up by name
        
        The places/transitions dicts are keyed by integer IDs, so for legacy
        string names, we need to find objects by name instead.
        
        Args:
            data: Dictionary containing arc properties
            places: Dictionary mapping place IDs to Place instances
            transitions: Dictionary mapping transition IDs to Transition instances
            
        Returns:
            Arc: New arc instance with restored properties
            
        Raises:
            ValueError: If source or target objects not found
        """
        # Resolve source and target references (handle both int IDs and string names)
        raw_source_id = data["source_id"]
        raw_target_id = data["target_id"]
        
        # Helper function to find object by ID (string or int) or name
        def find_object(raw_id, obj_dict, obj_type_name):
            # Try looking up by ID directly (works for both string and int IDs)
            obj = obj_dict.get(raw_id)
            if obj is not None:
                return obj
            
            # If not found, try converting to string (in case dict keys are strings)
            obj = obj_dict.get(str(raw_id))
            if obj is not None:
                return obj
            
            # Last resort: search by name (for legacy compatibility)
            for obj in obj_dict.values():
                if obj.name == str(raw_id):
                    return obj
            
            raise ValueError(f"{obj_type_name} not found with ID/name: {raw_id}")
        
        # Find source object
        if data["source_type"] == "place":
            source = find_object(raw_source_id, places, "Source place")
        else:
            source = find_object(raw_source_id, transitions, "Source transition")
        
        # Find target object
        if data["target_type"] == "place":
            target = find_object(raw_target_id, places, "Target place")
        else:
            target = find_object(raw_target_id, transitions, "Target transition")
        
        # Handle arc ID (keep as string, don't convert to int)
        arc_id = str(data.get("id"))  # Always store as string
        arc_name = str(data.get("name", f"A{arc_id}"))
        
        # Create arc
        arc = cls(
            source=source,
            target=target,
            id=arc_id,  # String ID
            name=arc_name,
            weight=int(data.get("weight", 1))
        )
        
        # Restore optional properties
        if "color" in data:
            arc.color = tuple(data["color"])
        if "width" in data:
            arc.width = data["width"]
        if "control_points" in data:
            arc.control_points = data["control_points"]
        
        return arc
    
    @staticmethod
    def create_from_dict(data: dict, places: dict, transitions: dict) -> 'Arc':
        """Factory method to create appropriate arc subclass from dictionary.
        
        This method examines the 'type' field in the data and creates the
        appropriate Arc subclass (Arc, InhibitorArc, CurvedArc, or CurvedInhibitorArc).
        
        Args:
            data: Dictionary containing arc properties
            places: Dictionary mapping place IDs to Place instances
            transitions: Dictionary mapping transition IDs to Transition instances
            
        Returns:
            Arc: Instance of appropriate Arc subclass
            
        Raises:
            ValueError: If source or target objects not found
        """
        arc_type = data.get("type", "arc")
        
        # Import subclasses here to avoid circular imports
        if arc_type == "inhibitor_arc":
            from shypn.netobjs.inhibitor_arc import InhibitorArc
            return InhibitorArc.from_dict(data, places, transitions)
        elif arc_type == "curved_arc":
            from shypn.netobjs.curved_arc import CurvedArc
            return CurvedArc.from_dict(data, places, transitions)
        elif arc_type == "curved_inhibitor_arc":
            from shypn.netobjs.curved_inhibitor_arc import CurvedInhibitorArc
            return CurvedInhibitorArc.from_dict(data, places, transitions)
        else:
            # Default to Arc for backward compatibility
            return Arc.from_dict(data, places, transitions)
