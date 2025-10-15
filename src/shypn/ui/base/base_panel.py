"""Base panel class for all UI panels.

This module provides the abstract base class for all panel implementations
in the Shypn application. Panels are self-contained UI components that:
- Load their GTK widgets from a builder
- Receive dependencies via constructor injection
- Delegate business logic to controllers
- Handle only UI-specific concerns

Example:
    class MyPanel(BasePanel):
        def __init__(self, builder, my_controller):
            self.my_controller = my_controller
            super().__init__(builder, my_controller=my_controller)
        
        def _load_widgets(self):
            self.button = self.get_widget('my_button')
        
        def connect_signals(self):
            self.button.connect('clicked', self._on_button_click)
        
        def _setup_ui(self):
            self.button.set_label('Click Me')
        
        def _on_button_click(self, button):
            # Delegate to controller
            self.my_controller.handle_click()
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from gi.repository import Gtk


class BasePanel(ABC):
    """Abstract base class for all UI panels.
    
    Responsibilities:
    - Manage GTK builder and widgets
    - Wire GTK signals to handler methods
    - Coordinate with injected controllers/services
    - Handle UI-specific logic only (NO business logic!)
    
    Subclasses must implement:
    - _load_widgets(): Load widgets from builder
    - connect_signals(): Connect GTK signals to handlers
    - _setup_ui(): Setup initial UI state
    
    Attributes:
        builder: GTK builder with loaded UI definition
        _dependencies: Dictionary of injected dependencies
        _widgets: Cache of loaded widgets
    """
    
    def __init__(self, builder: Gtk.Builder, **dependencies):
        """Initialize panel with GTK builder and dependencies.
        
        Args:
            builder: GTK builder with loaded UI definition
            **dependencies: Injected dependencies (controllers, services, etc.)
                           These should be stored as instance attributes in
                           subclass __init__ before calling super().__init__()
        
        Example:
            def __init__(self, builder, canvas_controller, file_service):
                # Store dependencies as instance attributes first
                self.canvas_controller = canvas_controller
                self.file_service = file_service
                
                # Then call super with all dependencies
                super().__init__(builder, 
                               canvas_controller=canvas_controller,
                               file_service=file_service)
        """
        self.builder = builder
        self._dependencies = dependencies
        self._widgets: Dict[str, Gtk.Widget] = {}
        
        # Initialize panel in correct order
        self._load_widgets()
        self._setup_ui()
        # Note: connect_signals() should be called explicitly after construction
        # to allow for two-phase initialization if needed
    
    @abstractmethod
    def _load_widgets(self):
        """Load widgets from GTK builder.
        
        This method should call get_widget() for each widget that the panel
        needs to interact with and store them as instance attributes.
        
        Example:
            def _load_widgets(self):
                self.drawing_area = self.get_widget('drawing_area')
                self.toolbar = self.get_widget('canvas_toolbar')
                self.status_label = self.get_widget('status_label')
        """
        pass
    
    @abstractmethod
    def connect_signals(self):
        """Connect GTK signals to handler methods.
        
        This method should wire up all GTK signals to appropriate handler
        methods on this panel instance.
        
        Example:
            def connect_signals(self):
                self.button.connect('clicked', self._on_button_click)
                self.entry.connect('changed', self._on_entry_changed)
                self.drawing_area.connect('draw', self._on_draw)
        """
        pass
    
    @abstractmethod
    def _setup_ui(self):
        """Setup initial UI state.
        
        This method should configure widgets with their initial state,
        set default values, configure event masks, etc.
        
        Example:
            def _setup_ui(self):
                self.drawing_area.set_size_request(800, 600)
                self.entry.set_text('Default value')
                self.combo.set_active(0)
        """
        pass
    
    def get_widget(self, widget_id: str) -> Optional[Gtk.Widget]:
        """Get widget by ID from builder with caching.
        
        Args:
            widget_id: ID of the widget in the UI definition
        
        Returns:
            The GTK widget, or None if not found
        
        Note:
            Widgets are cached after first retrieval for performance.
        """
        if widget_id not in self._widgets:
            widget = self.builder.get_object(widget_id)
            if widget is not None:
                self._widgets[widget_id] = widget
            return widget
        return self._widgets[widget_id]
    
    def get_dependency(self, dep_name: str) -> Any:
        """Get injected dependency by name.
        
        Args:
            dep_name: Name of the dependency
        
        Returns:
            The dependency object, or None if not found
        
        Note:
            Prefer accessing dependencies via instance attributes set in
            subclass __init__ rather than using this method.
        """
        return self._dependencies.get(dep_name)
    
    def has_widget(self, widget_id: str) -> bool:
        """Check if widget exists in builder.
        
        Args:
            widget_id: ID of the widget to check
        
        Returns:
            True if widget exists, False otherwise
        """
        return self.builder.get_object(widget_id) is not None
    
    def show(self):
        """Show the panel.
        
        Override this if the panel has a specific container widget
        that needs to be shown.
        """
        pass
    
    def hide(self):
        """Hide the panel.
        
        Override this if the panel has a specific container widget
        that needs to be hidden.
        """
        pass
    
    def cleanup(self):
        """Cleanup resources when panel is destroyed.
        
        Override this to disconnect signals, unregister observers, etc.
        Called when the panel is being destroyed or removed.
        
        Example:
            def cleanup(self):
                # Unregister from state manager
                self.state_manager.remove_observer(self.observer)
                
                # Disconnect signals
                self.button.disconnect_by_func(self._on_button_click)
                
                # Clear references
                self.canvas_controller = None
        """
        pass
