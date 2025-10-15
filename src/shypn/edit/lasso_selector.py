#!/usr/bin/env python3
"""Lasso Selector - Freeform selection using lasso polygon."""

import math


class LassoSelector:
    """Implements lasso (freeform polygon) selection.
    
    User clicks and drags to draw a freeform path. When released,
    all objects inside the polygon are selected.
    
    This class is separate from EditOperations to follow SRP
    (Single Responsibility Principle).
    """
    
    def __init__(self, canvas_manager):
        """Initialize lasso selector.
        
        Args:
            canvas_manager: ModelCanvasManager instance
        """
        self.canvas_manager = canvas_manager
        self.points = []  # List of (x, y) points in lasso path
        self.is_active = False
    
    def start_lasso(self, x, y):
        """Start drawing lasso at position.
        
        Args:
            x, y: Starting position (world coordinates)
        """
        self.is_active = True
        self.points = [(x, y)]
    
    def add_point(self, x, y):
        """Add point to lasso path.
        
        Args:
            x, y: Point position (world coordinates)
        """
        if not self.is_active:
            return
        
        # Only add if sufficiently far from last point (avoid clutter)
        if self.points:
            last_x, last_y = self.points[-1]
            dist = math.sqrt((x - last_x)**2 + (y - last_y)**2)
            if dist < 5.0:  # Minimum 5 pixels distance
                return
        
        self.points.append((x, y))
    
    def finish_lasso(self, multi=False):
        """Finish lasso and select objects inside.
        
        Args:
            multi: If True, add to existing selection (Ctrl+Lasso).
                   If False, replace selection (clear first).
        """
        if not self.is_active or len(self.points) < 3:
            self.cancel_lasso()
            return
        
        # Close the polygon
        if self.points[0] != self.points[-1]:
            self.points.append(self.points[0])
        
        # Find objects inside polygon
        selected = []
        for obj in self.canvas_manager.get_all_objects():
            if self._is_point_in_polygon(obj.x, obj.y, self.points):
                selected.append(obj)
        
        # Update selection
        if not multi:
            # Single-select mode: clear existing selection first
            self.canvas_manager.selection_manager.clear_selection()
            self.canvas_manager.clear_all_selections()
        
        # Add selected objects (either to empty selection or to existing)
        for obj in selected:
            self.canvas_manager.selection_manager.select(
                obj, 
                multi=True,  # Always use multi=True since we already cleared if needed
                manager=self.canvas_manager
            )
        
        
        # Reset
        self.is_active = False
        self.points = []
    
    def cancel_lasso(self):
        """Cancel lasso selection."""
        self.is_active = False
        self.points = []
    
    def render_lasso(self, cr, zoom=1.0):
        """Render lasso path on canvas.
        
        Args:
            cr: Cairo context
            zoom: Current zoom level
        """
        if not self.is_active or len(self.points) < 2:
            return
        
        cr.save()
        
        # Draw lasso path
        cr.set_source_rgba(0.2, 0.6, 1.0, 0.5)  # Blue semi-transparent
        cr.set_line_width(2.0 / zoom)  # Compensate for zoom
        cr.set_dash([5.0 / zoom, 5.0 / zoom])  # Dashed line
        
        # Draw path
        cr.move_to(self.points[0][0], self.points[0][1])
        for x, y in self.points[1:]:
            cr.line_to(x, y)
        
        # Close path visually
        if len(self.points) >= 3:
            cr.line_to(self.points[0][0], self.points[0][1])
        
        cr.stroke()
        
        # Draw points for visual feedback
        cr.set_source_rgba(0.2, 0.6, 1.0, 0.8)
        for x, y in self.points:
            cr.arc(x, y, 3.0 / zoom, 0, 2 * math.pi)
            cr.fill()
        
        cr.restore()
    
    def _is_point_in_polygon(self, x, y, polygon):
        """Check if point is inside polygon using ray casting algorithm.
        
        Args:
            x, y: Point coordinates
            polygon: List of (x, y) tuples defining polygon
            
        Returns:
            bool: True if point is inside polygon
        """
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
