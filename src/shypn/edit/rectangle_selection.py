"""Rectangle/Lasso Selection for Canvas.

Provides rubber-band rectangle selection when dragging with Select tool active.
"""
from typing import Optional, Tuple


class RectangleSelection:
    """Manages rectangle selection (rubber-band) state and rendering."""
    
    # Visual constants
    RECT_STROKE = (0.2, 0.6, 1.0, 0.8)  # Blue stroke
    RECT_FILL = (0.2, 0.6, 1.0, 0.1)    # Very light blue fill
    RECT_LINE_WIDTH = 1.5  # Pixels (device space)
    RECT_DASH = [4, 2]  # Dash pattern (4px line, 2px gap)
    
    def __init__(self):
        """Initialize rectangle selection state."""
        self.active = False  # Is selection active
        self.start_x = 0.0  # Start X in world coordinates
        self.start_y = 0.0  # Start Y in world coordinates
        self.current_x = 0.0  # Current X in world coordinates
        self.current_y = 0.0  # Current Y in world coordinates
    
    def start(self, world_x: float, world_y: float):
        """Start rectangle selection.
        
        Args:
            world_x: Starting X coordinate in world space
            world_y: Starting Y coordinate in world space
        """
        self.active = True
        self.start_x = world_x
        self.start_y = world_y
        self.current_x = world_x
        self.current_y = world_y
    
    def update(self, world_x: float, world_y: float):
        """Update rectangle selection current position.
        
        Args:
            world_x: Current X coordinate in world space
            world_y: Current Y coordinate in world space
        """
        if self.active:
            self.current_x = world_x
            self.current_y = world_y
    
    def finish(self) -> Optional[Tuple[float, float, float, float]]:
        """Finish rectangle selection and return bounds.
        
        Returns:
            (min_x, min_y, max_x, max_y) in world coordinates, or None if no selection
        """
        if not self.active:
            return None
        
        self.active = False
        
        # Calculate bounds (normalized)
        min_x = min(self.start_x, self.current_x)
        min_y = min(self.start_y, self.current_y)
        max_x = max(self.start_x, self.current_x)
        max_y = max(self.start_y, self.current_y)
        
        # Only return bounds if rectangle has meaningful size (> 5 pixels in any dimension)
        # This prevents accidental selections from tiny drags
        if abs(max_x - min_x) < 0.1 and abs(max_y - min_y) < 0.1:
            return None
        
        return (min_x, min_y, max_x, max_y)
    
    def cancel(self):
        """Cancel rectangle selection."""
        self.active = False
    
    def get_bounds(self) -> Optional[Tuple[float, float, float, float]]:
        """Get current selection bounds without finishing.
        
        Returns:
            (min_x, min_y, max_x, max_y) in world coordinates, or None if not active
        """
        if not self.active:
            return None
        
        min_x = min(self.start_x, self.current_x)
        min_y = min(self.start_y, self.current_y)
        max_x = max(self.start_x, self.current_x)
        max_y = max(self.start_y, self.current_y)
        
        return (min_x, min_y, max_x, max_y)
    
    def render(self, cr, zoom: float):
        """Render selection rectangle.
        
        Should be called in world space (inside Cairo transform).
        
        Args:
            cr: Cairo context (world space)
            zoom: Current zoom level (for device-space line width)
        """
        if not self.active:
            return
        
        bounds = self.get_bounds()
        if not bounds:
            return
        
        min_x, min_y, max_x, max_y = bounds
        width = max_x - min_x
        height = max_y - min_y
        
        # Draw filled rectangle
        cr.rectangle(min_x, min_y, width, height)
        cr.set_source_rgba(*self.RECT_FILL)
        cr.fill_preserve()
        
        # Draw dashed border
        cr.set_source_rgba(*self.RECT_STROKE)
        cr.set_line_width(self.RECT_LINE_WIDTH / zoom)
        
        # Set dash pattern (compensated for zoom)
        dash_pattern = [d / zoom for d in self.RECT_DASH]
        cr.set_dash(dash_pattern)
        cr.stroke()
        cr.set_dash([])  # Reset dash pattern
    
    def select_objects(self, manager, multi: bool = False):
        """Select all objects within rectangle bounds.
        
        Args:
            manager: Canvas manager with objects to select
            multi: If True, add to selection. If False, replace selection.
        
        Returns:
            int: Number of objects selected
        """
        from shypn.netobjs import Place, Transition
        
        bounds = self.get_bounds()
        if not bounds:
            return 0
        
        min_x, min_y, max_x, max_y = bounds
        
        # Clear existing selection if not multi-select
        if not multi:
            manager.clear_all_selections()
        
        selected_count = 0
        
        # Check places and transitions (not arcs - they don't have x,y center)
        for place in manager.places:
            if min_x <= place.x <= max_x and min_y <= place.y <= max_y:
                manager.selection_manager.select(place, multi=True, manager=manager)
                selected_count += 1
        
        for transition in manager.transitions:
            if min_x <= transition.x <= max_x and min_y <= transition.y <= max_y:
                manager.selection_manager.select(transition, multi=True, manager=manager)
                selected_count += 1
        
        return selected_count
