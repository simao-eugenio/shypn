"""
Handle detection and positioning for transformation operations.

This module provides utilities for:
- Calculating handle positions for different object types
- Detecting which handle (if any) is under the cursor
- Providing appropriate cursor types for different handles
"""

import math
from typing import Optional, Dict, Tuple


class HandleDetector:
    """Detects handle clicks and provides handle positions.
    
    This class handles the geometric calculations for placing transform
    handles around selected objects and detecting when the user clicks
    on a handle.
    
    Attributes:
        HANDLE_SIZE: Size of handle hit area in screen pixels
        HANDLE_NAMES: List of handle identifiers (n, ne, e, se, s, sw, w, nw)
    """
    
    # Handle size in screen pixels (for hit detection)
    HANDLE_SIZE = 8.0
    
    # Handle names in clockwise order starting from north
    HANDLE_NAMES = ['n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw']
    
    def __init__(self):
        """Initialize the handle detector."""
        self.handle_positions_cache = {}  # Cache for performance
    
    def get_handle_positions(self, obj, zoom: float) -> Dict[str, Tuple[float, float]]:
        """Calculate handle positions for an object in screen coordinates.
        
        Args:
            obj: The object (Place, Transition, Arc, etc.)
            zoom: Current zoom level
            
        Returns:
            Dictionary mapping handle name to (screen_x, screen_y) tuple
        """
        from shypn.netobjs import Place, Transition, Arc
        
        if isinstance(obj, Place):
            return self._get_place_handle_positions(obj, zoom)
        elif isinstance(obj, Transition):
            return self._get_transition_handle_positions(obj, zoom)
        elif isinstance(obj, Arc):
            return self._get_arc_handle_positions(obj, zoom)
        else:
            # Other object types don't have transform handles yet
            return {}
    
    def _get_place_handle_positions(self, place, zoom: float) -> Dict[str, Tuple[float, float]]:
        """Calculate handle positions for a Place (circular).
        
        For places, handles are positioned at 8 compass points around
        the circle at radius distance from center.
        
        Args:
            place: The Place object
            zoom: Current zoom level
            
        Returns:
            Dictionary of handle positions in screen coordinates
        """
        cx, cy = place.x, place.y
        radius = place.radius
        
        positions = {}
        
        # Calculate positions at 8 compass points (every 45 degrees)
        angles = {
            'n': 270,    # North (top)
            'ne': 315,   # Northeast
            'e': 0,      # East (right)
            'se': 45,    # Southeast
            's': 90,     # South (bottom)
            'sw': 135,   # Southwest
            'w': 180,    # West (left)
            'nw': 225,   # Northwest
        }
        
        for handle_name, angle_deg in angles.items():
            angle_rad = math.radians(angle_deg)
            handle_x = cx + radius * math.cos(angle_rad)
            handle_y = cy + radius * math.sin(angle_rad)
            positions[handle_name] = (handle_x, handle_y)
        
        return positions
    
    def _get_transition_handle_positions(self, transition, zoom: float) -> Dict[str, Tuple[float, float]]:
        """Calculate handle positions for a Transition (rectangular).
        
        For transitions, handles are positioned at:
        - 4 corners (ne, se, sw, nw)
        - 4 edge midpoints (n, e, s, w)
        
        Args:
            transition: The Transition object
            zoom: Current zoom level
            
        Returns:
            Dictionary of handle positions in screen coordinates
        """
        cx, cy = transition.x, transition.y
        
        # Get transition dimensions based on orientation
        if transition.horizontal:
            half_w = transition.width / 2
            half_h = transition.height / 2
        else:
            # For vertical transitions, swap width and height
            half_w = transition.height / 2
            half_h = transition.width / 2
        
        # Calculate corner and edge midpoint positions
        positions = {
            'n': (cx, cy - half_h),           # Top center
            'ne': (cx + half_w, cy - half_h), # Top right
            'e': (cx + half_w, cy),           # Right center
            'se': (cx + half_w, cy + half_h), # Bottom right
            's': (cx, cy + half_h),           # Bottom center
            'sw': (cx - half_w, cy + half_h), # Bottom left
            'w': (cx - half_w, cy),           # Left center
            'nw': (cx - half_w, cy - half_h), # Top left
        }
        
        return positions
    
    def _get_arc_handle_positions(self, arc, zoom: float) -> dict:
        """Get handle positions for an Arc.
        
        Arcs have a single handle at the midpoint (or control point if curved).
        For CurvedArc instances, the handle is positioned at the actual curve control point,
        accounting for parallel arc detection and offset.
        
        Args:
            arc: The Arc object
            zoom: Current zoom level
            
        Returns:
            Dictionary with 'midpoint' key mapping to (x, y) position
        """
        from shypn.netobjs.curved_arc import CurvedArc
        
        # Get source and target positions
        src_x, src_y = arc.source.x, arc.source.y
        tgt_x, tgt_y = arc.target.x, arc.target.y
        
        # Calculate midpoint
        mid_x = (src_x + tgt_x) / 2
        mid_y = (src_y + tgt_y) / 2
        
        # Check if this is a CurvedArc instance (legacy curved arc class)
        if isinstance(arc, CurvedArc):
            # Check if manual control point is set (from user transformation)
            if hasattr(arc, 'manual_control_point') and arc.manual_control_point is not None:
                # Use manual control point directly
                handle_x, handle_y = arc.manual_control_point
            else:
                # Use CurvedArc's own control point calculation
                # This accounts for parallel arc detection and offset
                offset_distance = None
                if hasattr(arc, '_manager') and arc._manager:
                    try:
                        parallels = arc._manager.detect_parallel_arcs(arc)
                        if parallels:
                            offset_distance = arc._manager.calculate_arc_offset(arc, parallels)
                    except (AttributeError, Exception):
                        # If manager methods fail, use default calculation
                        pass
                
                control_point = arc._calculate_curve_control_point(offset=offset_distance)
                if control_point:
                    handle_x, handle_y = control_point
                else:
                    # Degenerate case: fallback to midpoint
                    handle_x = mid_x
                    handle_y = mid_y
        # Check if arc uses the is_curved flag (new curve system)
        elif getattr(arc, 'is_curved', False):
            control_offset_x = getattr(arc, 'control_offset_x', 0.0)
            control_offset_y = getattr(arc, 'control_offset_y', 0.0)
            handle_x = mid_x + control_offset_x
            handle_y = mid_y + control_offset_y
        else:
            # Straight arc: handle at midpoint, but offset perpendicular for visibility
            dx = tgt_x - src_x
            dy = tgt_y - src_y
            length = math.sqrt(dx * dx + dy * dy)
            
            if length > 1:
                # Perpendicular offset (small, just for visibility)
                perp_x = -dy / length
                perp_y = dx / length
                offset = 15.0  # Small offset in world units
                handle_x = mid_x + perp_x * offset
                handle_y = mid_y + perp_y * offset
            else:
                handle_x = mid_x
                handle_y = mid_y
        
        return {'midpoint': (handle_x, handle_y)}
    
    def detect_handle_at_position(self, obj, screen_x: float, screen_y: float,
                                   zoom: float) -> Optional[str]:
        """Detect which handle (if any) is at the given screen position.
        
        This performs hit testing against all handles for the object.
        
        Args:
            obj: The object to check handles for
            screen_x: X coordinate in screen space
            screen_y: Y coordinate in screen space
            zoom: Current zoom level
            
        Returns:
            Handle name ('n', 'ne', etc.) if a handle is at this position,
            None otherwise
        """
        handle_positions = self.get_handle_positions(obj, zoom)
        
        # Calculate hit threshold in screen pixels
        hit_threshold = self.HANDLE_SIZE / 2.0
        
        # Check each handle for proximity to click position
        for handle_name, (hx, hy) in handle_positions.items():
            # Calculate distance in screen space
            dx = screen_x - hx
            dy = screen_y - hy
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance <= hit_threshold:
                return handle_name
        
        return None
    
    def get_cursor_for_handle(self, handle: str) -> str:
        """Get appropriate cursor name for a handle.
        
        This returns the GTK cursor name that should be displayed when
        hovering over or dragging a specific handle.
        
        Args:
            handle: Handle identifier ('n', 'ne', etc.)
            
        Returns:
            GTK cursor name (e.g., 'n-resize', 'ne-resize', etc.)
        """
        cursor_map = {
            'n': 'n-resize',      # North: vertical resize
            'ne': 'ne-resize',    # Northeast: diagonal resize
            'e': 'e-resize',      # East: horizontal resize
            'se': 'se-resize',    # Southeast: diagonal resize
            's': 's-resize',      # South: vertical resize
            'sw': 'sw-resize',    # Southwest: diagonal resize
            'w': 'w-resize',      # West: horizontal resize
            'nw': 'nw-resize',    # Northwest: diagonal resize
        }
        return cursor_map.get(handle, 'default')
    
    def is_corner_handle(self, handle: str) -> bool:
        """Check if a handle is a corner handle.
        
        Args:
            handle: Handle identifier
            
        Returns:
            True if handle is a corner (ne, se, sw, nw)
        """
        return handle in ['ne', 'se', 'sw', 'nw']
    
    def is_edge_handle(self, handle: str) -> bool:
        """Check if a handle is an edge (midpoint) handle.
        
        Args:
            handle: Handle identifier
            
        Returns:
            True if handle is an edge midpoint (n, e, s, w)
        """
        return handle in ['n', 'e', 's', 'w']
    
    def get_opposite_handle(self, handle: str) -> Optional[str]:
        """Get the handle opposite to the given handle.
        
        This is useful for center-based resize operations (holding Ctrl).
        
        Args:
            handle: Handle identifier
            
        Returns:
            Opposite handle name, or None if not found
        """
        opposite_map = {
            'n': 's',
            'ne': 'sw',
            'e': 'w',
            'se': 'nw',
            's': 'n',
            'sw': 'ne',
            'w': 'e',
            'nw': 'se',
        }
        return opposite_map.get(handle)
    
    def clear_cache(self):
        """Clear the handle positions cache.
        
        Should be called when objects are moved or resized.
        """
        self.handle_positions_cache.clear()
