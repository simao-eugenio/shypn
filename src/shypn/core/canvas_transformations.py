"""Canvas transformation system - Base classes and implementations.

This module provides an OOP framework for canvas transformations (rotation, reflection, etc.)
with proper coordinate transformation and persistence support.
"""

import math
from abc import ABC, abstractmethod


class CanvasTransformation(ABC):
    """Base class for canvas transformations.
    
    Provides a common interface for transformations like rotation, reflection, etc.
    All transformations must implement coordinate conversion and Cairo rendering.
    """
    
    def __init__(self):
        """Initialize base transformation."""
        self._enabled = True
        self._needs_redraw = True
    
    @abstractmethod
    def apply_to_context(self, cr, viewport_width, viewport_height):
        """Apply this transformation to a Cairo context.
        
        Args:
            cr: Cairo context to transform.
            viewport_width: Width of the viewport in pixels.
            viewport_height: Height of the viewport in pixels.
        """
        pass
    
    @abstractmethod
    def screen_to_world(self, screen_x, screen_y, viewport_width, viewport_height):
        """Transform screen coordinates to world coordinates.
        
        Args:
            screen_x: Screen X coordinate (pixels).
            screen_y: Screen Y coordinate (pixels).
            viewport_width: Width of the viewport in pixels.
            viewport_height: Height of the viewport in pixels.
            
        Returns:
            tuple: (world_x, world_y) in world coordinates.
        """
        pass
    
    @abstractmethod
    def world_to_screen(self, world_x, world_y, viewport_width, viewport_height):
        """Transform world coordinates to screen coordinates.
        
        Args:
            world_x: World X coordinate.
            world_y: World Y coordinate.
            viewport_width: Width of the viewport in pixels.
            viewport_height: Height of the viewport in pixels.
            
        Returns:
            tuple: (screen_x, screen_y) in pixels.
        """
        pass
    
    @abstractmethod
    def reset(self):
        """Reset transformation to default state."""
        pass
    
    @abstractmethod
    def to_dict(self):
        """Serialize transformation state to dictionary.
        
        Returns:
            dict: Transformation state for persistence.
        """
        pass
    
    @abstractmethod
    def from_dict(self, data):
        """Restore transformation state from dictionary.
        
        Args:
            data: Dictionary containing transformation state.
        """
        pass
    
    @property
    def enabled(self):
        """Get whether transformation is enabled."""
        return self._enabled
    
    @enabled.setter
    def enabled(self, value):
        """Set whether transformation is enabled."""
        self._enabled = bool(value)
        self._needs_redraw = True
    
    @property
    def needs_redraw(self):
        """Get whether transformation requires redraw."""
        return self._needs_redraw
    
    def clear_redraw_flag(self):
        """Clear the redraw flag after redrawing."""
        self._needs_redraw = False


