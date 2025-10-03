#!/usr/bin/env python3
"""TransientArc - Temporary preview arc for visual feedback during editing.

TransientArc is used to show a preview line when the user is creating an arc
interactively. It is NOT a PetriNetObject and is never added to the model.

Learned from legacy implementation:
- legacy/shypnpy/interface/arc_preview.py: Draw orange preview line with arrowhead
- legacy/shypnpy/interface/interactions.py: Store source element during arc tool use
- legacy/shypnpy/validate_ui.py: Fallback preview rendering

Usage pattern:
1. User activates arc tool and clicks source element (Place or Transition)
2. TransientArc is created from source to current cursor position
3. TransientArc is rendered on each motion event to follow cursor
4. When user clicks target, real Arc is created and TransientArc is discarded
5. If user cancels (ESC, right-click), TransientArc is simply discarded

TransientArc does NOT:
- Validate bipartite connections (happens when creating real Arc)
- Get added to model collections
- Have immutable id/name (not a PetriNetObject)
- Persist to disk
"""
import math
from typing import Tuple, Optional


class TransientArc:
    """Temporary preview arc for visual feedback during interactive arc creation.
    
    This is NOT a PetriNetObject - it's a lightweight visual guide that exists
    only during the arc creation interaction. It is never added to the model.
    
    The arc follows the cursor from the source element boundary to the current
    cursor position, providing visual feedback to the user about where the arc
    will connect.
    """
    
    # Visual styling (distinct from real arcs to show it's a preview)
    PREVIEW_COLOR = (0.95, 0.5, 0.1)  # Orange (from legacy arc_preview.py)
    PREVIEW_ALPHA = 0.85
    PREVIEW_WIDTH = 2.0
    ARROWHEAD_LENGTH = 11.0
    ARROWHEAD_WIDTH = 6.0
    
    def __init__(self, source, target_x: float, target_y: float):
        """Initialize a transient preview arc.
        
        Args:
            source: Source object (Place or Transition) - must have x, y attributes
            target_x: Current cursor X position in world coordinates
            target_y: Current cursor Y position in world coordinates
        
        Note:
            Unlike Arc, this does NOT validate bipartite connections.
            It's just a visual guide, validation happens when creating the real Arc.
        """
        self.source = source
        self.target_x = target_x
        self.target_y = target_y
    
    def update_target(self, target_x: float, target_y: float):
        """Update the target position (follows cursor movement).
        
        Args:
            target_x: New cursor X position in world coordinates
            target_y: New cursor Y position in world coordinates
        """
        self.target_x = target_x
        self.target_y = target_y
    
    def render(self, cr, transform=None):
        """Render the transient arc preview using Cairo.
        
        Draws an orange line from the source element boundary to the current
        cursor position, with an arrowhead at the cursor.
        
        Args:
            cr: Cairo context
            transform: Optional function to transform world coords to screen coords
        """
        # Get source position in world space
        src_x = self.source.x
        src_y = self.source.y
        
        # Calculate direction vector
        dx = self.target_x - src_x
        dy = self.target_y - src_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance < 1:
            return  # Too short to draw
        
        # Normalize direction
        ux = dx / distance
        uy = dy / distance
        
        # Get source boundary point (approximate)
        # Determine radius based on source object type
        if hasattr(self.source, 'radius'):
            # It's a Place (circular)
            radius = float(self.source.radius)
        else:
            # It's a Transition (rectangular) - approximate as circle
            width = float(getattr(self.source, 'width', 40.0))
            height = float(getattr(self.source, 'height', 20.0))
            radius = max(width, height) / 2.0
        
        # Start point at boundary (world space)
        start_x = src_x + ux * radius
        start_y = src_y + uy * radius
        
        # End point is cursor position (world space)
        end_x = self.target_x
        end_y = self.target_y
        
        # Transform to screen space if transform provided
        if transform:
            screen_start_x, screen_start_y = transform(start_x, start_y)
            screen_end_x, screen_end_y = transform(end_x, end_y)
        else:
            screen_start_x, screen_start_y = start_x, start_y
            screen_end_x, screen_end_y = end_x, end_y
        
        # Draw the preview line
        cr.save()
        cr.set_source_rgba(*self.PREVIEW_COLOR, self.PREVIEW_ALPHA)
        cr.set_line_width(self.PREVIEW_WIDTH)
        cr.move_to(screen_start_x, screen_start_y)
        cr.line_to(screen_end_x, screen_end_y)
        cr.stroke()
        
        # Draw arrowhead at cursor position
        self._draw_arrowhead(cr, screen_start_x, screen_start_y, 
                           screen_end_x, screen_end_y, ux, uy)
        
        cr.restore()
    
    def _draw_arrowhead(self, cr, sx: float, sy: float, ex: float, ey: float,
                       ux: float, uy: float):
        """Draw arrowhead at the end point.
        
        Args:
            cr: Cairo context (already in screen space)
            sx: Start X in screen space
            sy: Start Y in screen space
            ex: End X in screen space (cursor position)
            ey: End Y in screen space (cursor position)
            ux: Normalized direction X (unit vector)
            uy: Normalized direction Y (unit vector)
        """
        # Calculate arrowhead points
        # Left wing
        left_x = ex - self.ARROWHEAD_LENGTH * ux + self.ARROWHEAD_WIDTH * (-uy)
        left_y = ey - self.ARROWHEAD_LENGTH * uy + self.ARROWHEAD_WIDTH * ux
        
        # Right wing
        right_x = ex - self.ARROWHEAD_LENGTH * ux - self.ARROWHEAD_WIDTH * (-uy)
        right_y = ey - self.ARROWHEAD_LENGTH * uy - self.ARROWHEAD_WIDTH * ux
        
        # Draw filled triangle
        cr.move_to(ex, ey)
        cr.line_to(left_x, left_y)
        cr.line_to(right_x, right_y)
        cr.close_path()
        cr.fill()
    
    def __repr__(self):
        """String representation for debugging."""
        return (f"TransientArc(source={getattr(self.source, 'name', '?')}, "
                f"target=({self.target_x:.1f}, {self.target_y:.1f}))")


