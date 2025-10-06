#!/usr/bin/env python3
"""Model Canvas Manager.

This module manages the canvas properties, transformations, and behaviors
for the Petri Net model editor. It handles:
- Grid system with adaptive spacing based on zoom level
- Zoom operations (pointer-centered)
- Pan operations (viewport translation)
- Coordinate transformations (screen ↔ world)
- Rendering pipeline for grid and model elements
- Document metadata and state validation
- Petri net object collections (places, transitions, arcs)
- View state persistence (pan, zoom)

The manager maintains the model state separately from GTK widgets,
making it easier to test and maintain.
"""
import math
import json
import os
from datetime import datetime
from shypn.netobjs import Place, Arc, Transition
from shypn.edit import SelectionManager, ObjectEditingTransforms, RectangleSelection


class ModelCanvasManager:
    """Manages canvas properties, transformations, and rendering for Petri Net models."""
    
    # Zoom configuration
    MIN_ZOOM = 0.3   # 30% minimum (practical engineering range)
    MAX_ZOOM = 3.0   # 300% maximum (practical engineering range)
    ZOOM_STEP = 1.1  # Multiplicative zoom factor (10% per step)
    
    # Canvas extent for infinite canvas (half-extent in logical units)
    CANVAS_EXTENT = 10000.0  # ±10,000 units = 20,000×20,000 total canvas
    
    # Grid configuration
    # DPI-aware grid: 1mm physical spacing at all screen resolutions
    BASE_GRID_SPACING = 1.0  # 1mm physical spacing (DPI-aware)
    GRID_SUBDIVISION_LEVELS = [1, 2, 5, 10]  # Grid adapts at these zoom thresholds
    GRID_MAJOR_EVERY = 5  # Every 5th line is a major line (legacy-compatible)
    GRID_STYLE_LINE = 'line'  # Standard grid lines
    GRID_STYLE_DOT = 'dot'    # Dots at intersections
    GRID_STYLE_CROSS = 'cross'  # Small crosses at intersections
    
    def __init__(self, canvas_width=2000, canvas_height=2000, filename="default"):
        """Initialize the canvas manager.
        
        Args:
            canvas_width: Logical canvas width in world coordinates.
            canvas_height: Logical canvas height in world coordinates.
            filename: Base filename without extension (default: "default").
        """
        # Canvas logical size (world coordinates)
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        
        # Document metadata
        self.filename = filename  # Base filename without .shy extension
        self.modified = False  # Document modified flag
        self.created_at = datetime.now()
        self.modified_at = None
        
        # Viewport properties
        self.zoom = 1.0  # Current zoom level (1.0 = 100%)
        # Initialize pan to center the canvas (updated when viewport size is known)
        self.pan_x = 0.0  # Pan offset X (in world coordinates)
        self.pan_y = 0.0  # Pan offset Y (in world coordinates)
        self._initial_pan_set = False  # Flag to center on first draw
        
        # Viewport size (screen coordinates) - updated when widget is allocated
        self.viewport_width = 800
        self.viewport_height = 600
        
        # DPI detection (defaults to 96.0, updated from widget)
        self.screen_dpi = 96.0
        
        # Pointer position (for pointer-centered zoom)
        self.pointer_x = 0
        self.pointer_y = 0
        
        # Grid style
        self.grid_style = self.GRID_STYLE_LINE  # Default to line grid
        
        # Tool selection state
        self.current_tool = None  # Currently selected tool ('place', 'transition', 'arc', or None)
        
        # Petri net object collections
        # Creation order: Places and Transitions can be created in any order,
        # but Arcs must come after (they connect P↔T or T↔P)
        self.places = []  # List of Place instances
        self.transitions = []  # List of Transition instances
        self.arcs = []  # List of Arc instances (created last, after P and T)
        
        # ID counters for object naming
        self._next_place_id = 1
        self._next_transition_id = 1
        self._next_arc_id = 1
        
        # Selection and transformation system
        self.selection_manager = SelectionManager()
        self.editing_transforms = ObjectEditingTransforms(self.selection_manager)
        self.rectangle_selection = RectangleSelection()
        
        # Dirty flag for redraw optimization
        self._needs_redraw = True
        
        # Ensure all arcs have proper manager references
        self.ensure_arc_references()
    
    # ==================== DPI and Physical Units ====================
    
    def set_screen_dpi(self, dpi):
        """Update screen DPI from widget.
        
        Args:
            dpi: Screen resolution in dots per inch.
        """
        self.screen_dpi = dpi if dpi and dpi > 0 else 96.0
    
    def get_mm_to_pixels(self):
        """Convert millimeters to pixels based on screen DPI.
        
        Returns:
            float: Pixels per millimeter.
        """
        return self.screen_dpi / 25.4
    
    # ==================== Coordinate Transformations ====================
    
    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world (model) coordinates.
        
        Legacy formula: world = screen / zoom - pan
        
        Args:
            screen_x: X coordinate in screen space (pixels).
            screen_y: Y coordinate in screen space (pixels).
            
        Returns:
            tuple: (world_x, world_y) in model coordinate space.
        """
        world_x = (screen_x / self.zoom) - self.pan_x
        world_y = (screen_y / self.zoom) - self.pan_y
        return world_x, world_y
    
    def world_to_screen(self, world_x, world_y):
        """Convert world (model) coordinates to screen coordinates.
        
        Legacy formula: screen = (world + pan) * zoom
        
        Args:
            world_x: X coordinate in world space.
            world_y: Y coordinate in world space.
            
        Returns:
            tuple: (screen_x, screen_y) in screen coordinate space (pixels).
        """
        screen_x = (world_x + self.pan_x) * self.zoom
        screen_y = (world_y + self.pan_y) * self.zoom
        return screen_x, screen_y
    
    # ==================== Tool Management ====================
    
    def set_tool(self, tool_name):
        """Set the currently active tool.
        
        Args:
            tool_name: Tool to activate ('place', 'transition', 'arc') or None to clear.
        """
        self.current_tool = tool_name
    
    def get_tool(self):
        """Get the currently active tool.
        
        Returns:
            str or None: Currently active tool name ('place', 'transition', 'arc') or None.
        """
        return self.current_tool
    
    def clear_tool(self):
        """Clear the current tool selection (return to pan mode)."""
        self.current_tool = None
    
    def is_tool_active(self):
        """Check if any tool is currently active.
        
        Returns:
            bool: True if a tool is active, False if in pan mode.
        """
        return self.current_tool is not None
    
    # ==================== Petri Net Object Management ====================
    
    def add_place(self, x, y, **kwargs):
        """Create and add a Place at the specified position.
        
        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            **kwargs: Additional Place parameters (radius, label, etc.)
            
        Returns:
            Place: The newly created place instance
        """
        place_id = self._next_place_id
        place_name = f"P{place_id}"
        self._next_place_id += 1
        
        place = Place(x, y, place_id, place_name, **kwargs)
        place.on_changed = self._on_object_changed
        self.places.append(place)
        
        self.mark_modified()
        self.mark_dirty()
        return place
    
    def add_transition(self, x, y, **kwargs):
        """Create and add a Transition at the specified position.
        
        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            **kwargs: Additional Transition parameters (width, height, label, etc.)
            
        Returns:
            Transition: The newly created transition instance
        """
        transition_id = self._next_transition_id
        transition_name = f"T{transition_id}"
        self._next_transition_id += 1
        
        transition = Transition(x, y, transition_id, transition_name, **kwargs)
        transition.on_changed = self._on_object_changed
        self.transitions.append(transition)
        
        self.mark_modified()
        self.mark_dirty()
        return transition
    
    def add_arc(self, source, target, **kwargs):
        """Create and add an Arc between two objects.
        
        Args:
            source: Source object instance (Place or Transition)
            target: Target object instance (Place or Transition)
            **kwargs: Additional Arc parameters (weight, etc.)
            
        Returns:
            Arc: The newly created arc instance
        """
        arc_id = self._next_arc_id
        arc_name = f"A{arc_id}"
        self._next_arc_id += 1
        
        arc = Arc(source, target, arc_id, arc_name, **kwargs)
        arc.on_changed = self._on_object_changed
        arc._manager = self  # Store reference to manager for parallel detection
        self.arcs.append(arc)
        
        # Check if this arc creates a parallel situation and auto-convert to curved
        self._auto_convert_parallel_arcs_to_curved(arc)
        
        self.mark_modified()
        self.mark_dirty()
        return arc
    
    def remove_place(self, place):
        """Remove a place from the model.
        
        Also removes all arcs connected to this place.
        
        Args:
            place: Place instance to remove
        """
        if place in self.places:
            # Remove connected arcs
            self.arcs = [arc for arc in self.arcs 
                        if arc.source != place and arc.target != place]
            
            self.places.remove(place)
            self.mark_modified()
            self.mark_dirty()
    
    def remove_transition(self, transition):
        """Remove a transition from the model.
        
        Also removes all arcs connected to this transition.
        
        Args:
            transition: Transition instance to remove
        """
        if transition in self.transitions:
            # Remove connected arcs
            self.arcs = [arc for arc in self.arcs 
                        if arc.source != transition and arc.target != transition]
            
            self.transitions.remove(transition)
            self.mark_modified()
            self.mark_dirty()
    
    def remove_arc(self, arc):
        """Remove an arc from the model.
        
        Args:
            arc: Arc instance to remove
        """
        if arc in self.arcs:
            self.arcs.remove(arc)
            self.mark_modified()
            self.mark_dirty()
    
    def detect_parallel_arcs(self, arc):
        """Find arcs parallel to the given arc (same source/target or reversed).
        
        Parallel arcs are arcs that connect the same two nodes, either in the
        same direction or opposite direction. These need visual offset to
        avoid overlapping.
        
        Args:
            arc: Arc to check for parallels
            
        Returns:
            list: List of parallel arcs (excluding the given arc)
        """
        parallels = []
        
        for other in self.arcs:
            if other == arc:
                continue
            
            # Same direction: same source and target
            if (other.source == arc.source and other.target == arc.target):
                parallels.append(other)
                print(f"[ParallelDetect] Found same-direction parallel: {arc.name} and {other.name}")
            
            # Opposite direction: reversed source and target
            elif (other.source == arc.target and other.target == arc.source):
                parallels.append(other)
                print(f"[ParallelDetect] Found opposite-direction parallel: {arc.name} and {other.name}")
        
        if not parallels:
            print(f"[ParallelDetect] No parallels found for {arc.name}")
        
        return parallels
    
    def _auto_convert_parallel_arcs_to_curved(self, new_arc):
        """Automatically convert parallel arcs to curved arcs.
        
        When a new arc creates a parallel situation (same source/target or opposite),
        convert all involved arcs to curved arcs for better visualization.
        
        Args:
            new_arc: The newly added arc that may create parallels
        """
        from shypn.netobjs import CurvedArc, CurvedInhibitorArc, InhibitorArc
        from shypn.utils.arc_transform import make_curved
        
        parallels = self.detect_parallel_arcs(new_arc)
        
        if parallels:
            # Convert the new arc if it's straight
            if isinstance(new_arc, Arc) and not isinstance(new_arc, (CurvedArc, CurvedInhibitorArc)):
                curved_arc = make_curved(new_arc)
                index = self.arcs.index(new_arc)
                self.arcs[index] = curved_arc
                curved_arc._manager = self
                curved_arc.on_changed = self._on_object_changed
                # Update the reference in the arcs list to return the new curved arc
                new_arc = curved_arc
            
            # Convert all parallel arcs if they're straight
            for i, parallel in enumerate(parallels):
                if isinstance(parallel, (Arc, InhibitorArc)) and not isinstance(parallel, (CurvedArc, CurvedInhibitorArc)):
                    curved_arc = make_curved(parallel)
                    index = self.arcs.index(parallel)
                    self.arcs[index] = curved_arc
                    curved_arc._manager = self
                    curved_arc.on_changed = self._on_object_changed
                    # Update parallels list with new reference
                    parallels[i] = curved_arc
            
            # Mark dirty to trigger redraw
            self.mark_dirty()
    
    def calculate_arc_offset(self, arc, parallels):
        """Calculate offset for arc to avoid overlapping parallels.
        
        For parallel arcs between same nodes, we offset them perpendicular
        to the line connecting the nodes. The offset is calculated to
        distribute arcs evenly on both sides of the center line.
        
        For opposite direction arcs (A→B, B→A), they curve in opposite
        directions to create mirror symmetry.
        
        Args:
            arc: Arc to calculate offset for
            parallels: List of parallel arcs (from detect_parallel_arcs)
            
        Returns:
            float: Offset distance in pixels (positive = counterclockwise,
                   negative = clockwise, 0 = no offset)
        """
        if not parallels:
            return 0.0  # No offset needed for single arc
        
        # Separate same-direction and opposite-direction arcs
        same_direction = []
        opposite_direction = []
        
        for other in parallels:
            if other.source == arc.source and other.target == arc.target:
                same_direction.append(other)
            elif other.source == arc.target and other.target == arc.source:
                opposite_direction.append(other)
        
        # For opposite direction arcs (most common case: A→B, B→A)
        if len(opposite_direction) == 1 and len(same_direction) == 0:
            # Two arcs in opposite directions - mirror each other
            # Use a deterministic rule: arc with lower ID gets positive offset
            other = opposite_direction[0]
            if arc.id < other.id:
                return 50.0  # Curve counterclockwise (increased from 25)
            else:
                return -50.0  # Curve clockwise (mirror, increased from -25)
        
        # For same-direction arcs or mixed cases, use stable ordering
        all_arcs = [arc] + parallels
        all_arcs.sort(key=lambda a: a.id)  # Stable ordering by ID
        
        index = all_arcs.index(arc)
        total = len(all_arcs)
        
        # Calculate offset based on number of parallel arcs
        # For 2 arcs: offsets are +15, -15
        # For 3 arcs: offsets are +20, 0, -20
        # For 4 arcs: offsets are +30, +10, -10, -30
        # Pattern: distribute evenly around center (0)
        
        if total == 1:
            return 0.0
        elif total == 2:
            # Simple case: ±15 pixels
            return 15.0 if index == 0 else -15.0
        else:
            # General case: distribute evenly with 10px spacing
            spacing = 10.0
            center = (total - 1) / 2.0
            return (index - center) * spacing
    
    def replace_arc(self, old_arc, new_arc):
        """Replace an arc with a different type (for arc transformations).
        
        Used when transforming arcs via context menu:
        - Straight ↔ Curved
        - Normal ↔ Inhibitor
        
        The new arc maintains the same ID and properties but has a different
        class type (Arc, InhibitorArc, CurvedArc, or CurvedInhibitorArc).
        
        Args:
            old_arc: Arc instance to replace
            new_arc: New arc instance (different class, same ID/properties)
        """
        try:
            index = self.arcs.index(old_arc)
            print(f'[Manager] Replacing arc at index {index}: {type(old_arc).__name__} -> {type(new_arc).__name__}')
            self.arcs[index] = new_arc
            
            # Ensure new arc has manager reference and change callback
            new_arc._manager = self
            new_arc.on_changed = self._on_object_changed
            
            self.mark_modified()
            self.mark_dirty()
            print(f'[Manager] Arc replaced successfully, _manager and on_changed set')
        except ValueError:
            # Arc not found in list - may have been deleted
            print(f'[Manager] ERROR: Arc not found in list!')
            pass
    
    def ensure_arc_references(self):
        """Ensure all arcs have proper manager and callback references.
        
        This is useful after loading files or batch operations to ensure
        all arcs can be transformed and detected for parallel positioning.
        """
        for arc in self.arcs:
            if not hasattr(arc, '_manager') or arc._manager is None:
                arc._manager = self
                print(f'[Manager] Fixed missing _manager reference for {arc.name}')
            if not hasattr(arc, 'on_changed') or arc.on_changed is None:
                arc.on_changed = self._on_object_changed
                print(f'[Manager] Fixed missing on_changed callback for {arc.name}')
    
    def get_all_objects(self):
        """Get all Petri net objects in rendering order.
        
        Returns:
            list: All objects in rendering order (arcs behind, then P and T on top)
        """
        # Rendering order: Arcs (behind) → Places and Transitions (on top)
        # Arcs render first so they appear behind the nodes
        # Places and transitions render after (order between P/T doesn't matter)
        return list(self.arcs) + list(self.places) + list(self.transitions)
    
    def find_object_at_position(self, x, y):
        """Find the topmost object at the given world position.
        
        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            
        Returns:
            Place, Transition, Arc, or None: The object at the position, or None
        """
        # Check in reverse rendering order (top to bottom)
        # Transitions and places are checked first (easier to click)
        for transition in reversed(self.transitions):
            if transition.contains_point(x, y):
                return transition
        
        for place in reversed(self.places):
            if place.contains_point(x, y):
                return place
        
        # Arcs are thinner and harder to click, check them last
        for arc in reversed(self.arcs):
            if arc.contains_point(x, y):
                return arc
        
        return None
    
    def get_all_objects(self):
        """Get all Petri net objects in the model.
        
        Returns:
            list: All places, transitions, and arcs combined
        """
        return self.places + self.transitions + self.arcs
    
    def clear_all_selections(self):
        """Clear selection state on all objects.
        
        Used when SelectionManager needs to clear all selections.
        """
        for obj in self.get_all_objects():
            obj.selected = False
        self.selection_manager.clear_selection()
        self.mark_dirty()
    
    def clear_all_objects(self):
        """Remove all Petri net objects from the model and reset to new document state.
        
        This resets the canvas to a fresh "default" state as if creating a new document.
        """
        self.places.clear()
        self.transitions.clear()
        self.arcs.clear()
        
        # Reset ID counters
        self._next_place_id = 1
        self._next_transition_id = 1
        self._next_arc_id = 1
        
        # Reset to default filename (unsaved document state)
        self.filename = "default"
        self.modified = False
        self.created_at = datetime.now()
        self.modified_at = None
        
        self.mark_dirty()
    
    def _on_object_changed(self):
        """Callback when an object's properties change."""
        self.mark_modified()
        self.mark_dirty()
    
    def create_test_objects(self):
        """Create test objects for debugging rendering.
        
        Creates a simple Petri net: P1 -> T1 -> P2
        """
        # Create places
        p1 = self.add_place(-100, 0, label="P1")
        p2 = self.add_place(100, 0, label="P2")
        p1.set_tokens(2)
        p1.set_initial_marking(2)  # Set initial marking for proper reset
        
        # Create transition
        t1 = self.add_transition(0, 0, label="T1")
        
        # Create arcs
        a1 = self.add_arc(p1, t1, weight=1)
        a2 = self.add_arc(t1, p2, weight=1)
        
        print(f"Created test network: {p1.name} → {t1.name} → {p2.name}")
        print(f"Total objects: {len(self.places)} places, {len(self.transitions)} transitions, {len(self.arcs)} arcs")
    
    # ==================== Zoom Operations ====================
    
    def zoom_in(self, center_x=None, center_y=None):
        """Zoom in by one step, centered at the given point.
        
        Args:
            center_x: X coordinate of zoom center (screen space). If None, uses viewport center.
            center_y: Y coordinate of zoom center (screen space). If None, uses viewport center.
        """
        self.zoom_by_factor(self.ZOOM_STEP, center_x, center_y)
    
    def zoom_out(self, center_x=None, center_y=None):
        """Zoom out by one step, centered at the given point.
        
        Args:
            center_x: X coordinate of zoom center (screen space). If None, uses viewport center.
            center_y: Y coordinate of zoom center (screen space). If None, uses viewport center.
        """
        self.zoom_by_factor(1.0 / self.ZOOM_STEP, center_x, center_y)
    
    def zoom_by_factor(self, factor, center_x=None, center_y=None):
        """Zoom by a given factor, centered at a point.
        
        Implements pointer-centered zoom using legacy algorithm:
        - Get world coordinate under cursor before zoom
        - Apply new zoom
        - Adjust pan so world coordinate stays at same screen position
        
        Args:
            factor: Multiplicative zoom factor (e.g., 1.1 = zoom in 10%).
            center_x: X coordinate of zoom center (screen space). If None, uses viewport center.
            center_y: Y coordinate of zoom center (screen space). If None, uses viewport center.
        """
        # Default to viewport center if no center provided
        if center_x is None:
            center_x = self.viewport_width / 2
        if center_y is None:
            center_y = self.viewport_height / 2
        
        # Get world coordinates of zoom center before zoom
        # Legacy formula: world = screen / zoom - pan
        world_x = (center_x / self.zoom) - self.pan_x
        world_y = (center_y / self.zoom) - self.pan_y
        
        # Apply zoom with bounds
        new_zoom = self.zoom * factor
        new_zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, new_zoom))
        
        # Calculate new pan to keep zoom center at same screen position
        # After zoom, we want: world = screen / new_zoom - new_pan
        # So: new_pan = screen / new_zoom - world
        self.pan_x = (center_x / new_zoom) - world_x
        self.pan_y = (center_y / new_zoom) - world_y
        
        self.zoom = new_zoom
        
        # Clamp pan to maintain infinite canvas bounds
        self.clamp_pan()
        
        # Save view state after zoom operation
        self.save_view_state_to_file()
        
        self._needs_redraw = True
    
    def set_zoom(self, zoom_level, center_x=None, center_y=None):
        """Set absolute zoom level.
        
        Args:
            zoom_level: Target zoom level (clamped to MIN_ZOOM..MAX_ZOOM).
            center_x: X coordinate of zoom center (screen space).
            center_y: Y coordinate of zoom center (screen space).
        """
        zoom_level = max(self.MIN_ZOOM, min(self.MAX_ZOOM, zoom_level))
        factor = zoom_level / self.zoom
        self.zoom_by_factor(factor, center_x, center_y)
    
    def zoom_at_point(self, factor, center_x, center_y):
        """Zoom by a factor at a specific point (alias for zoom_by_factor).
        
        Args:
            factor: Multiplicative zoom factor.
            center_x: X coordinate of zoom center (screen space).
            center_y: Y coordinate of zoom center (screen space).
        """
        self.zoom_by_factor(factor, center_x, center_y)
    
    def clamp_pan(self):
        """Clamp pan to keep canvas bounds within viewport.
        
        Creates infinite canvas feeling while preventing blank space.
        Grid always fills viewport regardless of pan/zoom by clamping
        the pan values to ensure the canvas extent covers the screen.
        
        Canvas extent: ±CANVAS_EXTENT in world space
        Viewport: viewport_width × viewport_height in screen space
        
        The constraint is: canvas bounds must fully cover viewport.
        - Left edge: (-extent + pan) * zoom <= 0  →  pan <= extent
        - Right edge: (extent + pan) * zoom >= width  →  pan >= width/zoom - extent
        """
        extent_x = self.CANVAS_EXTENT
        extent_y = self.CANVAS_EXTENT
        
        # Ensure extent is large enough to cover viewport at current zoom
        min_half_x = (self.viewport_width / self.zoom) / 2.0
        min_half_y = (self.viewport_height / self.zoom) / 2.0
        extent_x = max(extent_x, min_half_x)
        extent_y = max(extent_y, min_half_y)
        
        # Calculate pan limits
        # Grid bounds: [-extent, +extent] in world space
        # Screen bounds: [0, viewport] in screen space
        min_pan_x = (self.viewport_width / self.zoom) - extent_x
        max_pan_x = extent_x
        min_pan_y = (self.viewport_height / self.zoom) - extent_y
        max_pan_y = extent_y
        
        # Clamp pan values
        self.pan_x = max(min_pan_x, min(max_pan_x, self.pan_x))
        self.pan_y = max(min_pan_y, min(max_pan_y, self.pan_y))
    
    # ==================== Pan Operations ====================
    
    def pan(self, dx, dy):
        """Pan the viewport by a delta in screen coordinates.
        
        Args:
            dx: Pan delta X in screen pixels (positive = drag right = pan increases).
            dy: Pan delta Y in screen pixels (positive = drag down = pan increases).
        """
        # Convert screen delta to world delta
        world_dx = dx / self.zoom
        world_dy = dy / self.zoom
        
        # Update pan (drag right = pan increases, matching legacy behavior)
        self.pan_x += world_dx
        self.pan_y += world_dy
        
        # Clamp pan to canvas bounds
        self.clamp_pan()
        
        self._needs_redraw = True
    
    def pan_to(self, world_x, world_y):
        """Pan so that the given world coordinate is at viewport center.
        
        Args:
            world_x: Target world X coordinate.
            world_y: Target world Y coordinate.
        """
        self.pan_x = world_x - (self.viewport_width / 2) / self.zoom
        self.pan_y = world_y - (self.viewport_height / 2) / self.zoom
        
        # Clamp pan to canvas bounds
        self.clamp_pan()
        
        self._needs_redraw = True
    
    def pan_relative(self, dx, dy):
        """Pan the viewport by incremental deltas (for drag updates).
        
        This is an alias for pan() but with clearer intent for incremental updates.
        
        Args:
            dx: Pan delta X in screen pixels (positive = pan right).
            dy: Pan delta Y in screen pixels (positive = pan down).
        """
        self.pan(dx, dy)
    
    # ==================== Grid Rendering ====================
    
    def get_grid_spacing(self):
        """Get adaptive grid spacing based on current zoom level.
        
        Uses DPI-aware physical spacing (1mm base) that adapts at zoom thresholds.
        Target at 100% zoom: 1mm minor cell, 5mm major cell (every 5th line).
        
        Returns:
            float: Grid spacing in world coordinates.
        """
        # Convert base spacing from mm to pixels
        px_per_mm = self.get_mm_to_pixels()
        base_px = self.BASE_GRID_SPACING * px_per_mm  # 1mm → pixels
        
        # Adaptive grid: spacing adapts based on zoom level
        # At high zoom (zoomed in), use smaller subdivisions for precision
        # At low zoom (zoomed out), use larger spacing to avoid clutter
        # Target: at zoom=1.0, grid spacing = 1mm (major cell = 5mm with GRID_MAJOR_EVERY=5)
        if self.zoom >= 5.0:
            return base_px / 5   # Very fine grid (0.2mm, major = 1mm)
        elif self.zoom >= 2.0:
            return base_px / 2   # Fine grid (0.5mm, major = 2.5mm)
        elif self.zoom >= 0.5:
            return base_px       # Normal grid (1mm, major = 5mm) ← TARGET at zoom=1.0
        elif self.zoom >= 0.2:
            return base_px * 2   # Coarse grid (2mm, major = 10mm)
        else:
            return base_px * 5   # Very coarse grid (5mm, major = 25mm)
    
    def get_visible_bounds(self):
        """Calculate the visible area in world coordinates.
        
        Uses screen_to_world transform to correctly map viewport corners.
        This ensures grid is regenerated for current view, creating infinite canvas illusion.
        
        Returns:
            tuple: (min_x, min_y, max_x, max_y) in world coordinates.
        """
        # Top-left corner of viewport (screen origin)
        min_x, min_y = self.screen_to_world(0, 0)
        # Bottom-right corner of viewport
        max_x, max_y = self.screen_to_world(self.viewport_width, self.viewport_height)
        return min_x, min_y, max_x, max_y
    
    def draw_grid(self, cr):
        """Draw the grid pattern on the cairo context.
        
        Now draws in world space (inside Cairo transform) so grid scales with zoom.
        Line widths are compensated to maintain constant pixel size.
        Uses major/minor line distinction (every 5th line is major).
        
        Args:
            cr: Cairo context to draw on (with zoom transform already applied).
        """
        grid_spacing = self.get_grid_spacing()
        min_x, min_y, max_x, max_y = self.get_visible_bounds()
        
        # Calculate grid positions in world coordinates
        start_x = math.floor(min_x / grid_spacing) * grid_spacing
        start_y = math.floor(min_y / grid_spacing) * grid_spacing
        
        # Calculate starting indices (for major/minor line determination)
        start_index_x = int(math.floor(min_x / grid_spacing))
        start_index_y = int(math.floor(min_y / grid_spacing))
        
        if self.grid_style == self.GRID_STYLE_LINE:
            # Standard line grid - draw in world coordinates with major/minor distinction
            
            # Draw vertical grid lines
            x = start_x
            index_x = start_index_x
            while x <= max_x:
                # Determine if this is a major line
                is_major = (index_x % self.GRID_MAJOR_EVERY) == 0
                
                if is_major:
                    # Major line: darker color, thicker width
                    cr.set_source_rgba(0.65, 0.65, 0.68, 0.8)  # Darker gray
                    cr.set_line_width(1.0 / self.zoom)
                else:
                    # Minor line: lighter color, thinner width
                    cr.set_source_rgba(0.85, 0.85, 0.88, 0.6)  # Lighter gray
                    cr.set_line_width(0.5 / self.zoom)
                
                cr.move_to(x, min_y)
                cr.line_to(x, max_y)
                cr.stroke()
                
                x += grid_spacing
                index_x += 1
            
            # Draw horizontal grid lines
            y = start_y
            index_y = start_index_y
            while y <= max_y:
                # Determine if this is a major line
                is_major = (index_y % self.GRID_MAJOR_EVERY) == 0
                
                if is_major:
                    # Major line: darker color, thicker width
                    cr.set_source_rgba(0.65, 0.65, 0.68, 0.8)  # Darker gray
                    cr.set_line_width(1.0 / self.zoom)
                else:
                    # Minor line: lighter color, thinner width
                    cr.set_source_rgba(0.85, 0.85, 0.88, 0.6)  # Lighter gray
                    cr.set_line_width(0.5 / self.zoom)
                
                cr.move_to(min_x, y)
                cr.line_to(max_x, y)
                cr.stroke()
                
                y += grid_spacing
                index_y += 1
            
        elif self.grid_style == self.GRID_STYLE_DOT:
            # Dot grid - draw small circles at intersections in world coordinates
            # Major intersections (every 5th line) get larger/darker dots
            
            y = start_y
            index_y = start_index_y
            while y <= max_y:
                x = start_x
                index_x = start_index_x
                while x <= max_x:
                    # Check if this is a major intersection
                    is_major_x = (index_x % self.GRID_MAJOR_EVERY) == 0
                    is_major_y = (index_y % self.GRID_MAJOR_EVERY) == 0
                    is_major = is_major_x and is_major_y
                    
                    if is_major:
                        # Major intersection: larger, darker dot
                        cr.set_source_rgba(0.65, 0.65, 0.68, 0.8)
                        dot_radius = 2.0 / self.zoom
                    else:
                        # Minor intersection: smaller, lighter dot
                        cr.set_source_rgba(0.85, 0.85, 0.88, 0.6)
                        dot_radius = 1.5 / self.zoom
                    
                    cr.arc(x, y, dot_radius, 0, 2 * math.pi)
                    cr.fill()
                    
                    x += grid_spacing
                    index_x += 1
                y += grid_spacing
                index_y += 1
                
        elif self.grid_style == self.GRID_STYLE_CROSS:
            # Cross-hair grid - draw small + at intersections in world coordinates
            # Major intersections (every 5th line) get larger/darker crosses
            
            y = start_y
            index_y = start_index_y
            while y <= max_y:
                x = start_x
                index_x = start_index_x
                while x <= max_x:
                    # Check if this is a major intersection
                    is_major_x = (index_x % self.GRID_MAJOR_EVERY) == 0
                    is_major_y = (index_y % self.GRID_MAJOR_EVERY) == 0
                    is_major = is_major_x and is_major_y
                    
                    if is_major:
                        # Major intersection: larger, darker cross
                        cr.set_source_rgba(0.65, 0.65, 0.68, 0.8)
                        cross_size = 4.0 / self.zoom
                        cr.set_line_width(1.0 / self.zoom)
                    else:
                        # Minor intersection: smaller, lighter cross
                        cr.set_source_rgba(0.85, 0.85, 0.88, 0.6)
                        cross_size = 3.0 / self.zoom
                        cr.set_line_width(0.5 / self.zoom)
                    
                    # Horizontal line of cross
                    cr.move_to(x - cross_size, y)
                    cr.line_to(x + cross_size, y)
                    # Vertical line of cross
                    cr.move_to(x, y - cross_size)
                    cr.line_to(x, y + cross_size)
                    cr.stroke()
                    
                    x += grid_spacing
                    index_x += 1
                y += grid_spacing
                index_y += 1
    
    # ==================== State Management ====================
    
    def set_viewport_size(self, width, height):
        """Update viewport size when widget is resized.
        
        Args:
            width: New viewport width in pixels.
            height: New viewport height in pixels.
        """
        self.viewport_width = width
        self.viewport_height = height
        
        # On first viewport size update, center the canvas
        if not self._initial_pan_set and width > 0 and height > 0:
            # Center the canvas: pan so that (0,0) world coordinate is at screen center
            self.pan_x = -(width / 2) / self.zoom
            self.pan_y = -(height / 2) / self.zoom
            self._initial_pan_set = True
        
        self._needs_redraw = True
    
    def set_grid_style(self, style):
        """Set the grid rendering style.
        
        Args:
            style: Grid style ('line', 'dot', or 'cross').
        """
        if style in [self.GRID_STYLE_LINE, self.GRID_STYLE_DOT, self.GRID_STYLE_CROSS]:
            self.grid_style = style
            self._needs_redraw = True
    
    def set_pointer_position(self, x, y):
        """Update current pointer position for pointer-centered zoom.
        
        Args:
            x: Pointer X coordinate in screen space.
            y: Pointer Y coordinate in screen space.
        """
        self.pointer_x = x
        self.pointer_y = y
    
    def needs_redraw(self):
        """Check if canvas needs redrawing.
        
        Returns:
            bool: True if redraw is needed.
        """
        return self._needs_redraw
    
    def mark_clean(self):
        """Mark canvas as clean (drawn)."""
        self._needs_redraw = False
    
    def mark_dirty(self):
        """Mark canvas as dirty (needs redraw)."""
        self._needs_redraw = True
    
    # ==================== Info Methods ====================
    
    def get_zoom_percentage(self):
        """Get zoom level as percentage string.
        
        Returns:
            str: Zoom percentage (e.g., "100%").
        """
        return f"{int(self.zoom * 100)}%"
    
    def get_info(self):
        """Get canvas state information for debugging.
        
        Returns:
            dict: Canvas state information.
        """
        return {
            'zoom': self.zoom,
            'zoom_percent': self.get_zoom_percentage(),
            'pan_x': self.pan_x,
            'pan_y': self.pan_y,
            'viewport': (self.viewport_width, self.viewport_height),
            'grid_spacing': self.get_grid_spacing(),
            'visible_bounds': self.get_visible_bounds(),
        }
    
    # ==================== Document Management ====================
    
    def create_new_document(self, filename="default"):
        """Initialize a new document with default state.
        
        Args:
            filename: Base filename without extension.
            
        Returns:
            dict: Validation result with 'valid' bool and 'errors' list.
        """
        # Reset to initial state
        self.filename = filename
        self.modified = False
        self.created_at = datetime.now()
        self.modified_at = None
        
        # Reset zoom and pan to defaults
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._initial_pan_set = False
        
        # Mark for redraw
        self.mark_dirty()
        
        # Validate initial state
        return self.validate_initial_state()
    
    def validate_initial_state(self):
        """Validate the initial state of the document.
        
        Checks:
        - Canvas dimensions are valid (> 0)
        - Zoom is at 100% (1.0)
        - Pan is centered (will be set on first draw)
        - Grid style is valid
        
        Returns:
            dict: {'valid': bool, 'errors': list of error messages}
        """
        errors = []
        
        # Check canvas dimensions
        if self.canvas_width <= 0:
            errors.append(f"Invalid canvas width: {self.canvas_width}")
        if self.canvas_height <= 0:
            errors.append(f"Invalid canvas height: {self.canvas_height}")
        
        # Check zoom is at 100%
        if abs(self.zoom - 1.0) > 0.01:
            errors.append(f"Initial zoom should be 100%, got {self.get_zoom_percentage()}")
        
        # Check zoom is within bounds
        if self.zoom < self.MIN_ZOOM or self.zoom > self.MAX_ZOOM:
            errors.append(f"Zoom out of bounds: {self.zoom} (min: {self.MIN_ZOOM}, max: {self.MAX_ZOOM})")
        
        # Check grid style is valid
        valid_styles = [self.GRID_STYLE_LINE, self.GRID_STYLE_DOT, self.GRID_STYLE_CROSS]
        if self.grid_style not in valid_styles:
            errors.append(f"Invalid grid style: {self.grid_style}")
        
        # Check filename is valid
        if not self.filename or self.filename.strip() == "":
            errors.append("Filename cannot be empty")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def get_document_state(self):
        """Get the current document state for saving.
        
        Returns:
            dict: Document state including metadata and canvas properties.
        """
        return {
            'filename': self.filename,
            'modified': self.modified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'canvas': {
                'width': self.canvas_width,
                'height': self.canvas_height,
                'zoom': self.zoom,
                'pan_x': self.pan_x,
                'pan_y': self.pan_y,
                'grid_style': self.grid_style,
            },
            'viewport': {
                'width': self.viewport_width,
                'height': self.viewport_height,
            }
        }
    
    def mark_modified(self):
        """Mark document as modified."""
        if not self.modified:
            self.modified = True
            self.modified_at = datetime.now()
            self.mark_dirty()
    
    def set_filename(self, filename):
        """Set the document filename.
        
        Args:
            filename: Base filename without extension.
        """
        if filename != self.filename:
            self.filename = filename
            self.mark_modified()
    
    def is_default_filename(self) -> bool:
        """Check if document has the default filename (unsaved state).
        
        This is a flag that indicates the document is in an unsaved/new state
        and should trigger file chooser dialogs in save operations.
        
        Returns:
            bool: True if filename is "default", False otherwise
        """
        return self.filename == "default"
    
    def to_document_model(self):
        """Convert canvas manager's Petri net objects to a DocumentModel.
        
        This creates a DocumentModel instance that can be saved/loaded by
        the persistency manager.
        
        Returns:
            DocumentModel: Document model containing all Petri net objects
        """
        from shypn.data.canvas import DocumentModel
        
        document = DocumentModel()
        document.places = list(self.places)
        document.transitions = list(self.transitions)
        document.arcs = list(self.arcs)
        
        # Sync ID counters
        document._next_place_id = self._next_place_id
        document._next_transition_id = self._next_transition_id
        document._next_arc_id = self._next_arc_id
        
        return document
    
    # ==================== View State Persistence ====================
    
    def get_view_state(self):
        """Get current canvas view state for persistence.
        
        Returns:
            dict: View state containing pan_x, pan_y, zoom
        """
        return {
            'pan_x': self.pan_x,
            'pan_y': self.pan_y,
            'zoom': self.zoom
        }
    
    def set_view_state(self, view_state):
        """Restore canvas view state from saved data.
        
        Args:
            view_state: Dictionary containing pan_x, pan_y, zoom
        """
        if view_state:
            self.pan_x = view_state.get('pan_x', 0.0)
            self.pan_y = view_state.get('pan_y', 0.0)
            self.zoom = view_state.get('zoom', 1.0)
            
            # Clamp zoom to valid range
            self.zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, self.zoom))
            
            # Clamp pan to infinite canvas bounds
            self.clamp_pan()
            
            # Mark that we don't need initial centering
            self._initial_pan_set = True
            
            self.mark_dirty()
    
    def save_view_state_to_file(self, filepath=None):
        """Save current view state to a JSON file.
        
        Args:
            filepath: Optional custom file path. If None, uses default location.
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        if filepath is None:
            # Create .shypn config directory in user's home
            config_dir = os.path.expanduser('~/.shypn')
            os.makedirs(config_dir, exist_ok=True)
            
            # Use filename to create view state file
            filename = self.filename if self.filename else 'default'
            filepath = os.path.join(config_dir, f'{filename}_view.json')
        
        try:
            view_state = self.get_view_state()
            with open(filepath, 'w') as f:
                json.dump(view_state, f, indent=2)
            return True
        except Exception as e:
            return False
    
    def load_view_state_from_file(self, filepath=None):
        """Load view state from a JSON file.
        
        Args:
            filepath: Optional custom file path. If None, uses default location.
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        if filepath is None:
            # Look for view state file in config directory
            config_dir = os.path.expanduser('~/.shypn')
            filename = self.filename if self.filename else 'default'
            filepath = os.path.join(config_dir, f'{filename}_view.json')
        
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, 'r') as f:
                view_state = json.load(f)
            self.set_view_state(view_state)
            return True
        except Exception as e:
            return False