class CanvasRotation(CanvasTransformation):
    """Canvas rotation transformation.
    
    Rotates the entire canvas around the viewport center.
    Supports arbitrary angles with snapping to common rotations (0°, 90°, 180°, 270°).
    """
    
    # Common rotation angles in degrees
    ANGLE_0 = 0.0
    ANGLE_90 = 90.0
    ANGLE_180 = 180.0
    ANGLE_270 = 270.0
    ANGLE_NEG_90 = -90.0
    
    # Snap threshold (degrees) - angles within this threshold snap to common angles
    SNAP_THRESHOLD = 2.0
    
    def __init__(self, angle_degrees=0.0):
        """Initialize canvas rotation.
        
        Args:
            angle_degrees: Initial rotation angle in degrees (default: 0.0).
        """
        super().__init__()
        self._angle_degrees = 0.0
        self._angle_radians = 0.0
        self.set_angle(angle_degrees)
    
    def set_angle(self, angle_degrees):
        """Set rotation angle with optional snapping.
        
        Args:
            angle_degrees: Rotation angle in degrees.
        """
        # Normalize to [0, 360)
        normalized = angle_degrees % 360.0
        
        # Snap to common angles if within threshold
        for common_angle in [self.ANGLE_0, self.ANGLE_90, self.ANGLE_180, self.ANGLE_270]:
            if abs(normalized - common_angle) < self.SNAP_THRESHOLD:
                normalized = common_angle
                break
        
        self._angle_degrees = normalized
        self._angle_radians = math.radians(normalized)
        self._needs_redraw = True
    
    def rotate(self, delta_degrees):
        """Rotate by a delta angle.
        
        Args:
            delta_degrees: Angle increment in degrees (positive = counterclockwise).
        """
        new_angle = self._angle_degrees + delta_degrees
        self.set_angle(new_angle)
    
    def rotate_90_cw(self):
        """Rotate 90° clockwise."""
        self.rotate(-90.0)
    
    def rotate_90_ccw(self):
        """Rotate 90° counterclockwise."""
        self.rotate(90.0)
    
    def rotate_180(self):
        """Rotate 180°."""
        self.rotate(180.0)
    
    def apply_to_context(self, cr, viewport_width, viewport_height):
        """Apply rotation to Cairo context.
        
        Rotates around the viewport center.
        
        Args:
            cr: Cairo context to transform.
            viewport_width: Width of the viewport in pixels.
            viewport_height: Height of the viewport in pixels.
        """
        if not self._enabled or abs(self._angle_radians) < 1e-6:
            return  # No rotation needed
        
        # Rotate around viewport center
        center_x = viewport_width / 2.0
        center_y = viewport_height / 2.0
        
        cr.translate(center_x, center_y)
        cr.rotate(self._angle_radians)
        cr.translate(-center_x, -center_y)
    
    def screen_to_world(self, screen_x, screen_y, viewport_width, viewport_height):
        """Transform screen coordinates to world coordinates with rotation.
        
        Args:
            screen_x: Screen X coordinate (pixels).
            screen_y: Screen Y coordinate (pixels).
            viewport_width: Width of the viewport in pixels.
            viewport_height: Height of the viewport in pixels.
            
        Returns:
            tuple: (world_x, world_y) accounting for rotation.
        """
        if not self._enabled or abs(self._angle_radians) < 1e-6:
            return (screen_x, screen_y)  # No rotation
        
        # Translate to center, rotate, translate back
        center_x = viewport_width / 2.0
        center_y = viewport_height / 2.0
        
        # Relative to center
        rel_x = screen_x - center_x
        rel_y = screen_y - center_y
        
        # Rotate (inverse rotation for screen→world)
        cos_a = math.cos(-self._angle_radians)
        sin_a = math.sin(-self._angle_radians)
        rotated_x = rel_x * cos_a - rel_y * sin_a
        rotated_y = rel_x * sin_a + rel_y * cos_a
        
        # Back to absolute coordinates
        world_x = rotated_x + center_x
        world_y = rotated_y + center_y
        
        return (world_x, world_y)
    
    def world_to_screen(self, world_x, world_y, viewport_width, viewport_height):
        """Transform world coordinates to screen coordinates with rotation.
        
        Args:
            world_x: World X coordinate.
            world_y: World Y coordinate.
            viewport_width: Width of the viewport in pixels.
            viewport_height: Height of the viewport in pixels.
            
        Returns:
            tuple: (screen_x, screen_y) accounting for rotation.
        """
        if not self._enabled or abs(self._angle_radians) < 1e-6:
            return (world_x, world_y)  # No rotation
        
        # Translate to center, rotate, translate back
        center_x = viewport_width / 2.0
        center_y = viewport_height / 2.0
        
        # Relative to center
        rel_x = world_x - center_x
        rel_y = world_y - center_y
        
        # Rotate (forward rotation for world→screen)
        cos_a = math.cos(self._angle_radians)
        sin_a = math.sin(self._angle_radians)
        rotated_x = rel_x * cos_a - rel_y * sin_a
        rotated_y = rel_x * sin_a + rel_y * cos_a
        
        # Back to absolute coordinates
        screen_x = rotated_x + center_x
        screen_y = rotated_y + center_y
        
        return (screen_x, screen_y)
    
    def reset(self):
        """Reset rotation to 0°."""
        self.set_angle(0.0)
    
    def to_dict(self):
        """Serialize rotation state to dictionary.
        
        Returns:
            dict: Rotation state for persistence.
        """
        return {
            'type': 'rotation',
            'angle_degrees': self._angle_degrees,
            'enabled': self._enabled
        }
    
    def from_dict(self, data):
        """Restore rotation state from dictionary.
        
        Args:
            data: Dictionary containing rotation state.
        """
        self._enabled = data.get('enabled', True)
        angle = data.get('angle_degrees', 0.0)
        self.set_angle(angle)
    
    @property
    def angle_degrees(self):
        """Get current rotation angle in degrees."""
        return self._angle_degrees
    
    @property
    def angle_radians(self):
        """Get current rotation angle in radians."""
        return self._angle_radians
    
    @property
    def is_rotated(self):
        """Check if canvas is rotated (not at 0°)."""
        return abs(self._angle_degrees) > 1e-6