class TransientArcManager:
    """Helper class to manage transient arc state during editing.
    
    This simplifies the interaction pattern:
    - Call start_arc(source) when user clicks source element
    - Call update_cursor(x, y) on mouse motion to update preview
    - Call finish_arc() when user clicks target (returns source for arc creation)
    - Call cancel_arc() to discard preview
    
    Usage in canvas interaction code:
    ```python
    # In canvas manager or interaction handler
    self.transient_manager = TransientArcManager()
    
    # On mouse click with arc tool:
    if hit_element:
        self.transient_manager.start_arc(hit_element)
    
    # On mouse motion:
    if self.transient_manager.has_active_arc():
        world_x, world_y = screen_to_world(event.x, event.y)
        self.transient_manager.update_cursor(world_x, world_y)
        self.canvas.queue_draw()  # Trigger redraw
    
    # In canvas draw handler:
    transient = self.transient_manager.get_active_arc()
    if transient:
        transient.render(cr, transform)
    
    # On mouse click (potential target):
    if self.transient_manager.has_active_arc():
        source = self.transient_manager.get_source()
        # Attempt to create real arc
        try:
            arc = Arc(source=source, target=target, ...)
            model.add_arc(arc)
            self.transient_manager.finish_arc()
        except ValueError as e:
            # Invalid connection (e.g., Place->Place)
            show_error(str(e))
            self.transient_manager.cancel_arc()
    ```
    """
    
    def __init__(self):
        """Initialize the transient arc manager."""
        self.active_arc: Optional[TransientArc] = None
        self.source_element = None
    
    def start_arc(self, source, cursor_x: float = None, cursor_y: float = None):
        """Start arc creation from a source element.
        
        Args:
            source: Source element (Place or Transition)
            cursor_x: Initial cursor X position (optional, defaults to source position)
            cursor_y: Initial cursor Y position (optional, defaults to source position)
        """
        if cursor_x is None:
            cursor_x = source.x
        if cursor_y is None:
            cursor_y = source.y
        
        self.source_element = source
        self.active_arc = TransientArc(source, cursor_x, cursor_y)
    
    def update_cursor(self, cursor_x: float, cursor_y: float):
        """Update cursor position (updates preview arc target).
        
        Args:
            cursor_x: Current cursor X in world coordinates
            cursor_y: Current cursor Y in world coordinates
        """
        if self.active_arc:
            self.active_arc.update_target(cursor_x, cursor_y)
    
    def has_active_arc(self) -> bool:
        """Check if there's an active arc preview."""
        return self.active_arc is not None
    
    def get_active_arc(self) -> Optional[TransientArc]:
        """Get the active transient arc (for rendering)."""
        return self.active_arc
    
    def get_source(self):
        """Get the source element of the active arc."""
        return self.source_element
    
    def finish_arc(self):
        """Finish arc creation (called after real arc is created)."""
        self.active_arc = None
        self.source_element = None
    
    def cancel_arc(self):
        """Cancel arc creation (discard preview)."""
        self.active_arc = None
        self.source_element = None
    
    def __repr__(self):
        """String representation for debugging."""
        if self.has_active_arc():
            return f"TransientArcManager(active={self.active_arc})"
        return "TransientArcManager(inactive)"
