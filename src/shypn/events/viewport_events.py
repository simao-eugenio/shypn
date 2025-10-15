"""Viewport-related events for zoom and pan changes.

This module defines events related to changes in the viewport:
- Zoom level changes
- Pan position changes
- General viewport changes
"""

from .base_event import BaseEvent


class ViewportChangedEvent(BaseEvent):
    """Event fired when any viewport property changes.
    
    Generic event for viewport changes. More specific events
    (ZoomChangedEvent, PanChangedEvent) are preferred when the
    specific change is known.
    
    Attributes:
        property_name: Name of the property that changed
        value: New value of the property
    """
    
    def __init__(self, property_name: str, value):
        """Initialize event.
        
        Args:
            property_name: Name of the property that changed
            value: New value of the property
        """
        super().__init__()
        self.property_name = property_name
        self.value = value
    
    def to_dict(self):
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'property_name': self.property_name,
            'value': str(self.value),
        })
        return data
    
    def __repr__(self):
        return f"ViewportChangedEvent(property={self.property_name}, value={self.value})"


class ZoomChangedEvent(BaseEvent):
    """Event fired when zoom level changes.
    
    Attributes:
        zoom: New zoom level (1.0 = 100%)
        old_zoom: Previous zoom level (optional)
        center_x: X coordinate of zoom center (optional)
        center_y: Y coordinate of zoom center (optional)
    """
    
    def __init__(self, zoom: float, old_zoom: float = None,
                 center_x: float = None, center_y: float = None):
        """Initialize event.
        
        Args:
            zoom: New zoom level (1.0 = 100%)
            old_zoom: Previous zoom level (optional)
            center_x: X coordinate of zoom center (optional)
            center_y: Y coordinate of zoom center (optional)
        """
        super().__init__()
        self.zoom = zoom
        self.old_zoom = old_zoom
        self.center_x = center_x
        self.center_y = center_y
    
    @property
    def zoom_percent(self) -> int:
        """Get zoom level as percentage."""
        return int(self.zoom * 100)
    
    def to_dict(self):
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'zoom': self.zoom,
            'zoom_percent': self.zoom_percent,
            'old_zoom': self.old_zoom,
            'center_x': self.center_x,
            'center_y': self.center_y,
        })
        return data
    
    def __repr__(self):
        return f"ZoomChangedEvent(zoom={self.zoom_percent}%)"


class PanChangedEvent(BaseEvent):
    """Event fired when pan position changes.
    
    Attributes:
        pan_x: New X pan offset
        pan_y: New Y pan offset
        old_pan_x: Previous X pan offset (optional)
        old_pan_y: Previous Y pan offset (optional)
    """
    
    def __init__(self, pan_x: float, pan_y: float,
                 old_pan_x: float = None, old_pan_y: float = None):
        """Initialize event.
        
        Args:
            pan_x: New X pan offset
            pan_y: New Y pan offset
            old_pan_x: Previous X pan offset (optional)
            old_pan_y: Previous Y pan offset (optional)
        """
        super().__init__()
        self.pan_x = pan_x
        self.pan_y = pan_y
        self.old_pan_x = old_pan_x
        self.old_pan_y = old_pan_y
    
    def to_dict(self):
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'pan_x': self.pan_x,
            'pan_y': self.pan_y,
            'old_pan_x': self.old_pan_x,
            'old_pan_y': self.old_pan_y,
        })
        return data
    
    def __repr__(self):
        return f"PanChangedEvent(x={self.pan_x:.1f}, y={self.pan_y:.1f})"
