"""Viewport controller for canvas view management.

Manages viewport state: zoom, pan, and viewport dimensions.
Implements pointer-centered zoom and infinite canvas with clamping.

This is a stateful controller (first one extracted from god class).
Unlike services (stateless), controllers maintain state between operations.

Module structure:
    AbstractViewportController -- ABC defining the public contract
    ViewportController         -- Concrete implementation
"""

from __future__ import annotations

import json
import math
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class AbstractViewportController(ABC):
    """Abstract base class defining the ViewportController public contract."""

    # ---- Zoom ----
    @abstractmethod
    def zoom_in(self, center_x: Optional[float] = None, center_y: Optional[float] = None) -> None: ...

    @abstractmethod
    def zoom_out(self, center_x: Optional[float] = None, center_y: Optional[float] = None) -> None: ...

    @abstractmethod
    def zoom_by_factor(
        self,
        factor: float,
        center_x: Optional[float] = None,
        center_y: Optional[float] = None,
    ) -> None: ...

    @abstractmethod
    def set_zoom(
        self,
        zoom_level: float,
        center_x: Optional[float] = None,
        center_y: Optional[float] = None,
    ) -> None: ...

    @abstractmethod
    def zoom_at_point(self, factor: float, center_x: float, center_y: float) -> None: ...

    @abstractmethod
    def zoom_at_point_rotation_aware(
        self,
        factor: float,
        center_x: float,
        center_y: float,
        world_x: float,
        world_y: float,
        rotation: Any,
    ) -> bool: ...

    # ---- Pan ----
    @abstractmethod
    def pan(self, dx: float, dy: float, rotation: Any = None) -> None: ...

    @abstractmethod
    def pan_to(self, world_x: float, world_y: float) -> None: ...

    @abstractmethod
    def pan_relative(self, dx: float, dy: float, rotation: Any = None) -> None: ...

    @abstractmethod
    def clamp_pan(self) -> None: ...

    # ---- Viewport sizing ----
    @abstractmethod
    def set_viewport_size(self, width: float, height: float) -> None: ...

    @abstractmethod
    def set_pointer_position(self, x: float, y: float) -> None: ...

    # ---- Info ----
    @abstractmethod
    def get_zoom_percentage(self) -> str: ...

    @abstractmethod
    def get_viewport_info(self) -> Dict[str, Any]: ...

    # ---- Persistence ----
    @abstractmethod
    def save_view_state_to_file(self) -> None: ...

    @abstractmethod
    def load_view_state_from_file(self) -> bool: ...

    # ---- Redraw tracking ----
    @abstractmethod
    def needs_redraw(self) -> bool: ...

    @abstractmethod
    def mark_clean(self) -> None: ...

    @abstractmethod
    def mark_dirty(self) -> None: ...

    # ---- Reset ----
    @abstractmethod
    def reset(self) -> None: ...

    # ---- Content bounds & fit ----
    @abstractmethod
    def get_content_bounds(
        self,
        places: Any,
        transitions: Any,
        arcs: Any,
    ) -> Optional[Tuple[float, float, float, float]]: ...

    @abstractmethod
    def fit_content(
        self,
        bounds: Tuple[float, float, float, float],
        padding_percent: float,
        horizontal_offset_percent: float,
        vertical_offset_percent: float,
    ) -> None: ...


