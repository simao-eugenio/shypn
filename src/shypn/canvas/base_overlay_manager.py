"""Base Overlay Manager - Abstract base class for canvas overlay management.

This module defines the abstract interface for managing overlay widgets on a canvas.
Overlays include palettes, toolbars, and other UI elements that appear on top of
the drawing canvas.

Design Principles:
- Single Responsibility: Only manages overlay widgets, not canvas logic
- Open/Closed: Open for extension (subclassing), closed for modification
- Dependency Inversion: Depends on abstractions (ABC), not concrete implementations
"""
from abc import ABC, abstractmethod


class BaseOverlayManager(ABC):
    """Abstract base class for managing canvas overlay widgets.
    
    An overlay manager is responsible for:
    - Creating and positioning overlay widgets (palettes, toolbars)
    - Managing overlay lifecycle (creation, visibility, cleanup)
    - Coordinating overlay interactions (mode switching, tool selection)
    
    This base class defines the interface that all overlay managers must implement.
    Subclasses provide concrete implementations for specific canvas types.
    
    Attributes:
        overlay_widget: The GtkOverlay widget that contains all overlay children
        overlay_box: Optional GtkBox for positioning overlays
        drawing_area: The GtkDrawingArea that the overlays are attached to
        canvas_manager: The ModelCanvasManager that manages the canvas state
    """
    
    def __init__(self, overlay_widget, overlay_box, drawing_area, canvas_manager):
        """Initialize the overlay manager.
        
        Args:
            overlay_widget: GtkOverlay widget for adding overlay children
            overlay_box: Optional GtkBox for positioning overlays
            drawing_area: GtkDrawingArea widget
            canvas_manager: ModelCanvasManager instance
        """
        self.overlay_widget = overlay_widget
        self.overlay_box = overlay_box
        self.drawing_area = drawing_area
        self.canvas_manager = canvas_manager
        
        # Palette storage dictionaries (keyed by drawing_area for multi-document support)
        self._palettes = {}
    
    @abstractmethod
    def setup_overlays(self, parent_window=None):
        """Create and attach all overlay widgets to the canvas.
        
        This method is called during canvas initialization to set up all
        overlay widgets (palettes, toolbars, etc.).
        
        Args:
            parent_window: Optional parent window for floating palettes
        """
        pass
    
    @abstractmethod
    def cleanup_overlays(self):
        """Remove and cleanup all overlay widgets.
        
        This method is called when closing a canvas tab to properly
        cleanup resources and remove references.
        """
        pass
    
    @abstractmethod
    def update_palette_visibility(self, mode):
        """Update which palettes are visible based on the current mode.
        
        Args:
            mode: Current mode string ('edit' or 'simulate')
        """
        pass
    
    @abstractmethod
    def get_palette(self, palette_name):
        """Get a specific palette by name.
        
        Args:
            palette_name: Name of the palette to retrieve
            
        Returns:
            The palette instance, or None if not found
        """
        pass
    
    def register_palette(self, palette_name, palette_instance):
        """Register a palette instance for later retrieval.
        
        Args:
            palette_name: Name to register the palette under
            palette_instance: The palette instance to register
        """
        self._palettes[palette_name] = palette_instance
    
    def unregister_palette(self, palette_name):
        """Unregister a palette instance.
        
        Args:
            palette_name: Name of the palette to unregister
        """
        if palette_name in self._palettes:
            del self._palettes[palette_name]