class TransformationManager:
    """Manages multiple canvas transformations.
    
    Coordinates transformations like rotation, reflection, etc.
    Applies them in correct order and handles persistence.
    """
    
    def __init__(self):
        """Initialize transformation manager."""
        self._transformations = {}
        self._redraw_callback = None
        
        # Create default transformations
        self._transformations['rotation'] = CanvasRotation()
    
    def get_rotation(self):
        """Get rotation transformation.
        
        Returns:
            CanvasRotation: The rotation transformation instance.
        """
        return self._transformations.get('rotation')
    
    def add_transformation(self, name, transformation):
        """Add a custom transformation.
        
        Args:
            name: Unique name for the transformation.
            transformation: CanvasTransformation instance.
        """
        if not isinstance(transformation, CanvasTransformation):
            raise TypeError("transformation must be a CanvasTransformation instance")
        self._transformations[name] = transformation
    
    def apply_all_to_context(self, cr, viewport_width, viewport_height):
        """Apply all enabled transformations to Cairo context.
        
        Transformations are applied in fixed order:
        1. Rotation
        2. (Future: Reflection, skew, etc.)
        
        Args:
            cr: Cairo context to transform.
            viewport_width: Width of the viewport in pixels.
            viewport_height: Height of the viewport in pixels.
        """
        # Apply transformations in order
        for name in ['rotation']:  # Fixed order
            if name in self._transformations:
                trans = self._transformations[name]
                if trans.enabled:
                    trans.apply_to_context(cr, viewport_width, viewport_height)
    
    def screen_to_world_all(self, screen_x, screen_y, viewport_width, viewport_height):
        """Apply all transformations to screen→world coordinate conversion.
        
        Args:
            screen_x: Screen X coordinate (pixels).
            screen_y: Screen Y coordinate (pixels).
            viewport_width: Width of the viewport in pixels.
            viewport_height: Height of the viewport in pixels.
            
        Returns:
            tuple: (world_x, world_y) after all transformations.
        """
        wx, wy = screen_x, screen_y
        
        # Apply transformations in reverse order for inverse transform
        for name in reversed(['rotation']):
            if name in self._transformations:
                trans = self._transformations[name]
                if trans.enabled:
                    wx, wy = trans.screen_to_world(wx, wy, viewport_width, viewport_height)
        
        return (wx, wy)
    
    def world_to_screen_all(self, world_x, world_y, viewport_width, viewport_height):
        """Apply all transformations to world→screen coordinate conversion.
        
        Args:
            world_x: World X coordinate.
            world_y: World Y coordinate.
            viewport_width: Width of the viewport in pixels.
            viewport_height: Height of the viewport in pixels.
            
        Returns:
            tuple: (screen_x, screen_y) after all transformations.
        """
        sx, sy = world_x, world_y
        
        # Apply transformations in forward order
        for name in ['rotation']:
            if name in self._transformations:
                trans = self._transformations[name]
                if trans.enabled:
                    sx, sy = trans.world_to_screen(sx, sy, viewport_width, viewport_height)
        
        return (sx, sy)
    
    def reset_all(self):
        """Reset all transformations to default state."""
        for trans in self._transformations.values():
            trans.reset()
        self._trigger_redraw()
    
    def needs_redraw(self):
        """Check if any transformation needs redraw.
        
        Returns:
            bool: True if any transformation needs redraw.
        """
        return any(t.needs_redraw for t in self._transformations.values())
    
    def clear_redraw_flags(self):
        """Clear redraw flags on all transformations."""
        for trans in self._transformations.values():
            trans.clear_redraw_flag()
    
    def to_dict(self):
        """Serialize all transformations to dictionary.
        
        Returns:
            dict: All transformation states for persistence.
        """
        return {
            name: trans.to_dict()
            for name, trans in self._transformations.items()
        }
    
    def from_dict(self, data):
        """Restore all transformations from dictionary.
        
        Args:
            data: Dictionary containing all transformation states.
        """
        for name, trans_data in data.items():
            if name in self._transformations:
                self._transformations[name].from_dict(trans_data)
    
    def set_redraw_callback(self, callback):
        """Set callback to trigger redraw when transformations change.
        
        Args:
            callback: Callable to trigger redraw (no arguments).
        """
        self._redraw_callback = callback
    
    def _trigger_redraw(self):
        """Trigger redraw if callback is set."""
        if self._redraw_callback:
            self._redraw_callback()