class ViewportController(AbstractViewportController):
    """Controller for viewport state (zoom, pan, dimensions).
    
    Responsibilities:
    - Zoom operations (in, out, by factor, set absolute)
    - Pan operations (delta, absolute, relative)
    - Viewport bounds clamping (infinite canvas)
    - Viewport size management
    - View state persistence (save/load pan and zoom)
    
    State managed:
    - zoom: Current zoom level (1.0 = 100%)
    - pan_x, pan_y: Pan offset in world coordinates
    - viewport_width, viewport_height: Viewport dimensions in screen pixels
    - pointer_x, pointer_y: Current pointer position (for zoom centering)
    - _initial_pan_set: Flag for first-time centering
    
    Design notes:
    - Uses legacy zoom algorithm (world = screen/zoom - pan)
    - Clamps pan to keep canvas within viewport (infinite canvas feel)
    - Saves view state to file after zoom operations
    """
    
    # Zoom configuration
    MIN_ZOOM = 0.05  # 5% minimum (allows viewing very large models)
    MAX_ZOOM = 3.0   # 300% maximum (practical engineering range)
    ZOOM_STEP = 1.1  # Multiplicative zoom factor (10% per step)
    
    # Canvas extent for infinite canvas (half-extent in logical units)
    CANVAS_EXTENT = 10000.0  # ±10,000 units = 20,000×20,000 total canvas
    
    def __init__(self, viewport_width=800, viewport_height=600, filename="default"):
        """Initialize viewport controller.
        
        Args:
            viewport_width: Initial viewport width in pixels.
            viewport_height: Initial viewport height in pixels.
            filename: Base filename for view state persistence.
        """
        # Viewport state
        self.zoom = 1.0  # Current zoom level (1.0 = 100%)
        self.pan_x = 0.0  # Pan offset X (in world coordinates)
        self.pan_y = 0.0  # Pan offset Y (in world coordinates)
        self._initial_pan_set = False  # Flag to center on first draw
        
        # Viewport dimensions (screen coordinates)
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        
        # Pointer position (for pointer-centered zoom)
        self.pointer_x = 0
        self.pointer_y = 0
        
        # Filename for persistence
        self.filename = filename
        
        # File path for model-specific view state (set by manager)
        self.model_filepath = None
        
        # Dirty flag for redraw tracking
        self._needs_redraw = True
    
    # ==================== Zoom Operations ====================
    
    def zoom_in(self, center_x=None, center_y=None):
        """Zoom in by one step (multiply by ZOOM_STEP).
        
        Args:
            center_x: X coordinate of zoom center (screen space). If None, uses viewport center.
            center_y: Y coordinate of zoom center (screen space). If None, uses viewport center.
        """
        self.zoom_by_factor(self.ZOOM_STEP, center_x, center_y)
    
    def zoom_out(self, center_x=None, center_y=None):
        """Zoom out by one step (divide by ZOOM_STEP).
        
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
    
    # ==================== Pan Operations ====================
    
    def pan(self, dx, dy, rotation=None):
        """Pan the viewport by a delta in screen coordinates.
        
        Args:
            dx: Pan delta X in screen pixels (positive = drag right = pan increases).
            dy: Pan delta Y in screen pixels (positive = drag down = pan increases).
            rotation: Optional CanvasRotation object for rotated canvas support.
        """
        # Convert screen delta to world delta
        world_dx = dx / self.zoom
        world_dy = dy / self.zoom
        
        # Apply inverse rotation if canvas is rotated (with tolerance for floating point errors)
        if rotation and abs(rotation.angle_degrees) > 0.001:
            cos_a = math.cos(-rotation.angle_radians)  # Inverse rotation
            sin_a = math.sin(-rotation.angle_radians)
            
            # Rotate the pan delta
            rotated_dx = world_dx * cos_a - world_dy * sin_a
            rotated_dy = world_dx * sin_a + world_dy * cos_a
            
            world_dx = rotated_dx
            world_dy = rotated_dy
        
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
    
    def pan_relative(self, dx, dy, rotation=None):
        """Pan the viewport by incremental deltas (for drag updates).
        
        This is an alias for pan() but with clearer intent for incremental updates.
        
        Args:
            dx: Pan delta X in screen pixels (positive = pan right).
            dy: Pan delta Y in screen pixels (positive = pan down).
            rotation: Optional CanvasRotation object for rotated canvas support.
        """
        self.pan(dx, dy, rotation)
    
    def clamp_pan(self):
        """Clamp pan to keep canvas bounds within viewport.
        
        Creates infinite canvas feeling while preventing blank space.
        Grid always fills viewport regardless of pan/zoom by clamping
        the pan values to ensure the canvas extent covers the screen.
        
        At very low zoom levels (<0.2), disable clamping to allow free panning
        for viewing large models without instability.
        
        Canvas extent: ±CANVAS_EXTENT in world space
        Viewport: viewport_width × viewport_height in screen space
        
        The constraint is: canvas bounds must fully cover viewport.
        - Left edge: (-extent + pan) * zoom <= 0  →  pan <= extent
        - Right edge: (extent + pan) * zoom >= width  →  pan >= width/zoom - extent
        """
        # At very low zoom levels, allow free panning (don't clamp)
        # This prevents instability when viewing very large models
        if self.zoom < 0.2:
            return
        
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
    
    # ==================== Viewport Management ====================
    
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
    
    def set_pointer_position(self, x, y):
        """Update current pointer position for pointer-centered zoom.
        
        Args:
            x: Pointer X coordinate in screen space.
            y: Pointer Y coordinate in screen space.
        """
        self.pointer_x = x
        self.pointer_y = y
    
    def get_zoom_percentage(self):
        """Get zoom level as percentage string.
        
        Returns:
            str: Zoom percentage (e.g., "100%").
        """
        return f"{int(self.zoom * 100)}%"
    
    def get_viewport_info(self):
        """Get viewport state information for debugging.
        
        Returns:
            dict: Viewport state information.
        """
        return {
            'zoom': self.zoom,
            'zoom_percent': self.get_zoom_percentage(),
            'pan_x': self.pan_x,
            'pan_y': self.pan_y,
            'viewport': (self.viewport_width, self.viewport_height),
            'pointer': (self.pointer_x, self.pointer_y),
        }
    
    # ==================== View State Persistence ====================
    
    def save_view_state_to_file(self):
        """Save current view state (pan and zoom) to file.
        
        Saves to model's directory as .view_state_{basename}.json
        or to ~/.shypn/{filename}_view.json for unsaved models.
        This preserves user's view position across sessions.
        """
        view_state = {
            'pan_x': self.pan_x,
            'pan_y': self.pan_y,
            'zoom': self.zoom,
        }
        
        # Determine state file location based on model filepath
        if self.model_filepath:
            # Save in model's directory
            model_dir = os.path.dirname(self.model_filepath)
            basename = os.path.basename(self.model_filepath)
            # Remove .shy extension if present
            if basename.endswith('.shy'):
                basename = basename[:-4]
            state_file = os.path.join(model_dir, f".view_state_{basename}.json")
        else:
            # Unsaved model - use ~/.shypn config directory
            config_dir = os.path.expanduser('~/.shypn')
            os.makedirs(config_dir, exist_ok=True)
            state_file = os.path.join(config_dir, f"{self.filename}_view.json")
        
        try:
            os.makedirs(os.path.dirname(state_file), exist_ok=True)
            with open(state_file, 'w') as f:
                json.dump(view_state, f, indent=2)
        except (OSError, IOError, PermissionError, TypeError) as e:
            logger.debug(f"Failed to save view state: {e}")
    
    def load_view_state_from_file(self):
        """Load view state (pan and zoom) from file.
        
        Looks in model's directory first, then falls back to ~/.shypn/
        
        Returns:
            bool: True if state was loaded successfully, False otherwise.
        """
        # Determine state file location based on model filepath
        if self.model_filepath:
            # Load from model's directory
            model_dir = os.path.dirname(self.model_filepath)
            basename = os.path.basename(self.model_filepath)
            # Remove .shy extension if present
            if basename.endswith('.shy'):
                basename = basename[:-4]
            state_file = os.path.join(model_dir, f".view_state_{basename}.json")
        else:
            # Unsaved model - try ~/.shypn config directory
            config_dir = os.path.expanduser('~/.shypn')
            state_file = os.path.join(config_dir, f"{self.filename}_view.json")
        
        if not os.path.exists(state_file):
            return False
        
        try:
            with open(state_file, 'r') as f:
                view_state = json.load(f)
            
            self.pan_x = view_state.get('pan_x', self.pan_x)
            self.pan_y = view_state.get('pan_y', self.pan_y)
            self.zoom = view_state.get('zoom', self.zoom)
            
            # Clamp loaded values
            self.zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, self.zoom))
            self.clamp_pan()
            
            self._needs_redraw = True
            return True
        except (OSError, IOError, json.JSONDecodeError, KeyError, ValueError) as e:
            logger.debug(f"Failed to load view state: {e}")
            return False
    
    # ==================== Redraw Management ====================
    
    def needs_redraw(self):
        """Check if viewport needs redrawing.
        
        Returns:
            bool: True if redraw is needed.
        """
        return self._needs_redraw
    
    def mark_clean(self):
        """Mark viewport as clean (drawn)."""
        self._needs_redraw = False
    
    def mark_dirty(self):
        """Mark viewport as dirty (needs redraw)."""
        self._needs_redraw = True
    
    # ==================== Reset ====================
    
    def reset(self) -> None:
        """Reset viewport to default state (zoom=1.0, centered)."""
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._initial_pan_set = False
        
        # Re-center if viewport size is known
        if self.viewport_width > 0 and self.viewport_height > 0:
            self.pan_x = -(self.viewport_width / 2) / self.zoom
            self.pan_y = -(self.viewport_height / 2) / self.zoom
            self._initial_pan_set = True
        
        self._needs_redraw = True

    # ==================== Rotation-Aware Zoom Helpers ====================

    def _apply_zoom_factor_with_bounds(self, factor: float) -> Tuple[float, bool]:
        """Apply zoom factor with bounds checking.

        Args:
            factor: Multiplicative zoom factor.

        Returns:
            (new_zoom, zoom_changed) tuple.
        """
        new_zoom = self.zoom * factor
        new_zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, new_zoom))
        zoom_changed = new_zoom != self.zoom
        return new_zoom, zoom_changed

    def _calculate_pan_for_zoom_without_rotation(
        self,
        world_x: float,
        world_y: float,
        center_x: float,
        center_y: float,
    ) -> Tuple[float, float]:
        """Calculate pan adjustment for pointer-centred zoom (no rotation).

        After the new zoom has been written to ``self.zoom``, solve::

            world = screen / zoom - pan  →  pan = screen / zoom - world

        Args:
            world_x: World X coordinate to keep under the cursor.
            world_y: World Y coordinate to keep under the cursor.
            center_x: Screen X of the zoom focal point.
            center_y: Screen Y of the zoom focal point.

        Returns:
            (pan_x, pan_y) in world coordinates.
        """
        pan_x = (center_x / self.zoom) - world_x
        pan_y = (center_y / self.zoom) - world_y
        return pan_x, pan_y

    def _calculate_pan_for_zoom_with_rotation(
        self,
        world_x: float,
        world_y: float,
        center_x: float,
        center_y: float,
        rotation: Any,
    ) -> Tuple[float, float]:
        """Calculate pan adjustment for pointer-centred zoom with canvas rotation.

        Solves::

            pan = c/zoom - world + R_inv((screen - c) / zoom)

        where *c* is the screen centre and *R_inv* is the inverse rotation.

        Args:
            world_x: World X coordinate to keep under the cursor.
            world_y: World Y coordinate to keep under the cursor.
            center_x: Screen X of the zoom focal point.
            center_y: Screen Y of the zoom focal point.
            rotation: CanvasRotation with ``angle_radians`` attribute.

        Returns:
            (pan_x, pan_y) in world coordinates.
        """
        cx = self.viewport_width / 2.0
        cy = self.viewport_height / 2.0

        # Offset of the zoom focal point from the screen centre, in world units
        screen_offset_x = (center_x - cx) / self.zoom
        screen_offset_y = (center_y - cy) / self.zoom

        # Rotate the offset by the inverse of the canvas rotation
        cos_a = math.cos(-rotation.angle_radians)
        sin_a = math.sin(-rotation.angle_radians)
        rotated_x = screen_offset_x * cos_a - screen_offset_y * sin_a
        rotated_y = screen_offset_x * sin_a + screen_offset_y * cos_a

        pan_x = (cx / self.zoom) - world_x + rotated_x
        pan_y = (cy / self.zoom) - world_y + rotated_y
        return pan_x, pan_y

    def zoom_at_point_rotation_aware(
        self,
        factor: float,
        center_x: float,
        center_y: float,
        world_x: float,
        world_y: float,
        rotation: Any,
    ) -> bool:
        """Zoom by *factor* at a focal point, honouring canvas rotation.

        The caller is responsible for converting the focal screen coordinate to
        world space (using ``screen_to_world``) before calling this method,
        because that conversion may require model-level context (e.g.
        ``transformation_manager``) that the viewport controller does not own.

        Args:
            factor: Multiplicative zoom factor.
            center_x: Screen X of the zoom focal point.
            center_y: Screen Y of the zoom focal point.
            world_x: World X of the zoom focal point (pre-computed by caller).
            world_y: World Y of the zoom focal point (pre-computed by caller).
            rotation: CanvasRotation object, or ``None`` for no rotation.

        Returns:
            ``True`` if the zoom level changed; ``False`` if it was already at
            the min/max bound.
        """
        new_zoom, zoom_changed = self._apply_zoom_factor_with_bounds(factor)
        if not zoom_changed:
            return False

        self.zoom = new_zoom

        if rotation and abs(rotation.angle_degrees) > 0.001:
            self.pan_x, self.pan_y = self._calculate_pan_for_zoom_with_rotation(
                world_x, world_y, center_x, center_y, rotation
            )
        else:
            self.pan_x, self.pan_y = self._calculate_pan_for_zoom_without_rotation(
                world_x, world_y, center_x, center_y
            )

        self.clamp_pan()
        self.save_view_state_to_file()
        self._needs_redraw = True
        return True

    # ==================== Content Bounds & Fit-to-Viewport ====================

    @staticmethod
    def _get_object_bounds(
        all_objects: List[Any],
    ) -> Tuple[float, float, float, float]:
        """Return (min_x, max_x, min_y, max_y) for a list of placed objects.

        Each object must expose ``.x`` and ``.y`` attributes.
        """
        min_x = min(obj.x for obj in all_objects)
        max_x = max(obj.x for obj in all_objects)
        min_y = min(obj.y for obj in all_objects)
        max_y = max(obj.y for obj in all_objects)
        return min_x, max_x, min_y, max_y

    @staticmethod
    def _update_bounds_with_arc(
        arc: Any,
        min_x: float,
        max_x: float,
        min_y: float,
        max_y: float,
    ) -> Tuple[float, float, float, float]:
        """Expand bounds to include arc endpoints and Bézier control points."""
        if hasattr(arc.source, 'x') and hasattr(arc.source, 'y'):
            min_x = min(min_x, arc.source.x)
            max_x = max(max_x, arc.source.x)
            min_y = min(min_y, arc.source.y)
            max_y = max(max_y, arc.source.y)
        if hasattr(arc.target, 'x') and hasattr(arc.target, 'y'):
            min_x = min(min_x, arc.target.x)
            max_x = max(max_x, arc.target.x)
            min_y = min(min_y, arc.target.y)
            max_y = max(max_y, arc.target.y)
        if hasattr(arc, 'control_points') and arc.control_points:
            for cp_x, cp_y in arc.control_points:
                min_x = min(min_x, cp_x)
                max_x = max(max_x, cp_x)
                min_y = min(min_y, cp_y)
                max_y = max(max_y, cp_y)
        return min_x, max_x, min_y, max_y

    def get_content_bounds(
        self,
        places: Any,
        transitions: Any,
        arcs: Any,
    ) -> Optional[Tuple[float, float, float, float]]:
        """Calculate the axis-aligned bounding box of all model content.

        Args:
            places: Iterable of place objects with ``.x`` / ``.y``.
            transitions: Iterable of transition objects with ``.x`` / ``.y``.
            arcs: Iterable of arc objects.

        Returns:
            ``(min_x, min_y, max_x, max_y)`` or ``None`` if the model is empty.
        """
        all_objects: List[Any] = list(places) + list(transitions)
        if not all_objects:
            return None

        min_x, max_x, min_y, max_y = self._get_object_bounds(all_objects)
        for arc in arcs:
            min_x, max_x, min_y, max_y = self._update_bounds_with_arc(
                arc, min_x, max_x, min_y, max_y
            )
        return (min_x, min_y, max_x, max_y)

    def _calculate_content_dimensions(
        self,
        bounds: Tuple[float, float, float, float],
    ) -> Tuple[float, float]:
        """Return padded content dimensions in world coordinates.

        Adds ~80 world-unit padding (≈ 40 px each side at 100 % zoom) to
        account for the visual radius of places and transitions.
        """
        min_x, min_y, max_x, max_y = bounds
        content_width = max(max_x - min_x + 80, 80.0)
        content_height = max(max_y - min_y + 80, 80.0)
        return content_width, content_height

    def _calculate_zoom_to_fit(
        self,
        content_width: float,
        content_height: float,
        padding_percent: float,
    ) -> float:
        """Return the zoom level required to fit content in the viewport.

        Args:
            content_width: Content width in world coordinates.
            content_height: Content height in world coordinates.
            padding_percent: Percentage of viewport to reserve as margin
                (e.g. ``10`` = leave 10 % empty on each axis).

        Returns:
            Zoom level clamped to ``[MIN_ZOOM, MAX_ZOOM]``.
        """
        padding_factor = 1.0 - (padding_percent / 100.0)
        available_width = self.viewport_width * padding_factor
        available_height = self.viewport_height * padding_factor
        zoom_x = available_width / content_width if content_width > 0 else 1.0
        zoom_y = available_height / content_height if content_height > 0 else 1.0
        target_zoom = min(zoom_x, zoom_y)
        return max(self.MIN_ZOOM, min(self.MAX_ZOOM, target_zoom))

    def _apply_viewport_offsets(
        self,
        horizontal_offset_percent: float,
        vertical_offset_percent: float,
        target_zoom: float,
    ) -> None:
        """Shift pan by percentage-based offsets after centering.

        Args:
            horizontal_offset_percent: % of viewport width to shift right
                (negative = left).
            vertical_offset_percent: % of viewport height to shift down
                (negative = up).
            target_zoom: Zoom level used to convert to world space.
        """
        if horizontal_offset_percent == 0 and vertical_offset_percent == 0:
            return
        viewport_width_world = self.viewport_width / target_zoom
        viewport_height_world = self.viewport_height / target_zoom
        self.pan_x += (horizontal_offset_percent / 100.0) * viewport_width_world
        self.pan_y += (vertical_offset_percent / 100.0) * viewport_height_world

    def fit_content(
        self,
        bounds: Tuple[float, float, float, float],
        padding_percent: float,
        horizontal_offset_percent: float,
        vertical_offset_percent: float,
    ) -> None:
        """Zoom and pan so that *bounds* fits inside the viewport.

        Args:
            bounds: Content bounding box ``(min_x, min_y, max_x, max_y)``.
            padding_percent: Viewport fraction to leave as margin.
            horizontal_offset_percent: Additional horizontal shift (% of width).
            vertical_offset_percent: Additional vertical shift (% of height).
        """
        content_width, content_height = self._calculate_content_dimensions(bounds)
        target_zoom = self._calculate_zoom_to_fit(
            content_width, content_height, padding_percent
        )
        self.zoom = target_zoom

        min_x, min_y, max_x, max_y = bounds
        self.pan_to((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)
        self._apply_viewport_offsets(
            horizontal_offset_percent, vertical_offset_percent, target_zoom
        )
