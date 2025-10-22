"""Base class for Topology Panel.

Clean OOP architecture:
- Base class handles UI lifecycle and Wayland safety
- Controller subclass handles analyzer coordination
- Minimal code in loader (wrapper only)

Author: Simão Eugénio
Date: 2025-10-20
"""

import sys
from abc import ABC, abstractmethod
from pathlib import Path

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib


class TopologyPanelBase(ABC):
    """Base class for Topology Panel.
    
    Responsibilities:
    - Load UI from XML
    - Manage widget lifecycle (Wayland safe)
    - Handle attach/detach/float operations
    - Coordinate with master palette
    
    NOT responsible for:
    - Analyzer logic (handled by controller subclass)
    - Business logic (handled by analyzers themselves)
    """
    
    def __init__(self, ui_path=None):
        """Initialize topology panel base.
        
        Args:
            ui_path: Optional path to UI file (defaults to ui/panels/topology_panel.ui)
        """
        # Determine UI path
        if ui_path is None:
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent.parent
            ui_path = project_root / 'ui' / 'panels' / 'topology_panel.ui'
        
        self.ui_path = Path(ui_path)
        
        # GTK components
        self.builder = Gtk.Builder()
        self.window = None  # Panel window
        self.content = None  # Content widget
        self.main_window = None  # Reference to main window
        self.palette_widget = None  # Reference to Master Palette widget
        
        # State tracking
        self.is_loaded = False  # Track if load() has been called
    
    def load(self):
        """Load UI from XML file - panel stays in its own window.
        
        SIMPLIFIED ARCHITECTURE:
        - Panel content stays in panel window (no reparenting)
        - Panel responds to show/hide signals from main app
        - No widget tree modifications = No Error 71!
        """
        if not self.ui_path.exists():
            raise FileNotFoundError(f"UI file not found: {self.ui_path}")
        
        try:
            # Load UI file
            self.builder.add_from_file(str(self.ui_path))
            
            # Get main widgets
            self.window = self.builder.get_object('topology_window')
            self.content = self.builder.get_object('topology_content')
            
            if not self.window or not self.content:
                raise RuntimeError("Required widgets not found in UI file")
            
            # Panel content stays in its own window - no reparenting
            print(f"[LOAD] Topology panel loaded (content stays in panel window)", file=sys.stderr)
            
            # Connect window delete event
            self.window.connect('delete-event', self._on_window_delete)
            
            # Initialize subclass-specific widgets
            self._init_widgets()
            
            # Connect signals
            self._connect_signals()
            
            # Hide window by default (will be shown when toggled)
            self.window.set_visible(False)
            
            # Mark as loaded
            self.is_loaded = True
            print(f"[LOAD] Topology panel load() complete, is_loaded=True", file=sys.stderr)
            
        except Exception as e:
            print(f"Error loading topology panel UI: {e}", file=sys.stderr)
            raise
    
    @abstractmethod
    def _init_widgets(self):
        """Initialize subclass-specific widgets.
        
        Called after base widgets are loaded.
        Subclasses should override to get widget references.
        """
        pass
    
    @abstractmethod
    def _connect_signals(self):
        """Connect subclass-specific signals.
        
        Called after widgets are initialized.
        Subclasses should override to connect button signals, etc.
        """
        pass
    
    # ===============================
    # Panel Control Methods
    # ===============================
    
    def set_palette_parent(self, palette_widget):
        """Set the Master Palette widget as parent for positioning.
        
        Args:
            palette_widget: The Master Palette container widget
        """
        self.palette_widget = palette_widget
        
        # Get the toplevel window containing the palette
        if palette_widget:
            toplevel = palette_widget.get_toplevel()
            if toplevel and isinstance(toplevel, Gtk.Window):
                self.window.set_transient_for(toplevel)
    
    def attach(self, main_window):
        """Simplified attach: connect panel window to main app.
        
        Panel stays in its own window. This method connects it to the main app
        for coordinated show/hide.
        
        Args:
            main_window: The main application window
        """
        if not self.is_loaded:
            raise RuntimeError("Panel must be loaded before attaching")
        
        # Store main window reference
        self.main_window = main_window
        
        # Set main window as transient parent (keeps panel on top)
        self.window.set_transient_for(main_window)
        
        print(f"[ATTACH] Topology panel attached to main window", file=sys.stderr)
    
    def hide(self):
        """Hide panel window."""
        print(f"[HIDE] Topology panel hiding window", file=sys.stderr)
        if self.window:
            self.window.hide()
    
    def show(self):
        """Show panel window positioned next to palette."""
        print(f"[SHOW] Topology panel showing window", file=sys.stderr)
        if self.window:
            # Position panel next to the Master Palette
            if self.palette_widget and self.main_window:
                # Get palette position relative to main window
                palette_alloc = self.palette_widget.get_allocation()
                palette_width = palette_alloc.width
                
                # Get main window position
                main_x, main_y = self.main_window.get_position()
                main_width, main_height = self.main_window.get_size()
                
                # Position panel to the right of palette
                panel_width = 400  # Default panel width for topology
                self.window.set_default_size(panel_width, main_height)
                self.window.move(main_x + palette_width, main_y)
            
            self.window.show_all()
    
    def _on_window_delete(self, window, event):
        """Handle window close button.
        
        Instead of destroying, we hide the window.
        
        Args:
            window: The window being closed
            event: The delete event
            
        Returns:
            True to prevent destruction
        """
        # Hide window instead of destroying
        window.hide()
        return True  # Prevent destruction


__all__ = ['TopologyPanelBase']
