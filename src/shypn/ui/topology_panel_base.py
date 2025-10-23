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
    
    # ========================================================================
    # PHASE 4: GtkStack Integration Methods
    # New architecture: Panels live in GtkStack, controlled by Master Palette
    # ========================================================================
    
    def add_to_stack(self, stack, container, panel_name='topology'):
        """Add panel content to a GtkStack container (Phase 4: new architecture).
        
        Args:
            stack: GtkStack widget that will contain all panels
            container: GtkBox container within the stack for this panel
            panel_name: Name identifier for this panel in the stack ('topology')
        """
        
        if self.window is None:
            self.load()
        
        # Extract content from window
        current_parent = self.content.get_parent()
        if current_parent == self.window:
            self.window.remove(self.content)
        elif current_parent and current_parent != container:
            current_parent.remove(self.content)
        
        # Add content to stack container
        if self.content.get_parent() != container:
            container.add(self.content)
        
        # Mark as hanged in stack mode (skeleton pattern)
        self.is_hanged = True
        self.parent_container = container
        self._stack = stack
        self._stack_panel_name = panel_name
        
        # Hide window (not needed in stack mode)
        if self.window:
            self.window.hide()
        
    
    def show_in_stack(self):
        """Show this panel in the GtkStack (Phase 4: Master Palette control)."""
        
        if not hasattr(self, '_stack') or not self._stack:
            return
        
        # Make stack visible
        if not self._stack.get_visible():
            self._stack.set_visible(True)
        
        # Set this panel as active child
        self._stack.set_visible_child_name(self._stack_panel_name)
        
        # Re-enable show_all and make content visible
        if self.content:
            self.content.set_no_show_all(False)  # Re-enable show_all
            self.content.show_all()  # Show all child widgets recursively
        
        # Make container visible too
        if self.parent_container:
            self.parent_container.set_visible(True)
        
    
    def hide_in_stack(self):
        """Hide this panel in the GtkStack (Phase 4: Master Palette control)."""
        
        # Hide the content using no_show_all to prevent show_all from revealing it
        if self.content:
            self.content.set_no_show_all(True)
            self.content.hide()
        
        # Hide container too
        if self.parent_container:
            self.parent_container.set_visible(False)
        
    
    # ========================================================================
    # Float/Detach Support (Skeleton Pattern)
    # ========================================================================
    
    def detach(self):
        """Detach panel from container and show as floating window.
        
        Skeleton pattern: synchronous, simple state flag.
        """
        print(f"[TOPOLOGY] detach() called", file=sys.stderr)
        
        if not hasattr(self, 'is_hanged') or not self.is_hanged:
            print(f"[TOPOLOGY] Already detached, nothing to do", file=sys.stderr)
            return
        
        # Remove content from container
        if self.parent_container:
            self.parent_container.remove(self.content)
            self.parent_container.set_visible(False)  # Hide empty container
        
        # Hide the stack if this was the active panel
        if hasattr(self, '_stack') and self._stack:
            self._stack.set_visible(False)
        
        # Add content to window
        self.window.add(self.content)
        
        # Update state
        self.is_hanged = False
        
        # Update float button state (if it exists)
        if hasattr(self, 'float_button') and self.float_button:
            self._updating_button = True
            self.float_button.set_active(True)
            self._updating_button = False
        
        # Show floating window
        self.window.show_all()
        
        print(f"[TOPOLOGY] Panel detached and floating", file=sys.stderr)
    
    def float(self):
        """Alias for detach() - make panel float as separate window."""
        self.detach()
    
    def hang_on(self, container):
        """Attach panel to container (opposite of detach).
        
        Args:
            container: GtkBox or container to attach to
        """
        print(f"[TOPOLOGY] hang_on() called", file=sys.stderr)
        
        if hasattr(self, 'is_hanged') and self.is_hanged:
            print(f"[TOPOLOGY] Already attached, nothing to do", file=sys.stderr)
            return
        
        # Hide floating window
        self.window.hide()
        
        # Remove content from window
        self.window.remove(self.content)
        
        # Add content to container
        container.pack_start(self.content, True, True, 0)
        container.set_visible(True)  # Show container with content
        
        # Update state and references
        self.is_hanged = True
        self.parent_container = container
        
        # Update float button state (if it exists)
        if hasattr(self, 'float_button') and self.float_button:
            self._updating_button = True
            self.float_button.set_active(False)
            self._updating_button = False
        
        # Show the stack if available
        if hasattr(self, '_stack') and self._stack:
            self._stack.set_visible(True)
            if hasattr(self, '_stack_panel_name'):
                self._stack.set_visible_child_name(self._stack_panel_name)
        
        print(f"[TOPOLOGY] Panel attached to container", file=sys.stderr)
    
    def attach_to(self, container):
        """Alias for hang_on() - attach panel to container."""
        self.hang_on(container)


__all__ = ['TopologyPanelBase']
