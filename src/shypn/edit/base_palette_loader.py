#!/usr/bin/env python3
"""Base Palette Loader - Abstract base class for UI palette loaders."""

from abc import ABC, abstractmethod
from gi.repository import Gtk
import os


class BasePaletteLoader(ABC):
    """Abstract base class for palette loaders.
    
    Provides common functionality for loading GTK UI files and
    connecting signals. Subclasses implement specific palette behavior.
    """
    
    def __init__(self, parent_window=None):
        """Initialize the palette loader.
        
        Args:
            parent_window: Parent GTK window (for modals/dialogs)
        """
        self.parent_window = parent_window
        self.builder = None
        self.root_widget = None
    
    @abstractmethod
    def get_ui_filename(self):
        """Return the UI filename to load.
        
        Returns:
            str: Filename of the .ui file (without path)
        """
        pass
    
    @abstractmethod
    def get_widget_references(self):
        """Get references to widgets from the builder.
        
        Called after UI is loaded. Subclasses should store
        widget references as instance attributes.
        """
        pass
    
    @abstractmethod
    def connect_signals(self):
        """Connect UI signals to handler methods.
        
        Called after widgets are referenced. Subclasses should
        connect all button clicks, toggles, etc.
        """
        pass
    
    def load_ui(self):
        """Load the UI file and return root widget.
        
        Returns:
            GtkWidget: Root widget of the palette
        """
        self.builder = Gtk.Builder()
        ui_path = self._get_ui_path()
        
        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"UI file not found: {ui_path}")
        
        self.builder.add_from_file(ui_path)
        
        # Let subclass get its widget references
        self.get_widget_references()
        
        # Let subclass connect signals
        self.connect_signals()
        
        return self.root_widget
    
    def _get_ui_path(self):
        """Get full path to UI file.
        
        Returns:
            str: Absolute path to UI file
        """
        # This file is in src/shypn/edit/
        # Go up to src/, then up to repo root, then into ui/palettes/
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        ui_path = os.path.join(base_dir, 'ui', 'palettes', self.get_ui_filename())
        return ui_path
    
    def get_widget(self, widget_id):
        """Get a widget by ID from the builder.
        
        Args:
            widget_id: Widget ID from UI file
            
        Returns:
            GtkWidget: Widget instance or None if not found
        """
        if not self.builder:
            return None
        return self.builder.get_object(widget_id)
    
    def get_root_widget(self):
        """Get the root widget of the palette.
        
        Returns:
            GtkWidget: Root widget or None
        """
        return self.root_widget
