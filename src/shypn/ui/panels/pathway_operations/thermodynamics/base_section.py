"""Base class for thermodynamics UI sections.

All thermodynamics sections (Settings, Mapping, Validation) inherit from
ThermodynamicsSectionBase and implement the abstract methods.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from abc import ABC, abstractmethod


class ThermodynamicsSectionBase(ABC):
    """Base class for sections within THERMODYNAMICS category.
    
    Each section is responsible for:
    1. Building its widget hierarchy
    2. Refreshing display from document model
    3. Saving UI state to document
    4. Handling user interactions
    
    Subclasses must implement:
    - build_widget(): Create and return the section widget
    - refresh_data(): Update display from document
    - save_to_document(): Persist UI state
    """
    
    def __init__(self, model_canvas=None):
        """Initialize base section.
        
        Args:
            model_canvas: ModelCanvasManager instance (optional)
        """
        self.model_canvas = model_canvas
        self.document = None
        self._widget = None
    
    @abstractmethod
    def build_widget(self) -> Gtk.Widget:
        """Build and return the section widget.
        
        Returns:
            Gtk.Widget: The main widget for this section
        """
        pass
    
    @abstractmethod
    def refresh_data(self):
        """Refresh display from document model.
        
        Called when:
        - Document is loaded/changed
        - Model canvas changes
        - User requests refresh
        """
        pass
    
    @abstractmethod
    def save_to_document(self):
        """Save current UI state to document model.
        
        Called when:
        - User clicks Apply/Save
        - Document is about to be saved
        - Section loses focus
        """
        pass
    
    def set_model_canvas(self, model_canvas):
        """Set the model canvas and refresh data.
        
        Args:
            model_canvas: ModelCanvasLoader or ModelCanvasManager instance
        """
        self.model_canvas = model_canvas
        
        # Get the actual manager from the loader
        manager = self._get_canvas_manager()
        if manager and hasattr(manager, 'document'):
            self.document = manager.document
            self.refresh_data()
    
    def _get_canvas_manager(self):
        """Get the current canvas manager instance consistently.
        
        This method normalizes access to the canvas manager, handling both
        loader and direct manager references.
        
        Returns:
            ModelCanvasManager instance if available, None otherwise
        """
        if self.model_canvas is None:
            return None
        
        # If it has add_document, it's a loader - get current manager
        if hasattr(self.model_canvas, 'add_document'):
            # It's a ModelCanvasLoader
            try:
                if hasattr(self.model_canvas, 'get_current_model'):
                    return self.model_canvas.get_current_model()
                elif hasattr(self.model_canvas, 'get_current_model_manager'):
                    return self.model_canvas.get_current_model_manager()
            except Exception as e:
                import logging
                logger = logging.getLogger(self.__class__.__name__)
                logger.warning(f"Failed to get manager from loader: {e}")
                return None
        
        # Check if it's already a manager (has places/transitions)
        if hasattr(self.model_canvas, 'places') and hasattr(self.model_canvas, 'transitions'):
            return self.model_canvas
        
        return None
    
    def set_document(self, document):
        """Set the document and refresh data.
        
        Args:
            document: DocumentModel instance
        """
        self.document = document
        self.refresh_data()
    
    def get_widget(self) -> Gtk.Widget:
        """Get the section widget (builds if necessary).
        
        Returns:
            Gtk.Widget: The main widget for this section
        """
        if self._widget is None:
            self._widget = self.build_widget()
        return self._widget
    
    def _show_info(self, message: str):
        """Show info message (can be overridden for custom notifications).
        
        Args:
            message: Info message to display
        """
        print(f"INFO: {message}")
    
    def _show_error(self, message: str):
        """Show error message (can be overridden for custom notifications).
        
        Args:
            message: Error message to display
        """
        print(f"ERROR: {message}")
