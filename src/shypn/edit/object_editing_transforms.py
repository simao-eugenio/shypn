"""Object Editing and Transform System.

Unified class for rendering selection feedback, bounding boxes,
and transform handles for selected objects.
"""
import math
from typing import Optional


class ObjectEditingTransforms:
    """Manages visual feedback and transformation for selected objects."""
    
    # Visual constants (all in screen pixels, compensated for zoom)
    SELECTION_COLOR = (0.2, 0.6, 1.0, 0.5)  # Blue highlight with alpha
    SELECTION_LINE_WIDTH = 3.0  # Pixels (compensated for zoom)
    SELECTION_OFFSET = 3.0  # Pixels offset from object edge
    
    BBOX_COLOR = (0.2, 0.6, 1.0, 0.8)  # Darker blue for bounding box
    BBOX_LINE_WIDTH = 1.5  # Pixels
    BBOX_DASH = [5, 3]  # Dash pattern (5px line, 3px gap)
    
    HANDLE_SIZE = 8.0  # Pixels (square handles)
    HANDLE_FILL = (1.0, 1.0, 1.0, 1.0)  # White fill
    HANDLE_STROKE = (0.2, 0.6, 1.0, 1.0)  # Blue stroke
    HANDLE_LINE_WIDTH = 1.5  # Pixels
    
    def __init__(self, selection_manager):
        """Initialize transform system.
        
        Args:
            selection_manager: SelectionManager instance to track selection
        """
        self.selection_manager = selection_manager
        self.active_handle = None  # 'move', 'n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw'
    
    def render_selection_layer(self, cr, manager, zoom: float):
        """Render all selection feedback.
        
        Should be called in world space (inside Cairo transform).
        
        Rendering depends on selection mode:
        - NORMAL mode: Only blue highlights (for arc creation, drag prep, etc.)
        - EDIT mode: Blue highlights + bounding box + transform handles
        
        Args:
            cr: Cairo context
            manager: Canvas manager
            zoom: Current zoom level (for compensation)
        """
        selected = self.selection_manager.get_selected_objects(manager)
        
        if not selected:
            return
        
        # Render individual object selection highlights (always show)
        for obj in selected:
            self._render_object_selection(cr, obj, zoom)
        
        # EDIT MODE: Show bounding box and transform handles
        if self.selection_manager.is_edit_mode():
            # Render bounding box (for any selection in EDIT mode)
            # Always show bounding box in EDIT mode to provide visual context
            self._render_bounding_box(cr, manager, zoom)
            
            # Render transform handles (only in edit mode)
            if len(selected) >= 1:
                self._render_transform_handles(cr, manager, zoom)
        # NORMAL MODE: No handles, just basic highlights
    
    def _render_object_selection(self, cr, obj, zoom: float):
        """Render selection highlight for individual object.
        
        Args:
            cr: Cairo context (world space)
            obj: Object to render selection for
            zoom: Current zoom level
        """
        from shypn.api import Place, Transition, Arc
        
        offset = self.SELECTION_OFFSET / zoom
        
        if isinstance(obj, Place):
            # Circle outline
            cr.arc(obj.x, obj.y, obj.radius + offset, 0, 2 * math.pi)
            cr.set_source_rgba(*self.SELECTION_COLOR)
            cr.set_line_width(self.SELECTION_LINE_WIDTH / zoom)
            cr.stroke()
        
        elif isinstance(obj, Transition):
            # Rectangle outline
            w = obj.width if obj.horizontal else obj.height
            h = obj.height if obj.horizontal else obj.width
            half_w = w / 2
            half_h = h / 2
            
            cr.rectangle(
                obj.x - half_w - offset,
                obj.y - half_h - offset,
                w + 2 * offset,
                h + 2 * offset
            )
            cr.set_source_rgba(*self.SELECTION_COLOR)
            cr.set_line_width(self.SELECTION_LINE_WIDTH / zoom)
            cr.stroke()
        
        elif isinstance(obj, Arc):
            # Arc selection: draw thicker line along arc path
            src_x, src_y = obj.source.x, obj.source.y
            tgt_x, tgt_y = obj.target.x, obj.target.y
            
            # Calculate direction
            dx = tgt_x - src_x
            dy = tgt_y - src_y
            length = math.sqrt(dx * dx + dy * dy)
            
            if length < 1:
                return  # Too short to render
            
            # Normalize direction
            dx /= length
            dy /= length
            
            # Get boundary points (same calculation as arc rendering)
            start_x, start_y = obj._get_boundary_point(obj.source, src_x, src_y, dx, dy)
            end_x, end_y = obj._get_boundary_point(obj.target, tgt_x, tgt_y, -dx, -dy)
            
            # Draw selection line (thicker and colored)
            cr.move_to(start_x, start_y)
            cr.line_to(end_x, end_y)
            cr.set_source_rgba(*self.SELECTION_COLOR)
            cr.set_line_width((self.SELECTION_LINE_WIDTH + 4.0) / zoom)  # Extra thick for visibility
            cr.stroke()
    
    def _render_bounding_box(self, cr, manager, zoom: float):
        """Render dashed bounding box around all selected objects.
        
        Args:
            cr: Cairo context (world space)
            manager: Canvas manager
            zoom: Current zoom level
        """
        bounds = self.selection_manager.get_selection_bounds(manager)
        if not bounds:
            return
        
        min_x, min_y, max_x, max_y = bounds
        
        # Add padding
        padding = 10.0 / zoom
        min_x -= padding
        min_y -= padding
        max_x += padding
        max_y += padding
        
        # Draw dashed rectangle
        cr.rectangle(min_x, min_y, max_x - min_x, max_y - min_y)
        cr.set_source_rgba(*self.BBOX_COLOR)
        cr.set_line_width(self.BBOX_LINE_WIDTH / zoom)
        
        # Set dash pattern (compensated for zoom)
        dash_pattern = [d / zoom for d in self.BBOX_DASH]
        cr.set_dash(dash_pattern)
        cr.stroke()
        cr.set_dash([])  # Reset dash pattern
    
    def _render_transform_handles(self, cr, manager, zoom: float):
        """Render resize/rotate handles on bounding box corners and edges.
        
        Args:
            cr: Cairo context (world space)
            manager: Canvas manager
            zoom: Current zoom level
        """
        bounds = self.selection_manager.get_selection_bounds(manager)
        if not bounds:
            return
        
        min_x, min_y, max_x, max_y = bounds
        
        # Add padding (same as bounding box)
        padding = 10.0 / zoom
        min_x -= padding
        min_y -= padding
        max_x += padding
        max_y += padding
        
        # Calculate handle positions
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        handle_size = self.HANDLE_SIZE / zoom
        half_size = handle_size / 2
        
        # 8 handles: corners and midpoints
        handles = {
            'nw': (min_x, min_y),     # Top-left
            'n':  (center_x, min_y),  # Top-center
            'ne': (max_x, min_y),     # Top-right
            'e':  (max_x, center_y),  # Right-center
            'se': (max_x, max_y),     # Bottom-right
            's':  (center_x, max_y),  # Bottom-center
            'sw': (min_x, max_y),     # Bottom-left
            'w':  (min_x, center_y),  # Left-center
        }
        
        # Render each handle
        for position, (hx, hy) in handles.items():
            # Draw filled rectangle for handle
            cr.rectangle(hx - half_size, hy - half_size, handle_size, handle_size)
            cr.set_source_rgba(*self.HANDLE_FILL)
            cr.fill_preserve()
            
            # Draw handle border
            cr.set_source_rgba(*self.HANDLE_STROKE)
            cr.set_line_width(self.HANDLE_LINE_WIDTH / zoom)
            cr.stroke()
    
    def hit_test_handle(self, x: float, y: float, manager, zoom: float) -> Optional[str]:
        """Test if a point hits a transform handle.
        
        Args:
            x, y: Point in world coordinates
            manager: Canvas manager
            zoom: Current zoom level
            
        Returns:
            Handle name ('nw', 'n', 'ne', etc.) or None
        """
        bounds = self.selection_manager.get_selection_bounds(manager)
        if not bounds:
            return None
        
        min_x, min_y, max_x, max_y = bounds
        padding = 10.0 / zoom
        min_x -= padding
        min_y -= padding
        max_x += padding
        max_y += padding
        
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        handle_size = self.HANDLE_SIZE / zoom
        half_size = handle_size / 2
        
        handles = {
            'nw': (min_x, min_y),
            'n':  (center_x, min_y),
            'ne': (max_x, min_y),
            'e':  (max_x, center_y),
            'se': (max_x, max_y),
            's':  (center_x, max_y),
            'sw': (min_x, max_y),
            'w':  (min_x, center_y),
        }
        
        # Check each handle
        for name, (hx, hy) in handles.items():
            if (hx - half_size <= x <= hx + half_size and
                hy - half_size <= y <= hy + half_size):
                return name
        
        return None
