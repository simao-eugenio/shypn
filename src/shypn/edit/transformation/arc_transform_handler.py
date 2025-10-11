"""
Arc transformation handler for curve/straight toggle and control point adjustment.

This module implements the ArcTransformHandler which allows users to:
- Toggle between straight and curved arcs
- Adjust the control point position for curved arcs
"""

from typing import Optional, Dict, Any, Tuple

from shypn.edit.transformation.transform_handler import TransformHandler


class ArcTransformHandler(TransformHandler):
    """Handles arc transformation operations.
    
    This handler supports:
    - Single handle at arc midpoint
    - Click handle to toggle straight/curved
    - Drag handle to adjust control point (for curved arcs)
    
    Attributes:
        arc_being_transformed: The arc currently being transformed
        original_geometry: Dictionary storing original arc properties
        handle_position: Position of the single control handle
    """
    
    # Minimum curve distance from straight line
    MIN_CURVE_OFFSET = 20.0
    MAX_CURVE_OFFSET = 200.0
    
    def __init__(self, selection_manager):
        """Initialize the arc transform handler.
        
        Args:
            selection_manager: The SelectionManager instance
        """
        super().__init__(selection_manager)
        self.arc_being_transformed = None
        self.handle_position: Optional[Tuple[float, float]] = None
        self.is_dragging = False
    
    def can_transform(self, obj) -> bool:
        """Check if this handler can transform the given object.
        
        Arc transformation is only supported for Arc objects.
        
        Args:
            obj: The object to check
            
        Returns:
            True if object is an Arc
        """
        from shypn.netobjs import Arc
        from shypn.netobjs.curved_arc import CurvedArc
        # Support both Arc (with is_curved) and CurvedArc (separate class)
        return isinstance(obj, Arc)
    
    def start_transform(self, obj, handle: str, start_x: float, start_y: float):
        """Start arc transformation operation.
        
        For arcs, we only have one handle (at the midpoint).
        Starting a transformation sets up for either:
        - Toggle straight/curved (if released without drag)
        - Adjust control point (if dragged)
        
        Args:
            obj: The arc being transformed
            handle: Handle identifier (should be 'midpoint' for arcs)
            start_x: Initial X coordinate in world space
            start_y: Initial Y coordinate in world space
        """
        from shypn.netobjs.curved_arc import CurvedArc
        
        self.is_active = True
        self.arc_being_transformed = obj
        self.drag_start_pos = (start_x, start_y)
        self.is_dragging = False
        
        # Check if this is a CurvedArc (legacy class) or Arc with is_curved flag
        self.is_curved_arc_class = isinstance(obj, CurvedArc)
        
        if self.is_curved_arc_class:
            # CurvedArc: add manual override properties if not present
            if not hasattr(obj, 'manual_control_point'):
                obj.manual_control_point = None  # None = use automatic calculation
            
            # Store original state
            self.original_geometry = {
                'type': 'curved_arc',
                'manual_control_point': obj.manual_control_point,
            }
        else:
            # Arc with is_curved flag
            self.original_geometry = {
                'type': 'arc',
                'is_curved': obj.is_curved,
                'control_offset_x': obj.control_offset_x if hasattr(obj, 'control_offset_x') else 0.0,
                'control_offset_y': obj.control_offset_y if hasattr(obj, 'control_offset_y') else 0.0,
            }
        
        self.original_state = self.original_geometry.copy()
    
    def update_transform(self, current_x: float, current_y: float):
        """Update arc transformation during drag.
        
        If the user drags the handle, we adjust the control point offset.
        
        Args:
            current_x: Current X coordinate in world space
            current_y: Current Y coordinate in world space
        """
        if not self.is_active or not self.drag_start_pos:
            return
        
        arc = self.arc_being_transformed
        start_x, start_y = self.drag_start_pos
        
        # Check if user has dragged enough to consider it a drag operation
        dx = current_x - start_x
        dy = current_y - start_y
        drag_distance = (dx * dx + dy * dy) ** 0.5
        
        if drag_distance > 5.0:  # 5 units threshold
            self.is_dragging = True
            
            # Update control point based on arc type
            if self.is_curved_arc_class:
                # CurvedArc: set manual control point with constraint
                self._update_curved_arc_control_point(arc, current_x, current_y)
            else:
                # Arc with is_curved: make sure it's curved and update offsets
                if not arc.is_curved:
                    arc.is_curved = True
                
                # Calculate control point offset from arc midpoint
                self._update_control_point(arc, current_x, current_y)
    
    def _update_curved_arc_control_point(self, arc, control_x: float, control_y: float):
        """Update the CurvedArc's manual control point position with constraint.
        
        Similar to _update_control_point but for CurvedArc (legacy) class.
        Applies MAX_CURVE_OFFSET constraint from arc midpoint.
        For parallel arcs, must account for the parallel arc offset.
        
        Args:
            arc: The CurvedArc object
            control_x: Desired X coordinate of control point (world space)
            control_y: Desired Y coordinate of control point (world space)
        """
        # Calculate arc endpoints
        src_x, src_y = arc.source.x, arc.source.y
        tgt_x, tgt_y = arc.target.x, arc.target.y
        
        # Calculate direction and length
        dx = tgt_x - src_x
        dy = tgt_y - src_y
        length = (dx * dx + dy * dy) ** 0.5
        
        # Check for parallel arcs and apply offset (same as rendering)
        offset_distance = 0.0
        if hasattr(arc, '_manager') and arc._manager:
            parallels = arc._manager.detect_parallel_arcs(arc)
            if parallels:
                offset_distance = arc._manager.calculate_arc_offset(arc, parallels)
        
        # Apply parallel arc offset to endpoints if needed
        if abs(offset_distance) > 1e-6 and length > 1e-6:
            # Normalize direction
            dx_norm = dx / length
            dy_norm = dy / length
            
            # Perpendicular vector (90° counterclockwise rotation)
            perp_x = -dy_norm
            perp_y = dx_norm
            
            # Offset the endpoints
            src_x += perp_x * offset_distance
            src_y += perp_y * offset_distance
            tgt_x += perp_x * offset_distance
            tgt_y += perp_y * offset_distance
        
        # Calculate midpoint (after parallel offset, matching rendering)
        mid_x = (src_x + tgt_x) / 2
        mid_y = (src_y + tgt_y) / 2
        
        # Calculate offset from midpoint
        offset_x = control_x - mid_x
        offset_y = control_y - mid_y
        
        # Apply constraints (max distance from midpoint)
        offset_distance = (offset_x * offset_x + offset_y * offset_y) ** 0.5
        
        if offset_distance > self.MAX_CURVE_OFFSET:
            # Clamp to maximum offset
            scale = self.MAX_CURVE_OFFSET / offset_distance
            offset_x *= scale
            offset_y *= scale
        
        # Set constrained manual control point
        arc.manual_control_point = (mid_x + offset_x, mid_y + offset_y)
    
    def _update_control_point(self, arc, control_x: float, control_y: float):
        """Update the arc's control point position.
        
        The control point is stored as an offset from the arc's midpoint.
        For parallel arcs, the midpoint must account for the parallel arc offset
        the same way rendering does.
        
        Args:
            arc: The arc object
            control_x: Desired X coordinate of control point (world space)
            control_y: Desired Y coordinate of control point (world space)
        """
        # Calculate arc endpoints
        src_x, src_y = arc.source.x, arc.source.y
        tgt_x, tgt_y = arc.target.x, arc.target.y
        
        # Calculate direction and length
        dx = tgt_x - src_x
        dy = tgt_y - src_y
        length = (dx * dx + dy * dy) ** 0.5
        
        # Check for parallel arcs - offset will be applied to control point
        parallel_offset = 0.0
        if hasattr(arc, '_manager') and arc._manager:
            parallels = arc._manager.detect_parallel_arcs(arc)
            if parallels:
                parallel_offset = arc._manager.calculate_arc_offset(arc, parallels)
        
        # Get boundary points from ACTUAL centers (same calculation as in arc.render())
        # This ensures offset is relative to actual arc endpoints, not offset centers
        dx_norm = dx / length if length > 1e-6 else 1.0
        dy_norm = dy / length if length > 1e-6 else 0.0
        
        start_x, start_y = arc._get_boundary_point(arc.source, src_x, src_y, dx_norm, dy_norm)
        end_x, end_y = arc._get_boundary_point(arc.target, tgt_x, tgt_y, -dx_norm, -dy_norm)
        
        # Calculate midpoint from BOUNDARY points
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2
        
        # Apply parallel arc offset perpendicular to arc direction
        if abs(parallel_offset) > 1e-6:
            perp_x = -dy_norm
            perp_y = dx_norm
            mid_x += perp_x * parallel_offset
            mid_y += perp_y * parallel_offset
        
        # Calculate offset from (potentially offset) midpoint
        offset_x = control_x - mid_x
        offset_y = control_y - mid_y
        
        # Apply constraints (max distance from midpoint)
        offset_distance = (offset_x * offset_x + offset_y * offset_y) ** 0.5
        
        if offset_distance > self.MAX_CURVE_OFFSET:
            # Clamp to maximum offset
            scale = self.MAX_CURVE_OFFSET / offset_distance
            offset_x *= scale
            offset_y *= scale
        
        # Update arc control offsets
        arc.control_offset_x = offset_x
        arc.control_offset_y = offset_y
    
    def end_transform(self) -> bool:
        """Complete the arc transformation.
        
        If the user didn't drag (just clicked), toggle straight/curved.
        If the user dragged, the control point has been adjusted.
        
        Returns:
            True if transformation was successful
        """
        if not self.is_active:
            return False
        
        arc = self.arc_being_transformed
        
        # If not dragging, toggle straight/curved
        if not self.is_dragging:
            if self.is_curved_arc_class:
                # CurvedArc: toggle by setting/clearing manual_control_point
                if arc.manual_control_point is not None:
                    # Currently curved (manual override) -> make straight
                    arc.manual_control_point = None
                else:
                    # Currently straight (using automatic) -> make curved with manual point
                    # Set a default control point using the automatic calculation
                    auto_cp = arc._calculate_curve_control_point()
                    if auto_cp:
                        arc.manual_control_point = auto_cp
                    else:
                        # Fallback: set manual point at midpoint offset
                        src_x, src_y = arc.source.x, arc.source.y
                        tgt_x, tgt_y = arc.target.x, arc.target.y
                        mid_x = (src_x + tgt_x) / 2
                        mid_y = (src_y + tgt_y) / 2
                        arc.manual_control_point = (mid_x, mid_y - 30)
            else:
                # Arc: toggle is_curved flag
                arc.is_curved = not arc.is_curved
                
                # If switching to curved, set a default control offset
                if arc.is_curved:
                    self._set_default_control_offset(arc)
                else:
                    # If switching to straight, eliminate the offsets
                    arc.control_offset_x = 0.0
                    arc.control_offset_y = 0.0
        
        # Check if anything changed
        if self.is_curved_arc_class:
            changed = (arc.manual_control_point != self.original_geometry['manual_control_point'])
        else:
            changed = (
                arc.is_curved != self.original_geometry['is_curved'] or
                abs(arc.control_offset_x - self.original_geometry['control_offset_x']) > 0.1 or
                abs(arc.control_offset_y - self.original_geometry['control_offset_y']) > 0.1
            )
        
        # Reset handler state
        self.reset()
        
        return changed
    
    def _set_default_control_offset(self, arc):
        """Set a default control point offset when switching to curved.
        
        Creates a perpendicular offset from the arc midpoint.
        
        Args:
            arc: The arc object
        """
        # Calculate arc direction
        src_x, src_y = arc.source.x, arc.source.y
        tgt_x, tgt_y = arc.target.x, arc.target.y
        
        dx = tgt_x - src_x
        dy = tgt_y - src_y
        length = (dx * dx + dy * dy) ** 0.5
        
        if length < 1:
            # Arc is too short, use default offset
            arc.control_offset_x = 0.0
            arc.control_offset_y = -30.0
            return
        
        # Normalize direction
        dx /= length
        dy /= length
        
        # Create perpendicular vector (rotate 90 degrees)
        perp_x = -dy
        perp_y = dx
        
        # Set offset perpendicular to arc, scaled by arc length
        offset_distance = min(50.0, length * 0.3)
        arc.control_offset_x = perp_x * offset_distance
        arc.control_offset_y = perp_y * offset_distance
    
    def cancel_transform(self):
        """Cancel the arc transformation and restore original state.
        
        This restores the arc to its original straight/curved state
        and control point position.
        """
        if not self.is_active or not self.arc_being_transformed:
            return
        
        arc = self.arc_being_transformed
        orig = self.original_geometry
        
        # Restore original arc properties based on type
        if self.is_curved_arc_class:
            arc.manual_control_point = orig['manual_control_point']
        else:
            arc.is_curved = orig['is_curved']
            arc.control_offset_x = orig['control_offset_x']
            arc.control_offset_y = orig['control_offset_y']
        
        # Reset handler state
        self.reset()
    
    def get_preview_geometry(self) -> Optional[Dict[str, Any]]:
        """Get current geometry for preview rendering.
        
        Returns current arc curve state and control point position.
        
        Returns:
            Dictionary with geometry information, or None
        """
        if not self.is_active or not self.arc_being_transformed:
            return None
        
        arc = self.arc_being_transformed
        
        return {
            'type': 'arc',
            'is_curved': arc.is_curved,
            'control_offset_x': arc.control_offset_x if hasattr(arc, 'control_offset_x') else 0.0,
            'control_offset_y': arc.control_offset_y if hasattr(arc, 'control_offset_y') else 0.0,
        }
    
    def reset(self):
        """Reset all handler state."""
        super().reset()
        self.arc_being_transformed = None
        self.handle_position = None
        self.is_dragging = False
