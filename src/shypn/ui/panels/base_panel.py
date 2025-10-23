"""Base class for all panel controllers."""

from gi.repository import Gtk, GObject


class BasePanel(GObject.GObject):
    """Base class for panel controllers.
    
    Each panel controller manages:
    - Widget creation and layout
    - Event handling
    - State management
    - Communication with main window via signals
    
    Signals:
        panel-ready: Emitted when panel is fully initialized
        panel-error: Emitted when panel encounters an error
    
    Subclasses must implement:
        - get_preferred_width()
        - initialize()
        - activate()
        - deactivate()
    """
    
    __gsignals__ = {
        'panel-ready': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'panel-error': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }
    
    def __init__(self, builder: Gtk.Builder, panel_name: str):
        """Initialize base panel.
        
        Args:
            builder: Gtk.Builder with main window UI loaded
            panel_name: Name of this panel (e.g., 'files', 'analyses')
        """
        super().__init__()
        self.builder = builder
        self.panel_name = panel_name
        self._container = None
        self._initialized = False
    
    def get_preferred_width(self) -> int:
        """Get preferred width for this panel in pixels.
        
        Subclasses should override this method.
        
        Returns:
            Width in pixels
        """
        raise NotImplementedError("Subclass must implement get_preferred_width()")
    
    def initialize(self):
        """Initialize panel widgets and connections.
        
        Subclasses should override this method to:
        1. Get container from builder
        2. Create/populate widgets
        3. Connect signals
        4. Set up initial state
        
        Called once during main window initialization.
        """
        raise NotImplementedError("Subclass must implement initialize()")
    
    def activate(self):
        """Called when panel becomes visible.
        
        Subclasses should override to:
        - Refresh data
        - Resume operations
        - Update UI state
        """
        raise NotImplementedError("Subclass must implement activate()")
    
    def deactivate(self):
        """Called when panel becomes hidden.
        
        Subclasses should override to:
        - Pause operations
        - Save state
        - Clean up temporary resources
        """
        raise NotImplementedError("Subclass must implement deactivate()")
    
    def get_container(self) -> Gtk.Widget:
        """Get the panel's container widget.
        
        Returns:
            Container widget or None if not initialized
        """
        return self._container
    
    def is_initialized(self) -> bool:
        """Check if panel is initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        return self._initialized
    
    def _emit_ready(self):
        """Emit panel-ready signal."""
        self._initialized = True
        self.emit('panel-ready')
    
    def _emit_error(self, message: str):
        """Emit panel-error signal.
        
        Args:
            message: Error message
        """
        self.emit('panel-error', message)
